# -*- coding: utf-8 -*-
"""生成 A4 胸环靶矢量图（打印用）。

坐标系：单位 mm，页面 210x297（A4 纵向），原点在左上角，y 轴向下。
———————————————————————————————————————————————————————
换挡数：只改下面参数区的 N_RINGS 一个数，其余全部自动跟：
  靶面宽度始终撑满 A4（BODY_HW=95 → 靶面 190mm 宽），环带宽度 = 95/(N_RINGS-1)。
      N_RINGS = 3  → 环带 47.5mm（≈5cm，跟标准胸环靶的环距一致）  分值 10 9 8
      N_RINGS = 4  → 环带 31.7mm                                  分值 10 9 8 7
      N_RINGS = 5  → 环带 23.8mm                                  分值 10 9 8 7 6
      N_RINGS = 6  → 环带 19.0mm
      N_RINGS = 10 → 环带 10.6mm
  分值永远从 TOP_VALUE(10) 往下数，最外一档收头顶 + 底部两角。
———————————————————————————————————————————————————————

环制照标准胸环靶：
  * 环线是等距放大的**操场形族**：左右竖直直边 + 上下圆头，
    第 k 条的半宽 a_k = A_STEP*k，圆头半高 0.66*a_k，直边半长 0.75*a_k；
  * 最外那条（a = 靶面半宽）正好贴着靶面两侧竖边；
  * 比它大的环没地方画，所以最外一档只在头部和底角成带——这就是标准靶的排法；
  * 环号排成十字：水平中线一排、竖直中线一排，都左右/上下对称。

头型和肩角照参考靶实测：
  * 头顶是一条**很宽的浅弧**（一直张到半宽 37mm 才收直边），不是窄圆顶；
  * 头两侧先外扩到最宽 42.8mm，再往里收到 40.2mm 的底角，所以头根上有个很轻的收腰；
  * 肩线与水平线成 28°（比"从底角直接斜到竖边"的 45° 平得多），竖边因此起得更高。

输出 SVG；PDF 由 export_pdf.py 用 Chromium 出，A4 实际尺寸 1:1。
"""
from math import radians, tan
from pathlib import Path

# ───────────────────────── 参数区 ─────────────────────────
N_RINGS = 5                             # ★ 挡数总开关（分值 = 10 往下数 N_RINGS 档）
TOP_VALUE = 10                          # 最内环（环心）的分值

PAGE_W, PAGE_H = 210.0, 297.0           # A4，mm
FRAME = 5.0                             # 外框距纸边

CX = 105.0                              # 中轴
BODY_HW = 95.0                          # 靶面半宽 → 靶面宽 190（A4 能放的极限）
BODY_BOT = 288.0                        # 靶面平底
CY = 162.0                              # 环心高度

A_STEP = BODY_HW / (N_RINGS - 1)        # 环带宽（自动 = 95/(挡数-1)）
CAP_R = 0.66                            # 圆头半高 / 半宽（参考图实测）
SIDE_K = 1.50                           # 直边长 / 半宽（参考图实测）
RATIO_H = CAP_R + SIDE_K / 2            # 竖半高 / 半宽 = 1.41

# 头部（照参考靶实测的比例）
HEAD_TOP_Y = 7.0                        # 头顶最高点
HEAD_H = 70.0                           # 头部高：最高点 → 头部底角
HEAD_HW = 42.8                          # 头部最宽处半宽
HEAD_BASE_HW = 40.2                     # 头部底角半宽（比最宽处往里收）
HEAD_WIDE_R = 0.68                      # 最宽处落在头部高度的几成处（0=顶，1=底）
HEAD_ARC_HW = 37.3                      # 顶部圆弧两端的半宽
HEAD_ARC_H = 11.3                       # 顶部圆弧的竖向高度

SHOULDER_DEG = 28.0                     # 肩线与水平线的夹角；越小肩越平（参考靶约 28°）

W_SIL = 1.2                             # 靶面轮廓线宽
W_RING = 0.4                            # 环线线宽
W_FRAME = 0.8                           # 外框
W_BOX = 0.6                             # 信息框
W_GRID = 0.25                           # 表格线
W_LINE = 0.3                            # 填空横线

FS_BIG10 = 15.0                         # 环心大号分值
FS_RINGNO = 4.5                         # 环号
FS_TITLE = 11.0                         # 标题「胸环靶」
FS_LABEL = 4.0                          # 字段名

BOX = (152.0, 7.0, 50.0, 71.5)          # 记分/信息合一框 x,y,w,h（框底不能压到肩线）
BOX_FIELDS = ["日期", "时间", "姓名", "组别", "靶位"]
BOX_COLS = 5                            # 记分格横向格数

FONT_CN = "Microsoft YaHei, SimHei, sans-serif"
FONT_NUM = "Arial, Helvetica, sans-serif"
# ─────────────────────────────────────────────────────────

