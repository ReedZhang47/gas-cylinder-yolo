# Figure 1: v5 study pipeline

`draw_fig1.py` generates the vector master `main_pipeline_v5.svg` and the PDF used by the paper at `../fig1_pipeline.pdf`. It does not use `paper/make_figures.py`.

The supplied `main_pipeline.md`, `main_pipeline.svg`, and `main_pipeline.pptx` remain as v4 references. The new figure adds the planned D arm with a dashed border and arrow. `dev61` enters development evaluation only; it is not a training input. Remove the pending styling and replace the target count only after D's dataset and runs are verified.

Regenerate from the repository root with the bundled Python (the project `.venv` currently lacks ReportLab):

```powershell
& 'C:\Users\Reed\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\yolo\paper\figures\new fig1\draw_fig1.py'
```
