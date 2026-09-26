# Figure 7: miss / false-alarm operating trade-off

`draw_fig7.py` creates `fig7_operating_tradeoff.pdf` and editable
`operating_tradeoff_abc.svg` from the completed A/B/C
`experiments/v4_protocol/per_image/per_image_*.json` caches. It uses the
`joint.oof_rows` for each arm: a dev61 image appears only in its held-out fold
after detector and checkpoint selection. The first `tp_masks` bit means a
correct match at IoU 0.50; at each confidence threshold the script counts
TP, FP, and FN. The denominators are 72 labelled objects and 61 images.

Panel (a) shows FN/72 against FP/61 for thresholds 0.05-0.95, with markers at
0.25 and 0.50. Panel (b) prints the exact count of missed labelled objects
and FP/image at confidence >=0.25. The D row is blank. When D is evaluated,
the same calculation can be applied to its validated per-image OOF cache.

This is development analysis, not final-test evidence. The figure uses
cross-fitted held-out predictions, not the full-dev61 deployment models. A
threshold chosen from dev61 needs confirmation on a new frozen external test.

Suggested caption:

> Figure 7. Operating trade-off from pooled held-out dev61 predictions at
> IoU 0.50. (a) Fraction of labelled objects missed versus false positives
> per image as the confidence threshold varies from 0.05 to 0.95. Filled and
> open markers indicate thresholds 0.25 and 0.50, respectively. (b) Exact
> miss count and false positives per image at 0.25. The D row is reserved for
> validated v5 results. The curves are development estimates.

Regenerate with the project's `.venv` Python:

```powershell
& 'D:\yolo\.venv\Scripts\python.exe' 'D:\yolo\paper\figures\fig07\draw_fig7.py'
```