HEAD_BASE_Y = HEAD_TOP_Y + HEAD_H               # 头部底角高度
HEAD_WIDE_Y = HEAD_TOP_Y + HEAD_WIDE_R * HEAD_H # 头部最宽处高度
HEAD_ARC_Y = HEAD_TOP_Y + HEAD_ARC_H            # 顶部圆弧两端的高度
# 肩线从头部底角斜到靶面竖边；夹角一定，竖边起点（SHOULDER_Y）就跟着定
SHOULDER_Y = HEAD_BASE_Y + (BODY_HW - HEAD_BASE_HW) * tan(radians(SHOULDER_DEG))

V_OUT = TOP_VALUE - (N_RINGS - 1)       # 最外一档的分值


def value_of(i):
    """第 i 层环的分值（i=0 是最内的环心）。"""
    return TOP_VALUE - i


def contour(k):
    """第 k 条环线的操场形参数（a=半宽, c=圆头半高, h=直边半长）。
    k=1 最内（环心那档的外沿），k=N_RINGS-1 最外（贴着靶面竖边）。"""
    a = A_STEP * k
    return a, CAP_R * a, SIDE_K * a / 2.0


def band_mid(i, vertical=False):
    """第 i 层环带中线到环心的距离（i=1..N_RINGS-2 才有意义）。"""
    d = RATIO_H * A_STEP if vertical else A_STEP
    return d * (i + 0.5)


def ring_path(a, c, h):
    x1, x2 = CX + a, CX - a
    return (f"M {x1:.2f},{CY-h:.2f} L {x1:.2f},{CY+h:.2f} "
            f"A {a:.2f},{c:.2f} 0 0 1 {x2:.2f},{CY+h:.2f} "
            f"L {x2:.2f},{CY-h:.2f} "
            f"A {a:.2f},{c:.2f} 0 0 1 {x1:.2f},{CY-h:.2f} Z")


def silhouette_path():
    """靶面轮廓，一路画下来：
    左肩 → 头部底角 → 头最宽处 → 顶部圆弧外端 → 圆弧过顶 → 右边镜像 → 平底。"""
    # 顶部圆弧用二次贝塞尔。控制点放在最高点上方 HEAD_ARC_H 处，
    # 这样曲线中点（= 控制点与两端点的平均）正好落在 HEAD_TOP_Y，弧顶高度就是设定的。
    arc_ctrl_y = HEAD_TOP_Y - HEAD_ARC_H
    return (f"M {CX - BODY_HW:.2f},{SHOULDER_Y:.2f} "
            f"L {CX - HEAD_BASE_HW:.2f},{HEAD_BASE_Y:.2f} "
            f"L {CX - HEAD_HW:.2f},{HEAD_WIDE_Y:.2f} "
            f"L {CX - HEAD_ARC_HW:.2f},{HEAD_ARC_Y:.2f} "
            f"Q {CX:.2f},{arc_ctrl_y:.2f} {CX + HEAD_ARC_HW:.2f},{HEAD_ARC_Y:.2f} "
            f"L {CX + HEAD_HW:.2f},{HEAD_WIDE_Y:.2f} "
            f"L {CX + HEAD_BASE_HW:.2f},{HEAD_BASE_Y:.2f} "
            f"L {CX + BODY_HW:.2f},{SHOULDER_Y:.2f} "
            f"L {CX + BODY_HW:.2f},{BODY_BOT:.2f} "
            f"L {CX - BODY_HW:.2f},{BODY_BOT:.2f} Z")


def num(x, y, txt, size=FS_RINGNO, bold=False):
    b = ' font-weight="bold"' if bold else ''
    return (f'<text x="{x:.2f}" y="{y:.2f}"{b} font-family="{FONT_NUM}" '
            f'font-size="{size}" text-anchor="middle" fill="#000">{txt}</text>')


