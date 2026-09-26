# Figure 5: detector-wise performance

`draw_fig5.py` reads the three completed v4 protocol JSON files and generates
`fig5_detector_consistency.pdf` and the editable vector master
`detector_consistency_abc.svg`. The six columns are `yolov8s`, `yolov8m`,
`yolo11s`, `yolo11m`, `yolo26s`, and `yolo26m`. Every printed number is the
**fixed-endpoint `last.pt` result at epoch 300 on dev61**, rounded to three
decimals. Panel (a) reports mAP50-95 and panel (b) reports mAP50. Both panels
use the same 0-1 colour scale. These are descriptive development-set scores;
the joint cross-fitted OOF result and its paired intervals belong in Fig. 4.
Displayed scores below 0.50 use black numerals; displayed scores of 0.50 or
higher use white numerals. The colour ramp is tuned so both sides of that fixed
threshold retain at least 4.5:1 numeral-to-cell contrast.

The D row is deliberately blank. After the D training and evaluation are
verified, extend the script's `ARMS` input list with the D result file and let
the same validation and plotting code fill those cells. Do not copy or infer D
values from the A/B/C data.

Suggested caption:

> Figure 5. Fixed-endpoint performance by detector and training-data arm on
> dev61 (61 images). Each model was evaluated at epoch 300 under the shared
> training protocol. (a) mAP50-95, the primary metric; (b) mAP50. Cell colour
> uses a common 0-1 AP scale, and the numeric scores are shown inside cells.
> The blank D row is reserved for validated LoRA text-to-image results. These
> development-set results describe detector-wise behaviour; the arm-level
> cross-fitted comparison is reported separately in Fig. 4.

The v4 `fig4_bootstrap_ci.pdf` is archived in `../archive/v4/`.

Regenerate from the repository root with the bundled Python:

```powershell
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\yolo\paper\figures\fig05\draw_fig5.py'
```
