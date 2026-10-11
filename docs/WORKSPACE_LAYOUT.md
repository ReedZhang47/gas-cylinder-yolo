# 工作区与 Git 边界

2026-10-08 整理。D1085 六 detector 训练、评估及统计已完成验收；作者回复“继续”后，D493 规模实验完整流水线于 2026-10-10 北京时间 01:44 启动、06:20 完成，结果已落盘，待独立验收。提交和推送由作者手动完成。

## 继续纳入 Git

| 目录 / 文件 | 用途 |
|---|---|
| 根目录 README、PROGRESS、NEXT_STEPS、EXPERIMENTS、COMMANDS | 当前状态、执行顺序、实验协议和有效入口 |
| `annotator/`、`scripts/`（除 legacy） | 标注、数据整理、生成复现、YOLO 训练及评估脚本 |
| `docs/v5_prompts/` | 正式提示词、C/D 元数据、来源映射、工作流与训练/生成方法证据 |
| `runpod_qwen21/` | 已使用的 LoRA 训练脚本；保留用于方法复现，云端任务已经结束 |
| `experiments/v4_protocol/`、`experiments/v5_d/`、`experiments/v5_d_scale/`、独立性与来源 JSON | v4/D1085 正式结果；D493 抽样冻结及后续评测；折定义、逐图预测和统计依据 |
| `experiments/lora_compare/`（除可再生评审图片与 ZIP） | 最终参数评价、原始评分/裁决、冻结协议、逐图标签、版本证据及验收哈希 |
| `paper/` 的 TeX、BibTeX、表格、计划及现用脚本 | 正文、参考文献与写作依据 |
| `paper/figures/manuscript/` | 正文实际引用的六张 PDF；新克隆仍具有这些编译资源 |
| `paper/figures/lora_compare/`、`paper/tables/lora_*` | LoRA 三指标主图/表、提示词补充图、原图对照与完整网格 |
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

2026-10-11 LoRA 评价收尾：删除 53 个一次性脚本、渲染预览及废弃 v1/v2 评审 ZIP，约 1010.87 MiB。旧 ZIP 中图片已逐字节核验为当前评审图片的重复副本；旧页面和说明另存 `experiments/lora_compare/versions/v1/review_pages/` 与 `v2/review_pages/`。版本源码/协议、原始 v3 评分、裁决、当前匿名包与全部正式产物继续保留。清单与删除前哈希见 [cleanup_manifest.json](../experiments/lora_compare/cleanup_manifest.json)，可复核入口为 [audit_lora_compare.py](../scripts/audit_lora_compare.py)。`.tmp/lora-eval/` 含 CLIP 模型和运行依赖，属于复现所需本地环境，未清理。

归档不随新克隆分发。论文所需的 C/D 模型记录已保存在 `docs/v5_prompts/generation_models.md`，训练参数在 `qwen21_lora_training_validation.md`，正式生成过程在 `full_generation_20261004.md`；当前工作不依赖旧运维和试点文件。
