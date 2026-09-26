# Figure 10: selected detection outcomes

`draw_fig10.py` produces `fig10_detection_cases.pdf` and editable,
self-contained `detection_cases_abc.svg`. It reads the pinned
`experiments/v4_protocol/qualitative_detections.json` prediction cache and the
reviewed dev61 YOLO label files. The three selected images are
`new_test_set_0014` (fallen cylinder), `new_test_set_0006` (empty-label false
alarm), and `new_test_set_0005` (one label, two A predictions). These inputs
have no visible stock-photo watermark in the selected display. The rows are
illustrative, not a sample from which to infer prevalence. Predictions are
shown at confidence >=0.25, using the cached A/B/C deployment checkpoints
(`yolo26s` epochs 280/200/260). The D column contains no inferred boxes.

White dashed boxes are the reviewed labels; solid arm-colour boxes and numeric
confidence labels are cached predictions. The original images are embedded in
the PDF/SVG. Regeneration requires the private dev61 image and label files.

Suggested caption:

> Figure 10. Illustrative detection outcomes on three dev61 images. The first
> row includes a fallen cylinder detected by C; the second is an empty-label
> image on which A produces a false alarm; the third has one labelled cylinder
> with two A predictions and one prediction each from B and C. Reviewed labels
> are white dashed boxes and predictions are solid boxes with confidence
> scores (threshold 0.25). The D column is reserved. These hand-selected
> examples illustrate the quantitative results and do not estimate error
> frequency.

Regenerate with the project's `.venv` Python:

```powershell
& 'D:\yolo\.venv\Scripts\python.exe' 'D:\yolo\paper\figures\fig10\draw_fig10.py'
```