def build_svg() -> str:
    o = []
    add = o.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" '
        f'height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">')
    add('<rect width="100%" height="100%" fill="#ffffff"/>')
    add(f'<rect x="{FRAME}" y="{FRAME}" width="{PAGE_W-2*FRAME}" '
        f'height="{PAGE_H-2*FRAME}" fill="none" stroke="#000" '
        f'stroke-width="{W_FRAME}"/>')

    body = silhouette_path()
    add(f'<path d="{body}" fill="none" stroke="#000" '
        f'stroke-width="{W_SIL}" stroke-linejoin="miter"/>')
    add(f'<defs><clipPath id="body"><path d="{body}"/></clipPath></defs>')
    add('<g clip-path="url(#body)">')

    # 环线 N-1 条
    for k in range(1, N_RINGS):
        add(f'<path d="{ring_path(*contour(k))}" fill="none" stroke="#000" '
            f'stroke-width="{W_RING}"/>')

    # 中间各档环号：十字排（水平一排 + 竖直一排），左右/上下对称
    for i in range(1, N_RINGS - 1):
        v = value_of(i)
        dx, dy = band_mid(i), band_mid(i, vertical=True)
        for sx in (-1, 1):
            add(num(CX + sx * dx, CY + FS_RINGNO * 0.36, v))
            add(num(CX, CY + sx * dy + FS_RINGNO * 0.36, v))

    # 环心
    add(num(CX, CY + FS_BIG10 * 0.36, TOP_VALUE, FS_BIG10, bold=True))

    # 最外一档：头顶 + 底部两角
    head_mid = (HEAD_TOP_Y + CY - RATIO_H * BODY_HW) / 2
    add(num(CX, head_mid, V_OUT))
    add(num(CX - 80, BODY_BOT - 10, V_OUT))
    add(num(CX + 80, BODY_BOT - 10, V_OUT))
    add('</g>')

    # 标题（左上空白处）
    add(f'<text x="{CX - 69}" y="48" font-family="{FONT_CN}" '
        f'font-size="{FS_TITLE}" font-weight="bold" text-anchor="middle" '
        f'fill="#000" letter-spacing="2">胸环靶</text>')

    # ── 右上：信息 + 记分 合一的框 ──
    bx, by, bw, bh = BOX
    add(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" '
        f'stroke="#000" stroke-width="{W_BOX}"/>')
    pad = 3.0
    f_top, f_lh = by + 10.5, 7.5
    for i, name in enumerate(BOX_FIELDS):
        ty = f_top + i * f_lh
        add(f'<text x="{bx+pad}" y="{ty:.2f}" font-family="{FONT_CN}" '
            f'font-size="{FS_LABEL}" fill="#000">{name}：</text>')
        add(f'<line x1="{bx+pad+11:.2f}" y1="{ty+1.2:.2f}" '
            f'x2="{bx+bw-pad:.2f}" y2="{ty+1.2:.2f}" '
            f'stroke="#000" stroke-width="{W_LINE}"/>')

    gx0, gx1 = bx + pad, bx + bw - pad
    gy0 = f_top + (len(BOX_FIELDS) - 1) * f_lh + 5
    rows, cell_h = 2, 7.6
    gy1 = gy0 + rows * cell_h
    cw = (gx1 - gx0) / BOX_COLS
    for i in range(rows + 1):
        y = gy0 + i * cell_h
        add(f'<line x1="{gx0}" y1="{y:.2f}" x2="{gx1}" y2="{y:.2f}" '
            f'stroke="#000" stroke-width="{W_GRID}"/>')
    for i in range(BOX_COLS + 1):
        x = gx0 + i * cw
        add(f'<line x1="{x:.2f}" y1="{gy0:.2f}" x2="{x:.2f}" y2="{gy1:.2f}" '
            f'stroke="#000" stroke-width="{W_GRID}"/>')
    for n in range(1, rows * BOX_COLS + 1):
        r_, c_ = divmod(n - 1, BOX_COLS)
        add(f'<text x="{gx0 + c_*cw + 1.2:.2f}" y="{gy0 + r_*cell_h + 3.0:.2f}" '
            f'font-family="{FONT_NUM}" font-size="2.4" fill="#000">{n}</text>')
    ty_ = gy1 + 6.5
    add(f'<text x="{gx0}" y="{ty_:.2f}" font-family="{FONT_CN}" '
        f'font-size="{FS_LABEL}" fill="#000">合计</text>')
    add(f'<line x1="{gx0+11:.2f}" y1="{ty_+1.2:.2f}" x2="{gx1:.2f}" '
        f'y2="{ty_+1.2:.2f}" stroke="#000" stroke-width="{W_LINE}"/>')

    add('</svg>')
    return "\n".join(o)


def report():
    """跑完打印一张换算表，方便挑挡数。"""
    print("现在：N_RINGS=%d  环带 %.1fmm  分值 %d~%d  环心环直径 %.1fmm"
          % (N_RINGS, A_STEP, TOP_VALUE, V_OUT, 2 * A_STEP))
    print("  靶面 %.0f x %.0fmm，环心 y=%.0f，最外环线竖半高 %.1f"
          % (2 * BODY_HW, BODY_BOT - HEAD_TOP_Y, CY, RATIO_H * BODY_HW))
    print("  头部最宽 %.1fmm（y=%.1f），底角 %.1fmm，肩线 %.0f°，竖边从 y=%.1f 起"
          % (2 * HEAD_HW, HEAD_WIDE_Y, 2 * HEAD_BASE_HW, SHOULDER_DEG, SHOULDER_Y))
    for k in range(1, N_RINGS):
        a, c, h = contour(k)
        print("    环线%d 外沿  宽 %.1f 高 %.1f mm" % (k, 2 * a, 2 * (c + h)))
    print("改挡数换算表（靶面宽度固定 190mm）：")
    for n in range(3, 11):
        print("    N_RINGS=%2d -> 环带 %5.1fmm  分值 %d~%d"
              % (n, 2 * BODY_HW / 2 / (n - 1), TOP_VALUE, TOP_VALUE - n + 1))


if __name__ == "__main__":
    out = Path(__file__).with_name("target_A4.svg")
    out.write_text(build_svg(), encoding="utf-8")
    print("written:", out)
    report()
