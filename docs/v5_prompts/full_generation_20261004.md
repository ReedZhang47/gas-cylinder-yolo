# v5 扩大生成：2026-10-04

后续状态（2026-10-08）：本文记录原两组 1308 张候选的历史批次。人工筛选后追加 new24，最终保留 new150 551＋real93 421＋new24 113＝1085 张，位于 `D:\gas_cylinders\D1085\images`，待框标注；C/D seed、提示词和 24 段新增词归档已完成，当前核验入口为 `d1085_review_and_metadata_20261008.md`。以下候选路径、初始预算和待筛选状态均为 2026-10-04 快照。

作者指示：只修正 R001 底部检查表和 N092 过粗的气瓶，其余问题接受，随后扩大生成。按原定预算执行 real93 93×6=558 与 new150 150×5=750，共 **1308 张候选**；筛选目标仍为 465+620=1085 张。小批及修词复测图另存，不自动计入本批。

## 完成状态与下一步

本批已完成：北京时间 **2026-10-04 15:26:51–22:11:48**，运行约 **6 小时 45 分钟**。控制器最终状态为 `completed`，real93 完成 558/558，new150 完成 750/750。完成快照留档于 `full_generation_20261004_completion.json`。

作者已将候选复制到 `D:\gas_cylinders\D1085`；目录核对为 `real93` 558 张、`new150` 750 张 PNG，共 **1308 张**，当前无 TXT 标注文件。`D1085` 是目标数据集目录名，不代表已筛选出 1085 张合格图。下一步由作者人工筛选、打标和复核，目标保留 465+620=1085 张；按实际图像内容确定取舍及类别。

生成阶段已结束，**后续不再重复读取 Comfy Desktop 日志**。逐图提示词、seed 和实际参数以 PNG 元数据为准，工作流以工作区保存的 JSON 为准；seed 等元数据后续与 C 臂 1085 张统一导出。既有日志和技术验证仅保留作历史证据，不作为下一阶段重复巡检事项。本次核对完成状态和文件数量，未宣称逐图复制哈希或标注质量已复核。

## 提示词修正与证据

已从原始 PNG prompt 元数据核对，两条原提示词分别没有禁止检查表版式的具体构图要求、没有气瓶长径比描述。

R001 的底部检查表有训练数据来源：作者提供的 `D:\gas_cylinders\real_photo\93_real_photos\images\real_photo_8.png` 和实际训练输入 `.tmp/runpod_qwen21/real93/images/real_photo_8.png` 都含蓝白检查表与水印，两者 SHA256 相同，为 `97bb0ff0e7b9fffd318f289aaeb25ad062b8996f8ca84e709cacb5d851095652`。这证明此类版式元素进入过训练，支持 LoRA 学到并跨场景复现该版式的解释；不能据此精确归因某一张输出只来自第 8 张。第 1 张训练照片本身没有表格，并不排除其他训练图的影响。

- **R001**：仅对该 ID 覆盖通用的 inspection 风格句；描述相机向下拍摄，灭火器在画面上半部，下方四分之一必须是泥土、碎石、木片和钢筋，纹理连续延伸到画面下边缘。第一版罗列禁止表格/工具栏的提示词仍生成页脚，最终版采用具体的地面构图描述。
- **N092**：保留深棕色、蓝调时段、屋顶、横卧等场景要求，新增细长高压工业气瓶、约 1.4 米长/0.23 米直径、长径比至少 5、窄直筒身和圆肩的约束。这些尺寸是生成目标提示，不是对训练实物尺寸的测量。原词 gas cylinder 没有区分细长高压瓶与粗短储罐，训练中也有较粗的深棕色瓶。

修改同步到 `real93_cores.tsv` / `real93_prompts.jsonl`、`new150_cores.tsv` / `new150_prompts.jsonl` 和 `build_prompt_sets.py` 的 R001 专用风格覆盖。与 Git HEAD 比较，**243 条提示词正文仅 R001、N092 两条改变**。历史小批输入保留当时文本。

最终复测：

| ID | 输出原图 | SHA256 | 观察 |
|---|---|---|---|
| R001 | `D:\Comfy-Desktop\ComfyUI-Shared\output\v5_prompt_fixes_20261004_r2\R001_v01_00001_.png` | `c8a446bdb13da835389130fc127dca3edc9d00d2d641fa4223020be71eb12b9d` | 没有底部白色文字/表格条，底部为连续地面 |
| N092 | `D:\Comfy-Desktop\ComfyUI-Shared\output\v5_prompt_fixes_20261004\N092_v01_00001_.png` | `d91a1f9d9fa2b7ed9fcbbbbcddefdc2f72ac8fc500381aa8569a0976e47d441e` | 气瓶明显细长；仍为直立，按作者要求不追加姿态修正 |

