# Figure 4: arm-level development comparison

`draw_fig4.py` generates `fig4_arm_level_comparison.pdf` and editable
`arm_level_comparison_abc.svg` directly from
`experiments/v4_protocol/bootstrap_paired.json`. Panel (a) shows the A/B/C
joint detector-and-checkpoint cross-fitted pooled OOF mAP50-95 (filled circles)
and mAP50 (open circles). Panel (b) shows the observed A/B/C mAP50-95
differences and their 95% paired image-cluster bootstrap intervals. The D score
row and D-A/B/C contrasts are blank and labelled as reserved. The D extension
must read validated D results; it must not infer them from the v4 comparisons.

The source's `target=joint` comparisons use 10,000 whole-image paired bootstrap
resamples on dev61. dev61 has been used for development and is not a sealed
test set. D is a later v5 extension rather than a v4 preregistered arm.

Suggested caption:

> Figure 4. Arm-level comparison on the independently sourced dev61 development
> set (61 images). (a) Joint detector-and-checkpoint cross-fitted pooled OOF AP
> for the three completed arms. (b) Observed differences in mAP50-95 with 95%
> paired image-cluster bootstrap intervals (10,000 resamples). Intervals for
> C-A and C-B exclude zero; the B-A interval crosses zero. Empty D slots are
> reserved for validated v5 results.

Generate with the project's `.venv` Python:

```powershell
& 'D:\yolo\.venv\Scripts\python.exe' 'D:\yolo\paper\figures\fig04\draw_fig4.py'
```
