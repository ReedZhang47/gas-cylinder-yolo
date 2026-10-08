# v5 D 臂：提示词与批量生图

## 当前入口

截至 2026-10-08，D 人工图像审核已完成；原两组筛选后补充 new24，实际保留 **new150 551＋real93 421＋new24 113＝1085 张**。来源在 `D:\gas_cylinders\D`，最终图片在 `D:\gas_cylinders\D1085\images`，按上述顺序统一命名；当前待框标注与复核。核验与映射见 `d1085_review_and_metadata_20261008.md`。2026-10-04 原两组 1308 张候选的运行方法仍见 `full_generation_20261004.md`。

后续不再重复读取 Comfy Desktop 日志。逐图参数以 PNG 元数据为准，工作流使用本目录 JSON；C/D 各 1085 张的 seed、提示词已统一导出到 `cd1085_seed_prompts.csv`（严格 3 列/2170 数据行）。new24 的 24 段原始正向文本已入表，ID N151–N174；提示词总表 `d_prompt_catalog.csv` 含 267 条。既有训练和加载验证留档供引用。

兼容 Qwen-Image-2.1 的 real93 LoRA 已完成训练及本机固定输入验证。训练方法、参数、loss、哈希、权重维度和 N114 五张对照记录见 qwen21_lora_training_validation.md；Runpod 资源收尾与完整归档见 ../archive/runpod_qwen21_handoff.md。旧 Liblib 权重与当前底模不兼容，旧工作流及单图/小批过程记录已移入本地 `../archive/comfy_pilots_20261004/`，不再纳入 Git。

| 文件 | 角色 |
|---|---|
| ../Prompts_Based_on_real93.md | 原始 93 条描述素材，保留供对照 |
| real93_cores.tsv、new150_cores.tsv | 逐条可审阅的场景核心 |
| build_prompt_sets.py | 检查 ID、数量、重复并生成完整提示词 |
| real93_prompts.jsonl、new150_prompts.jsonl | 提示词编辑源；draft 为源文件状态，本批已获作者授权并使用 approved 冻结副本完成生成 |
| new24_prompts.csv、new24_prompts.jsonl | 从审核后的 new24 PNG 提取的 24 段原文；N151–N174，保留数合计 113 |
| d_prompt_catalog.csv | real93 93＋new150 150＋new24 24 的 267 条提示词总表及实际保留数 |
| cd1085_seed_prompts.csv | C/D 两臂当前图名、seed、提示词：3 列，2170 数据行 |
| d1085_review_and_metadata_20261008.md、cd_metadata_20261008_audit.json | 人工筛选完成状态、目录数量、元数据提取方法和导出校验 |
| d1085_source_mapping.json | D 最终图名与审核源图的一对一 SHA256 映射 |
| new24_workflows/ | new24 的实际 API / GUI 工作流快照 |
| real93_lora_metadata.csv | 已用于云端 LoRA 训练的 93 条人工复核 caption 精确副本（无照片） |
| generation_models.md | C/D 精确模型组件和现用工作流入口；不依赖本地历史归档 |
| qwen21_lora_training_validation.md | 实际训练环境与参数、loss/检查点、维度核对和固定 N114 推理验证 |
| qwen21_lora_n114_validation.csv | 五张固定 seed 对照图的有效强度、连线、参数和 PNG SHA256 |
| pilot_workflow_ui.json、pilot_workflow_api.json | 接入 step-1860 的试运行 GUI/API 工作流；作者指定 LoRA 0.8，GUI randomize |
| full_generation_20261004.md | R001/N092 修词与复测、1308 张候选完成记录、冻结输入及历史运行方法 |
| full_generation_20261004_completion.json | 完成时间、批次数量、复制目录及待筛选/标注状态的持久摘要 |
| scripts/run_comfy_v5_batch.py | 两套提示词的后台控制器，逐图进度与停止文件 |
| scripts/comfy_batch_t2i.py | 默认 dry-run；顺序排队、随机或确定性 seed、恢复和 manifest；seed 从 PNG 统一导出 |
| scripts/export_cd_png_metadata.py | 只读当前 PNG，提取 seed/正向文本、归并 new24 和核对 D 来源映射 |

LoRA 训练使用的 93 条人工复核 caption 已保存在 real93_lora_metadata.csv；本机 .tmp/runpod_qwen21/real93 和已上传的 real93_REVIEWED.tar 使用同一内容。它们与后续批量生图提示词是两个不同产物。有关旧数据包、传输和训练启动的历史记录在 docs/archive/runpod_qwen21_2026-09-26.md。

## 当前数据整理流程

1. 已完成 GUI/API 单图、断点恢复和 14 张小批验证；作者接受其余小批问题，仅修正 R001/N092 后授权完整候选生成。冻结输入与工作流及其哈希已留档。
2. 人工筛选与补充批次、C/D seed 和提示词导出已完成；实际保留 real93 421、新场景 551＋113，共 1085 张。原 465＋620 仅为初始预算。
3. 对 `D1085\images` 打标并逐张复核，按实际图像内容确定类别和框；检查空标、近重复及与 dev61 的来源独立性，再冻结正式 D 训练清单。当前无 TXT 标签；不重复读取 Desktop 日志或重新提取已完成的汇总表。

保留的工作流、正式提示词、C/D 元数据、训练与生成方法用于后续标注、实验和写作。单图/小批测试、旧不兼容工作流及未执行的 RunComfy 方案仅在本地 docs/archive/ 留存。归档目录不随新克隆分发，当前工作不依赖它们。

2026-10-04 的历史顺序：API 单图使用 8189，后端重启后小批与完整批次使用 8188；修正 R001 页脚与 N092 粗大瓶身后，完整批次于北京时间 15:26–22:11 完成。随后人工筛选和 new24 补充已完成；当前进入标注、复核和训练输入冻结。
