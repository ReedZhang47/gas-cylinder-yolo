# Fig. 2 — data provenance and generative workflows

`draw_fig2.py` generates the manuscript-ready vector PDF at
`../fig2_generation_workflows.pdf` and the editable `generation_workflows_v5.svg`.
The two on-site inspection photographs in panel (a) are embedded from picture
shapes 7 and 9 in the author's `fig1_pipeline.pptx`; they illustrate the real93
origin and are not a before/after pair. The real93 corpus also includes
web-sourced real photographs. Panel (b) diagrams the completed C arm. Panel
(c) separates D's completed LoRA training from its still-pending formal
1,085-image dataset. The old `../fig2_arms_samples.pdf` remains as v4 example
material and is no longer the manuscript's Fig. 2.

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

### D: real93-trained Qwen-Image LoRA

- Training workflow: standard Qwen-Image LoRA training flow; 2,000 training
  steps, learning rate `0.0004`, LoRA rank `16`, no cropping.
- Tagging algorithm: “通义千问” (Qwen), threshold `0.30` as supplied by
  the author. The workflow JSON should later pin down the threshold's precise
  node and interpretation.
- The trained LoRA is used for trial text-to-image generation with
  Qwen-Image-2.1. Formal candidate screening, human box review, and the
  1,085-image D training dataset remain pending.

## Regeneration

Run `draw_fig2.py` from the repository root with a Python interpreter that has
`python-pptx`, Pillow, and ReportLab. On the author's current Windows machine,
the working interpreter is
`C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
The code draws text and
shapes into both the PDF and SVG, and embeds the source photographs in each;
neither output depends on external image paths at viewing time. The PDF is
included by `paper/working_paper.tex`.
