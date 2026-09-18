# PROGRESS.md — 工地危险样本扩充项目（v3）

> ## 约定
> - 需求 prompt 写入 `D:\yolo\Prompt.md`（仅用户可编辑，AI 只读）。
> - 本文件是**唯一进度台账**：每轮工作完成并验证后立即更新（结果数字、产物路径、下一步、新坑）；改前先读当前版本，改完刷新文首「截止」行。
> - 命令/路径变化必须同步 `COMMANDS.md`；全文禁止引用不存在的文件。
> - 弃用文件一律移入 `_trash\`（勿真删）。**红线：任何训练池都不得包含 test 图片或其派生图**（编辑合成图必须先记录来源，见五节踩坑）。
> - **新会话阅读顺序**：本文件（现状/数据/结果）→ `List_of_Experiments.md`（要做什么）→ `COMMANDS.md`（怎么跑）→ `paper\PAPER_PLAN.md`（论文口径与投稿）。

> **已确认（2026-09-19，用户）**：① 新 test 61 张标签**已人工逐张复核**；② B 臂只要求**总量与 C 臂一致（868 张）**，不按"单图有无标签"配正负比——**标注单位是框**，一张图上可同时有违规气瓶与规范气瓶（混合样本）；③ `paper\reference\` 已加入 `.gitignore`（不入库）；④ 同意补新 test 的 imgsz 扫描（见 `List_of_Experiments.md` 第二节）。

> 截止（2026-09-19）：**项目正式进入 v3**——test 换成网络来源的 61 张独立图（`new_test_set\`）；**real93 全量作真实臂**（不再划 60/33）；**gen1085 保留为生成（编辑合成）臂**；v1/v2 产物已归档 `_trash\`。首个 v3 数字：gen1085/yolo26s 在新 test 上 **P 0.927 / R 0.889 / mAP50 0.927 / mAP50-95 0.698**（干净口径）。下一步：三臂对照（真实 93 / 真实+传统增广 868 / 编辑合成 868）成套开跑，见 `List_of_Experiments.md`。

## 一、项目与目标

- **一句话**：工地危险样本（违规场景照片）真实稀缺、摆拍有安全与伦理问题 → 用 **Qwen-Image-Edit 编辑真实巡检照片**合成稀缺的"违规状态"样本（真实性红线）→ 训练多目标检测器。第一步 = 气瓶「放置问题」，第二步 = 不带安全帽的工人。
- **检测目标**：Placement Issues——气瓶**未放置在专用固定架或手推车上**即为目标（监理口径：统一归入「放置问题·未固定」，含倒地）。
- **正/负样本（标注单位是「框」，不是整图）**：框 = 一处违规（未固定/倒地）的气瓶；规范放置的气瓶不标。**一张图可以同时含违规框与规范气瓶（混合样本）**；"有框图 / 空标图"只是统计口径，不代表整图性质。
- **生成质量红线**：必须带喷漆磨损、污渍、锈迹（真实照片里没有干净气瓶；防「过净」域差导致真实场景漏检）。
- **合成工具链（2026-09-18 更正）**：**Qwen-Image-Edit-2509 图生图编辑**（两批生成图全部由此产生：`LoadImage(真实照片) → TextEncodeQwenImageEditPlus → KSampler`）；文生图（z-image-turbo）为早期试验，当前不是主力。canny ControlNet 为试验项。
- **分工**：编辑合成图**只源自 real93**；test 用外部独立图源（见 2.3），杜绝"测试照片被编辑进训练集"。
- **工作流与人工环节**：`生成（用户人工，ComfyUI + Qwen-Image-Edit，本仓库不跑）→ 来源审计（scripts\audit_gen_sources.py）→ 自动预打标（autolabel.py / 一键 bat）→ 人工逐张复核（annotator GUI）→ 训练 → 评测`。**新批次生成图由用户交付到 `D:\gas_cylinders\`**；agent 负责审计、打标、复核支持、训练与评测，不负责生成本身。

## 二、数据现状（`D:\gas_cylinders\`，工作区外）

### 2.1 真实照片 93 张（real 臂训练集）
- `real_photo\93_real_photos\`：57 张有框（共 179 框）+ 36 张空标；单类 `0: Placement Issues`。
- 来源：用户方监理提供的安全巡检记录。
- v3 用途：**全部 93 张作真实臂训练集**（v1/v2 的 75/18、60/33 划分已弃用，清单留在 `v1_split\`、`v2_split\` 作历史）。

### 2.2 编辑合成图 1085 张（生成臂）
- 两批：`Placement_Issues\`（493 张 = 380 张有框/1062 框 + 113 张空标）、`Placement_Issues_2\`（592 张 = 414 张有框/1129 框 + 178 张空标）；合计 **794 张有框（2191 框）+ 291 张空标**。
- **来源（2026-09-18 审计）**：全部是 93 张真实照片的 Qwen-Image-Edit 编辑版，编辑源覆盖 93/93 张；逐图来源见 `gen_sources.json`，审计/过滤工具 `scripts\audit_gen_sources.py`。
- 划分（seed=42 分层 80/20，`gen1085_split\`）：**train 868（635 张有框/1768 框 + 233 张空标）/ val 217**；test key 已指向 v3 test（见 2.3）。
- 训练产物：`runs\detect\gen1085\`（六权重，COCO 预训练、100 轮、报 last.pt）；`runs\detect\gen493\`（第一批 394 张的旧点，可复用作规模曲线第一点）。

### 2.3 新 test 集 61 张（v3 唯一评测口径）
- `new_test_set\`：**61 张网络来源图**（与 real93 及所有训练数据完全无关）= **30 张有框（72 框）+ 31 张空标**；**全部与气瓶有关**（规范放置的不标，不规范的标框）。
- 配置：`v3\test61.txt`（绝对路径清单）+ `v3\data_test61.yaml`（train=val=test，供独立评测）。
- 特点：分辨率明显小于训练图（小至 194×259），域差与"小图"效应需在评估与讨论中说明。
- **独立性已实测**（2026-09-19）：与 93 张真实照片、800 张抽样生成图做缩略图相关性检查，最高仅 0.73（"同场景"通常在 0.95 以上；93 张真实照片内部最高 0.83）→ test 与训练数据无近似重复。

### 2.4 其它素材
- `Hardhat\`：2 张真实图，第二目标「不带安全帽的工人」素材。

### 2.5 v3 配置目录
- `v3\`：`test61.txt`、`real93_train.txt`（93 张绝对路径）、`data_test61.yaml`、`data_real93.yaml`。
- `gen1085_split\data.yaml`：生成臂 yaml（train/val 868/217，test → v3 test）。

## 三、结果与结论（v3）

**设置**：六权重统一超参（epochs=100 / imgsz=640 / batch=16 / device=0），**固定轮数、报 last.pt、不做验证集选权**；test = new_test_set 61 张（72 框）；各臂只差训练数据来源。

**主结果（新 test，六权重全表；数字源 `phase10_v3_main.json`）**：

| 权重 | C 编辑合成 train 868 | gen493 train 394（规模曲线第一点） | 差值（868−394） |
|---|---|---|---|
| yolov8s | 0.850 / 0.648 | 0.786 / 0.537 | **+0.111** |
| yolov8m | 0.837 / 0.630 | 0.679 / 0.484 | **+0.146** |
| yolo11s | 0.805 / 0.601 | 0.748 / 0.530 | **+0.071** |
| yolo11m | 0.768 / 0.555 | 0.658 / 0.450 | **+0.105** |
| **yolo26s** | **0.927 / 0.698** | 0.795 / 0.557 | **+0.141** |
| yolo26m | 0.876 / 0.661 | 0.717 / 0.510 | **+0.151** |

- **规模效应成立（干净口径）**：合成数据 394 → 868 张，六权重 mAP50-95 全涨（+0.07~+0.15），且是在与训练数据完全独立的 test 上取得 ——「扩量有效」在 v3 有了扎实证据；最优权重 yolo26s（0.927 / 0.698）。
- A 臂（real93 全量 93 张）与 B 臂（93 × N → 868 增广）待训，三臂对比完成后成主表。
- 沿革见下；v1/v2 的 run 与 summary 已归档 `_trash\`。
- **沿革（v1/v2 一句话，仅备查）**：v1 建立 93 张真实 + 493 张生成图与六权重评测闭环；v2 补第二批到 1085 张、真实集重划 60/33、全篇改 last.pt 协议；v2 期间审计发现**生成图全部是真实照片的编辑版**、且当时 test33 的 33 张全被用作编辑源（611/1085 张受影响）→ 生成臂结果作废、test 必须换 → 这直接促成 v3。v1/v2 的全部 run 目录、summary JSON 与日志已归档 `_trash\`（`runs\`/`summaries\`/`logs\`/`scripts\`）。

## 四、路线图（v3）

1. ✅ 换 test：61 张独立网络图 + v3 配置落地（2026-09-19）。
2. **三臂对照成套**：A 真实 93 / B 真实+传统增广 868 / C 编辑合成 868，六权重 × 统一协议 → 主结果表。
3. 规模曲线：gen493（394）vs gen1085（868）在新 test 上复评（C 臂内部），可选再扩生成到 1500+。
4. 方法学补充：复核价值消融、负样本消融、多随机种子、工作点 PR、误差分析图（见 `List_of_Experiments.md`）。
5. 多目标扩展：安全帽（第二目标）。
6. 论文：按 v3 口径改写 Methodology（编辑合成 = 状态级增广）与 Experiments；投稿策略见 `paper\PAPER_PLAN.md`。

## 五、资产与踩坑

- **环境**：`D:\yolo\.venv`（Py 3.13 / torch 2.8.0+cu129 / ultralytics 8.4.135）；GPU RTX 5070 Ti Laptop 11.9 GB；预训练权重 `weights\`（v8/11/26 × s/m）。
- **代码**（`scripts\`）：`autolabel.py` + `prepare_labeling_workspace.bat`（打标，默认模型见下）、`splits_gen1085\`（生成臂划分）、`run_phase8_gen1085.ps1`（生成臂训练）、`eval_gen1085.py`（评测）、`audit_gen_sources.py`（来源审计）。
- **打标模型（生产件）**：`runs\detect\gen1085\yolo26s\weights\last.pt`（在 119 张未见过的生成图上门 mAP50-95 0.932）；`autolabel.py` 与一键 bat 默认已指向它。
- **run 目录**（`runs\detect\`）：`gen1085\`（生成臂六权重）、`gen493\`（规模曲线旧点）。
- **沙箱**：训练/评测/autolabel 需 danger-full-access；跨盘写（`D:\gas_cylinders`）也要升级。
- **踩坑（含 v1/v2 教训，v3 继续适用）**：
  1. **合成图必须能追溯来源**：v2 的 611 张泄漏就是"没记来源 + test 被当编辑源"造成的；新批次生成后先跑 `make_gen_clean.py` 类审计。
  2. 固定轮数协议必须 `patience=0` 关早停（小数据臂可能被 self-val fitness 误截断，实测 yolo11m 300 轮曾在第 105 轮被截）。
  3. `data.yaml` 的 `path` 与清单行必须绝对路径（`path: .` 会解析到进程 CWD；相对清单行找不到标签）。
  4. 独立 python 脚本跑 ultralytics 必须 `__main__` 守卫 + `workers=0`（Windows spawn）。
  5. train=val 全量重训的自评指标虚高，仅作 sanity check。
  6. `.gitignore` 不支持行内注释。打标工作区根 `data.yaml`（`path: .` / `train: images`）**仅**供 annotator GUI 使用，勿用于训练。

## 六、文件地图

| 路径 | 内容 |
|---|---|
| `PROGRESS.md` | **本文件**：唯一进度台账 |
| `COMMANDS.md` | 命令表（AI agent 用） |
| `List_of_Experiments.md` | 待做实验一页清单（v3） |
| `Prompt.md` | 用户 prompt（私有，不入库） |
| `scripts\` | 全部代码（见五节） |
| `annotator\` | 标注 GUI（`start_annotator.bat` / `stop_server.bat`） |
| `runs\detect\` | `gen1085\`（生成臂六权重）、`gen493\`（规模曲线旧点）、`v3\`（v3 评测输出）、`v3_check\`（体检） |
| `phase10_v3_main.json` | **v3 结果汇总（权威数字）**：各臂 × 六权重 × 新 test |
| `weights\` | 预训练源权重（v8/11/26 × s/m） |
| `paper\` | 论文工作区（PAPER_PLAN / working_paper.tex / references.bib / reference\ 文献库） |
| `_trash\` | **弃用归档区**（v1/v2 的 runs/summaries/logs/scripts/data），勿真删 |
| `D:\gas_cylinders\new_test_set\` | **v3 test（61 张网络图）** |
| `D:\gas_cylinders\v3\` | v3 配置（test61 / real93_train / 各臂 yaml） |
| `D:\gas_cylinders\gen1085_split\` | 生成臂划分（train 868 / val 217） |
| `D:\gas_cylinders\real_photo\93_real_photos\` | 93 张真实照片（real 臂 + 编辑源） |
| `D:\gas_cylinders\Placement_Issues[_2]\` | 两批编辑合成图（493 + 592） |
| `D:\gas_cylinders\Hardhat\` | 第二目标素材 |
