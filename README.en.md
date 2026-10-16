# A4 Target Generator

Generates a printable A4 chest-ring target (胸环靶) as SVG, PDF and PNG. 胸环靶 is the human-silhouette target used in Chinese shooting practice. Change a single number and you get a different ring count.

[中文说明](README.md)

![A4 target](preview.png)

The field labels on the target are in Chinese (date, time, name, group, lane). The ring numbers and the large 10 are numeric.

## Running it

`generate_target.py` is the main script. It writes `target_A4.svg` next to itself.

```bash
python generate_target.py
```

For the PDF and the preview image, run `export_pdf.py`, which reads that SVG:

```bash
python export_pdf.py
```

The PDF page is exactly 210×297mm. Set your print dialog to "Actual size" or 100%; "Fit to page" will shrink it.

The only dependency is playwright:

```bash
pip install playwright
```

A downloaded Chromium is not required. The script falls back to a local Edge or Chrome install.

## Ring count

Open `generate_target.py`. The first entry in the parameters block is `N_RINGS`, the single switch for the ring count. The target face always stretches to the full A4 width (190mm), and the ring width is derived as `95/(N_RINGS-1)`, so changing that one number moves every ring line and every score with it.

| N_RINGS | ring width | scores |
|---|---|---|
| 3 | 47.5mm | 10~8 |
| 4 | 31.7mm | 10~7 |
| 5 | 23.8mm | 10~6 |
| 6 | 19.0mm | 10~5 |
| 8 | 13.6mm | 10~3 |
| 10 | 10.6mm | 10~1 |

The script prints this table when it runs, so you do not have to go looking for it. The image in this repo was generated with 5 rings.

Fewer rings means wider bands and easier scoring. A4 is only so big, so ring count and ring width trade off against each other.

## How the target is drawn

The ring layout follows the standard chest-ring target. Ring lines are equally spaced stadium shapes, two vertical straight sides plus rounded top and bottom, not ellipses. The straight sides of the outermost ring line sit exactly on the two vertical edges of the target face. Anything larger would have nowhere to go, so the widest score band only appears across the head and the two bottom corners, which is how the standard target arranges it.

`CAP_R = 0.66` (cap half-height over half-width) and `SIDE_K = 1.50` (straight side length over half-width) in the parameters block control that shape, if you want fatter caps or longer sides.

The head outline and shoulder angle came off the same reference: the top of the head is a wide, shallow arc that only reaches the straight sides at a half-width of 37.3mm, the sides flare out to 42.8mm at their widest and taper back in to 40.2mm at the base, and the shoulder line sits at 28° to horizontal. Those live in the `HEAD_*` group and `SHOULDER_DEG`. Change the shoulder angle and the vertical side edge moves with it, which pushes the box down into the shoulder line, so `BOX` has to move too.

The box in the upper right combines the information fields and the scoresheet: five blank lines plus a 2×5 grid. The field names live in `BOX_FIELDS`; the box itself is `BOX`. Adding a field pushes the grid down into the shoulder line.

## Files

| File | Purpose |
|---|---|
| `generate_target.py` | Writes the SVG. All parameters are in the block at the top of this file |
| `export_pdf.py` | SVG to PDF, plus `preview.png` |
| `target_A4.svg` | Vector output, stays sharp at any print size |
| `target_A4.pdf` | For printing |
| `preview.png` | The preview above |

## Fonts

Chinese text in the SVG is set in `Microsoft YaHei, SimHei, sans-serif`, numbers in `Arial, Helvetica`. That works as-is on Windows. On Linux and macOS the system fallback takes over, so the 胸环靶 title may render in a different typeface.

## License

MIT, see `LICENSE`.
