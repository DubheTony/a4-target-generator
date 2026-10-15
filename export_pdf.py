# -*- coding: utf-8 -*-
"""把 target_A4.svg 渲染成 PDF（A4 实际尺寸，1:1）和 README 用的预览图。

用本机已装的 Playwright + Chromium 渲染，好处是中文系统字体和矢量线都能正确输出，
PDF 页面尺寸就是 210x297mm，打印时选"实际大小/100%"即得设计尺寸。

用法： python export_pdf.py       # 出 target_A4.pdf + preview.png
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SVG = HERE / "target_A4.svg"
PDF = HERE / "target_A4.pdf"
PNG = HERE / "preview.png"

# 用一层 HTML 包住 SVG，靠 @page 把纸张钉死成 A4，避免 Chromium 自己加边距
HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>
  @page { size: 210mm 297mm; margin: 0; }
  html,body { margin:0; padding:0; }
  svg { display:block; width:210mm; height:297mm; }
</style></head><body>
__SVG__
</body></html>"""


def main():
    from playwright.sync_api import sync_playwright

    if not SVG.exists():
        sys.exit(f"找不到 {SVG}，先跑 generate_target.py")
    svg_text = SVG.read_text(encoding="utf-8")
    html = HTML.replace("__SVG__", svg_text)

    tmp_html = HERE / "_临时" / "_render.html"
    tmp_html.parent.mkdir(exist_ok=True)
    tmp_html.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        b = None
        for ch in (None, "msedge", "chrome"):        # 没下 Chromium 就用本机 Edge
            try:
                b = p.chromium.launch(channel=ch) if ch else p.chromium.launch()
                break
            except Exception:
                continue
        if b is None:
            sys.exit("Playwright 找不到可用的浏览器（本机 Edge 也没试通）")
        pg = b.new_page(viewport={"width": 794, "height": 1123})
        pg.goto(tmp_html.as_uri())
        pg.wait_for_timeout(300)
        pg.pdf(path=str(PDF), format="A4", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        # 预览用的位图：4 px/mm，方便放大看细节（也直接当 README 的示例图）
        pg.set_viewport_size({"width": 210 * 4, "height": 297 * 4})
        pg.wait_for_timeout(200)
        pg.screenshot(path=str(PNG), full_page=True)
        b.close()
    print("PDF ->", PDF)
    print("PNG ->", PNG)


if __name__ == "__main__":
    main()
