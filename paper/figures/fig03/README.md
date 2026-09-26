# Figure 3: training-image examples

`draw_fig3.py` produces `fig3_training_examples.pdf` and the self-contained
editable `training_examples_abc.svg`. The examples are actual images from the
completed A/B/C training pools. Each row matches one real A seed to one B
augmentation of that seed; the B mapping is reconstructed from the documented
seed-42 trim and on-disk output order in `scripts/make_aug1085_dataset.py`.
C examples are independent, reviewed image edits of *other* real93 seeds.
Their position on a row does not imply correspondence to that row's A image.
Red outlines use the on-disk YOLO training labels. The D column is left blank
until reviewed LoRA text-to-image samples exist. The PDF and SVG embed the
original image pixels; regeneration reads the private on-disk datasets.

Selected sources: A `real_photo_30`, `real_photo_50`, `real_photo_70`; C
`Placement_Issues_0001`, `Placement_Issues_0554`,
`Placement_Issues_0515`. The script resolves the corresponding B sample IDs
deterministically and asserts the C samples occur in the training list.

Suggested caption:

> Figure 3. Examples of the training data arms. Columns A and B are paired by
> row: each classically augmented image is derived from the real photograph
> immediately to its left. Column C shows independently edited images of
> other real93 seeds; vertical placement does not denote a matched edit.
> Red boxes are reviewed training labels. The D column is reserved for
> reviewed LoRA text-to-image samples.

Regenerate with the project's `.venv` Python:

```powershell
& 'D:\yolo\.venv\Scripts\python.exe' 'D:\yolo\paper\figures\fig03\draw_fig3.py'
```