两张 PNG 的提示词、LoRA 0.8 与文件哈希均核对。扩大批次的最初三张 R001 也未见检查表条，但其中部分仍有水平构图接缝；保留待人工筛选。修词不保证每个随机输出都无版式伪影。

## 运行参数与冻结输入

后台启动：北京时间 **2026-10-04 15:26:51**，结束于 **22:11:48**；两套输入均已完成。

参数沿用已验证的 Qwen-Image-2.1 INT8 convrot、step-1860 LoRA **0.8**、随机 seed、1184×896、25 步、CFG 1、Euler/simple、denoise 1、batch_size 1。本批使用服务 `http://127.0.0.1:8188`。seed 仅由 PNG prompt 元数据保存，文件名/manifest/控制台不逐图另记；后续与 C 臂统一导出。

按作者本次扩大指令，运行输入副本设置为 approved，审批范围为候选生成。源 JSONL 的编辑状态仍为 draft；人工图像取舍及框标注尚未完成。

| 冻结文件 | SHA256 |
|---|---|
| `_archive/20261008/tmp/comfy_v5_full_20261004_real93_prompts.jsonl` | `3612610cca4b302cb4325f105e4fae6eb5a24559a33128602fca1005cc1b8c99` |
| `_archive/20261008/tmp/comfy_v5_full_20261004_new150_prompts.jsonl` | `c29a6b5f2ed3980222ed37fd2849577ed5c2d0448e8f254c70bba826913e60ac` |
| `_archive/20261008/tmp/comfy_v5_full_20261004_workflow_api.json` | `be810dd5ce1549619a2611afaf264970c3c0b1d4560368ac627d7fde21230952` |

本次使用冻结副本；以上文件及运行清单保留作已完成批次的历史记录。工作区 `pilot_workflow_api.json` / `pilot_workflow_ui.json` 保存对应 API / GUI 工作流。

## 历史运行入口（本批已结束）

以下为追溯运行方法的记录，不是待执行操作；不再启动或恢复本批。2026-10-08 已将本批冻结副本、清单和过程输出移入忽略的 `_archive/20261008/tmp/`。旧配置内部仍保留当时的执行路径；历史命令不是可直接重新运行的当前入口。

- 输出：`D:\Comfy-Desktop\ComfyUI-Shared\output\v5_full_20261004\real93\` 和 `...\new150\`。
- 控制器：`scripts/run_comfy_v5_batch.py`，顺序执行两套输入；同一状态文件有进程锁，防止两个控制器同时运行。控制器会写 running/completed/failed/stopped 状态。
- 配置：`D:\yolo\_archive\20261008\tmp\comfy_v5_full_20261004_config.json`。
- 最终状态：`D:\yolo\_archive\20261008\tmp\comfy_v5_full_20261004_state.json`；持久完成摘要见 `full_generation_20261004_completion.json`。
- 日志：`_archive/20261008/tmp/comfy_v5_full_20261004_stdout.log`、`_archive/20261008/tmp/comfy_v5_full_20261004_stderr.log`。
- 清单：`_archive/20261008/tmp/comfy_v5_full_20261004_real93_manifest.jsonl`、`_archive/20261008/tmp/comfy_v5_full_20261004_new150_manifest.jsonl`。先记 submitted/prompt_id，再记 completed/输出哈希；恢复时跳过完成项，未完成提交沿用已有 prompt_id，不重新排队。恢复未完成提交需要原 Comfy history 仍可查询；若后端重启清空 history，先检查已有输出再处理。

本次没有设置额外的定时巡检；后台控制器负责执行与记录。实际总耗时约 6 小时 45 分钟。

历史停止方法：控制文件 `_archive/20261008/tmp/comfy_v5_full_20261004.stop` 使控制器在完成当前图后停止：

```powershell
New-Item -ItemType File -Path 'D:\yolo\_archive\20261008\tmp\comfy_v5_full_20261004.stop'
```

历史恢复方法需先确认原任务没有运行，处理停止文件或错误原因，再使用同一冻结配置与完成清单。原后台启动命令（本批已完成，无需执行）：

```powershell
Start-Process -FilePath 'E:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe' -ArgumentList @('-u','D:\yolo\scripts\run_comfy_v5_batch.py','--config','D:\yolo\_archive\20261008\tmp\comfy_v5_full_20261004_config.json') -WorkingDirectory 'D:\yolo' -WindowStyle Hidden -RedirectStandardOutput 'D:\yolo\_archive\20261008\tmp\comfy_v5_full_20261004_stdout.log' -RedirectStandardError 'D:\yolo\_archive\20261008\tmp\comfy_v5_full_20261004_stderr.log'
```
