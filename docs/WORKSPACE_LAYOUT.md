# 工作区与 Git 边界

2026-10-08 整理。当前阶段为 D1085 框标注与复核；提交和推送由作者手动完成。

## 继续纳入 Git

| 目录 / 文件 | 用途 |
|---|---|
| 根目录 README、PROGRESS、NEXT_STEPS、EXPERIMENTS、COMMANDS | 当前状态、执行顺序、实验协议和有效入口 |
| `annotator/`、`scripts/`（除 legacy） | 标注、数据整理、生成复现、YOLO 训练及评估脚本 |
| `docs/v5_prompts/` | 正式提示词、C/D 元数据、来源映射、工作流与训练/生成方法证据 |
| `runpod_qwen21/` | 已使用的 LoRA 训练脚本；保留用于方法复现，云端任务已经结束 |
| `experiments/v4_protocol/`、独立性与来源 JSON | 正式实验结果、折定义、逐图预测和统计依据 |
| `paper/` 的 TeX、BibTeX、表格、计划及现用脚本 | 正文、参考文献与写作依据 |
| `paper/figures/manuscript/` | 正文实际引用的六张 PDF；新克隆仍具有这些编译资源 |
| `paper/figures/ppt_editable/`（除 previews） | 当前可编辑 PPT、COM 脚本、scene.json 与必要图片素材 |

`scene.json` 和 `media/` 是当前 COM 绘图输入，保留。`paper/make_figures.py` 仍用于正文表格及 v4 结果复现，保留。图件只调整存放和引用路径，本次没有重新生成或覆盖人工修改的 PPT。

## 本地归档，不再追踪

| 目录 | 内容 |
|---|---|
| `_archive/20261008/tmp/` | 已结束任务的临时提取结果、冻结输入/运行清单、旧图预览与一次性检查脚本 |
| `docs/archive/comfy_pilots_20261004/` | API 单图、小批试生成、就绪检查、修词测试和旧不兼容工作流 |
| `docs/archive/` 其余内容 | 旧方案、云端运维交接和历史讨论 |
| `scripts/legacy/` | 旧实验脚本；新增 `runpod_preparation/` 保存 caption/上传包准备脚本 |
| `experiments/archive/` | 旧 p1/饱和度试点、v3 结果及已被最终统计覆盖的 interim 文件 |
| `paper/figures/archive/` | 旧 PDF/SVG/PPT、旧构图代码、检查记录与未使用素材 |

移动采用保留文件的方式，并校验移动前后 SHA256；本地移动清单在 `_archive/20261008/moves.json`。已被跟踪的归档目录执行了 `git rm --cached`，只停止追踪，本地文件保留；历史版本仍可从既有 Git 提交恢复。之后普通 `git add -A` 不会重新纳入这些归档。

`.tmp/`、`_trash/`、`weights/`、`runs/`、`logs/`、`.venv/`、`node_modules/`、`paper/reference/`、缓存与 `ppt_editable/previews/` 也由 `.gitignore` 排除。`.tmp/runpod_qwen21/` 的受限训练传输材料保持原位并继续忽略；不影响已归档的正式训练数据包和方法记录。

归档不随新克隆分发。论文所需的 C/D 模型记录已保存在 `docs/v5_prompts/generation_models.md`，训练参数在 `qwen21_lora_training_validation.md`，正式生成过程在 `full_generation_20261004.md`；当前工作不依赖旧运维和试点文件。
