# Fig. 2 — data provenance and generative workflows

`draw_fig2.py` generates the manuscript-ready vector PDF
`fig2_generation_workflows.pdf` and editable `generation_workflows_v5.svg` in
this folder. Two on-site inspection photographs are embedded from
`source_real93_a.jpg` and `source_real93_b.jpg`, extracted from picture shapes
7 and 9 of the archived author PPTX; they illustrate the real93 origin and
are not a before/after pair. The corpus also includes web-sourced
real photographs. Panel (a) shows the completed C editing route with separate
photo and instruction inputs. Panel (b) separates completed D LoRA fitting
from the still-pending formal 1,085-image dataset. The old
`../archive/v4/fig2_arms_samples.pdf` remains as v4 example material and is no
longer the manuscript's Fig. 2.

## Exact model and workflow record supplied by the author

### C: Qwen-Image-Edit-2509

| Component | File |
|---|---|
| Main image-edit model | `qwen_image_edit_2509_fp8_e4m3fn.safetensors` |
| Text encoder | `qwen_2.5_vl_7b_fp8_scaled.safetensors` |
| VAE | `qwen_image_vae.safetensors` |
| Four-step acceleration LoRA | `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` |

The earlier workflow drawing includes a mode switch between the original
sampling path and the Lightning LoRA path. The exact workflow JSON and the mode
used for each retained image are still to be archived; the diagram does not
assert that every retained C image used four-step sampling.

### D: real93-trained Qwen-Image-2.1 LoRA

- The active Runpod training uses 93 reviewed image-caption pairs with
  Qwen-Image-2.1, dataset repeat `5`, `4` epochs (`1,860` planned steps),
  rank `16`, and learning rate `1e-4`. The latest verified progress and exact
  script are in `docs/v5_prompts/runpod_qwen21_handoff.md` and
  `runpod_qwen21/run_train.sh`.
- The earlier Liblib template used 2,000 steps, learning rate `0.0004`,
  rank `16`, no cropping, and Qwen tagging threshold `0.30`; that weight is
  incompatible with the current 2.1 model. Its seven trial PNGs are not D
  evidence. The dashed dataset target remains prospective pending a compatible
  checkpoint, synthesis, screening, and reviewed boxes.

## Regeneration

Run `draw_fig2.py` from the repository root with a Python interpreter that has
ReportLab. On the author's current Windows machine,
the working interpreter is
`C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
The code draws text and
shapes into both the PDF and SVG, and embeds the source photographs in each;
neither output depends on external image paths at viewing time. The archived
PPTX and extraction helper are in `../archive/drafts/`. The PDF is
included by `paper/working_paper.tex`.
