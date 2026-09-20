# PROGRESS.md — 工地危险样本扩充项目（v3）

> ## 约定
> - 需求 prompt 写入 `D:\yolo\Prompt.md`（仅用户可编辑，AI 只读）。
> - 本文件是**唯一进度台账**：每轮工作完成并验证后立即更新（结果数字、产物路径、下一步、新坑）；改前先读当前版本，改完刷新文首「截止」行。
> - 命令/路径变化同步 `COMMANDS.md`；全文禁止引用不存在的文件。
> - 弃用文件一律移入 `_trash\`（勿真删）。

> 截止（2026-09-20，v3 文档收口 + 一处数字更正）：
> - **v3 结果主体已出**——C 臂（gen1085 train 868）六权重在新 test 上完成复评 + 规模曲线（gen493 394 张）复评，数字见 `phase10_v3_main.json`。
> - **A/B 两臂仍未出**：A 臂 2026-09-19 00:12 误启动，已中断（日志已归档 `_trash\logs\` 的 v3_real93_*.log）；B 臂增广脚本 `make_aug93_dataset.py` 尚未写。三臂对照成套前，main 表停留在 C 臂单臂。
> - B 臂只要求**总量与 C 臂一致（868 张）**，不按"单图有无标签"配正负比——**标注单位是框**，一张图上可同时有违规气瓶与规范气瓶（混合样本）。
> - **本次文档修订要点**：① 独立性主张改以**缩略图相关性实测**为唯一证据（脚本 `scripts\check_test_independence.py`，本次复跑数字与 2026-09-19 一致）；② 清掉 v2 末期废案（ComfyUI 来源审计 / 611 张 / gen_clean 洗池）在方法与论文文档中的一切"方法学贡献"表述，该废案沿革见第三节末；③ 主结果表的脚注补上 gen493 的协议差异。

## 一、项目与目标

- **一句话**：工地危险样本（违规场景照片）真实稀缺、摆拍有安全与伦理问题 → 用 **Qwen-Image-Edit 编辑真实巡检照片**合成稀缺的"违规状态"样本（真实性红线）→ 训练多目标检测器。第一步 = 气瓶「放置问题」，第二步 = 不带安全帽的工人。
- **检测目标**：Placement Issues——气瓶**未放置在专用固定架或手推车上**即为目标（监理口径：统一归入「放置问题·未固定」，含倒地）。
- **正/负样本（标注单位是「框」，不是整图）**：框 = 一处违规（未固定/倒地）的气瓶；规范放置的气瓶不标。**一张图可以同时含违规框与规范气瓶（混合样本）**；"有框图 / 空标图"只是统计口径，不代表整图性质。
- **生成质量红线**：必须带喷漆磨损、污渍、锈迹（真实照片里没有干净气瓶；防「过净」域差导致真实场景漏检）。
- **合成工具链**：**Qwen-Image-Edit-2509 图生图编辑**（目前两批生成图全部由此产生：`LoadImage(真实照片) → TextEncodeQwenImageEditPlus → KSampler`）；文生图（z-image-turbo）为早期试验，当前不是主力。canny ControlNet 为试验项。
- **分工**：编辑合成图**只源自 real93**；test 用外部独立图源（见 2.3），杜绝"测试照片被编辑进训练集"。
- **工作流与人工环节**：`生成（用户人工，ComfyUI + Qwen-Image-Edit，本仓库不跑）→  自动预打标（autolabel.py / 一键 bat）→ 人工逐张复核（annotator GUI）→ 训练 → 评测`。**新批次生成图由用户交付到 `D:\gas_cylinders\`**；agent 负责审计、打标、复核支持、训练与评测，不负责生成本身。

## 二、数据现状（`D:\gas_cylinders\`，工作区外）

### 2.1 真实照片 93 张（real 臂训练集）
- `real_photo\93_real_photos\`：57 张有框（共 179 框）+ 36 张空标；单类 `0: Placement Issues`。
- 来源：用户方监理提供的安全巡检记录。
- v3 用途：**全部 93 张作真实臂训练集**（v1/v2 时用途不同，已弃用）。

### 2.2 编辑合成图 1085 张（生成臂）
- 两批：`Placement_Issues\`（493 张 = 380 张有框/1062 框 + 113 张空标）、`Placement_Issues_2\`（592 张 = 414 张有框/1129 框 + 178 张空标）；合计 **794 张有框（2191 框）+ 291 张空标**。
- 来源：全部是 93 张真实照片的 Qwen-Image-Edit 编辑版，编辑源覆盖 93/93 张。
- 划分（seed=42 分层 80/20，`gen1085_split\`）：**train 868（635 张有框/1768 框 + 233 张空标）/ val 217**；test key 已指向 v3 test（见 2.3）。
- 训练产物：`runs\detect\gen1085\`（六权重，COCO 预训练、100 轮、报 last.pt）；`runs\detect\gen493\`（第一批 394 张的旧点，可复用作规模曲线第一点）。

### 2.3 新 test 集 61 张（v3 唯一评测口径）
- `new_test_set\`：**61 张网络来源图**（与 93 张巡检照片及其全部编辑产物无来源/场景重叠，见下）= **30 张有框（72 框）+ 31 张空标**；**全部与气瓶有关**（规范放置的不标，不规范的标框）。
- 配置：`v3\test61.txt`（绝对路径清单）+ `v3\data_test61.yaml`（train=val=test，供独立评测）。
- 特点：分辨率跨度大（**192×137 ~ 2160×2880，中位 509×516；34/61 张两边都 <640**），与训练图差异需在 4.4 分辨率分析里讨论。
- **独立性证据（唯一口径，2026-09-19 实测 / 2026-09-20 复跑一致）**：缩略图（48×48 灰度、去均值归一化、余弦相似度）相关性——test↔real93 **最大 0.730**、test↔生成图 800 张抽样 **最大 0.732**，均 **0 对 >0.90**；对照组 real93 内部最大 0.834（"同场景"通常 ≥0.95）。最相似一对：`new_test_set_0059.jpg ~ real_photo_19.png`（0.730）。复现命令见 `COMMANDS.md`，脚本 `scripts\check_test_independence.py`。
- **为什么这比"来源审计"更硬**：新 test 是网络来源，与 93 张巡检照片**及由它们编辑出的 1085 张生成图**都无来源、无场景重叠；缩略图相关性是直接测"像不像"，而非间接推"源不同"。

### 2.4 其它素材
- `Hardhat\`：2 张真实图，第二目标「不带安全帽的工人」起步素材。

### 2.5 配置目录
- `v3\`：`test61.txt`、`real93_train.txt`（93 张绝对路径）、`data_test61.yaml`、`data_real93.yaml`。
- `gen1085_split\data.yaml`：生成臂 yaml（train/val 868/217，test → v3 test）。
- **遗留（v1/v2 口径，勿用于 v3）**：`real_photo\93_real_photos\` 下的 `v1_split\`（`all.txt`/train/val）、`v2_split\`（`train60.txt`/`test33.txt`）与根 `data.yaml`。其中 `v1_split\all.txt` 仍是 `make_v3_configs.py` 生成 real93 清单的**输入**，故保留；其余仅备查。

### 2.6 数据侧存档（不进论文叙事）
- `D:\gas_cylinders\gen_sources.json`：1085 张生成图的**逐图来源记录**（ComfyUI 元数据里的 LoadImage 源照片名），`test_set` 字段已于 v3 更新为 `test61.txt`（`derived_from_test: 0`）。它是 v2 末期废案的产物（见三节末），**仅作数据管理存档**：查"某张生成图从哪来"用，不构成 v3 的独立性论证。

## 三、结果与结论（v3）

**设置**：六权重统一超参（epochs=100 / imgsz=640 / batch=16 / device=0），**固定轮数、报 last.pt、不做验证集选权**；test = new_test_set 61 张（72 框）；各臂只差训练数据来源。

**主结果（新 test，六权重全表；数字源 `phase10_v3_main.json`）**：

| 权重 | C 编辑合成 gen 1085 train 868 | gen493 train 394（规模曲线第一点） | 差值（868−394） |
|---|---|---|---|
| yolov8s | 0.850 / 0.648 | 0.786 / 0.537 | **+0.111** |
| yolov8m | 0.837 / 0.630 | 0.679 / 0.484 | **+0.146** |
| yolo11s | 0.805 / 0.601 | 0.748 / 0.530 | **+0.071** |
| yolo11m | 0.768 / 0.555 | 0.658 / 0.450 | **+0.105** |
| **yolo26s** | **0.927 / 0.698** | 0.795 / 0.557 | **+0.141** |
| yolo26m | 0.876 / 0.661 | 0.717 / 0.510 | **+0.151** |

- **规模效应成立**：合成数据 394 → 868 张，六权重 mAP50-95 全涨（+0.07~+0.15），且是在与训练数据完全独立的 test 上取得 ——「扩量有效」在 v3 有了扎实证据；最优权重 yolo26s（0.927 / 0.698）。
- ⚠️ **gen493 列的协议脚注**：gen493 六权重是 **v1 时期训练**的（其 `args.yaml` 为 `patience: 100`、`data.yaml` 的 test 仍指 `v1_split\all.txt`），本次只把**评测**统一到 v3（独立 test / imgsz 640 / 报 last.pt）。已核 `results.csv`：六权重**都恰好跑满 100 轮**、早停未触发，故与 gen1085（`patience: 0`）的对比成立；但严格同协议需按 v3 重跑 gen493（待办，见 `List_of_Experiments.md`）。
- A 臂（real93 全量 93 张）与 B 臂（93 × N → 868 增广）待训，三臂对比完成后成主表。
- 沿革见下；v1/v2 的 run 与 summary 已归档 `_trash\`。
- **沿革（v1/v2 一句话，仅备查）**：v1 建立 93 张真实 + 493 张生成图与六权重评测闭环，test 为 93 张真实；v2 补第二批生成到 1085 张、真实集重划 60/33、全篇改 last.pt 协议，real60 和 gen1085 都在 real33 上做 test；v2 期间意识到**生成图全部是真实照片的编辑版**、test33 的 33 张全被用作编辑源 → 属于泄露，test 必须换 → 促成 v3。v1/v2 的全部 run 目录、summary JSON 与日志已归档 `_trash\`，不再使用。
- **v2 末期废案（已整体废弃，勿再引用）**：换 test 之前曾有一版补救方案——用 ComfyUI 元数据做**来源审计**，查出 1085 张里 **611 张**的编辑源命中 v2 test33（`_trash\data\gen_clean\manifest.json` 的 `counts.dropped`），再据此"洗"出干净池 gen_clean（474 张）与来源池 gen_source_pool；对应脚本 `_trash\scripts\audit_gen_sources.py`、`_trash\scripts\splits_gen_clean\`。该方案**已被 v3 整体取代**：直接换成与 93 张巡检照片（及其全部编辑产物）无关的网络 test，既保住了 gen1085 全量资产，也比 60/33 更独立；同时 real93 得以全量用于训练（A/B 臂由 60 张改为 **93 张**）。**这套审计/洗池路线不再作为方法学贡献，也别再写进论文**；611 这个数字只在本文档与 `_trash` 存档中备查。

## 四、路线图（v3）

1. ✅ 换 test：61 张独立网络图片 + v3 配置落地。
2. **三臂对照成套**：A 真实 93 / B 真实+传统增广 868 / C 编辑合成 868，六权重 × 统一协议 → 主结果表。
3. 规模曲线：gen493（394）vs gen1085（868）在新 test 上复评（C 臂内部）已完成；**待办：把 gen493 六权重按 v3 协议（patience=0 + v3 test 配置）重跑一遍**，让曲线两点完全同协议（现 gen493 为 v1 时期训练，见三节脚注）；之后可选再扩生成到 1500+，或补一个 gen250（200）节点。
4. 方法学补充：复核价值消融、负样本消融、多随机种子、工作点 PR、误差分析图（见 `List_of_Experiments.md`）。
5. 多目标扩展：安全帽（第二目标）。
6. 论文：按 v3 口径改写 Methodology（编辑合成 = 状态级增广）与 Experiments；投稿策略见 `paper\PAPER_PLAN.md`。

## 五、资产与踩坑

- **环境**：`D:\yolo\.venv`（Py 3.13 / torch 2.8.0+cu129 / ultralytics 8.4.135）；GPU RTX 5070 Ti Laptop 11.9 GB；预训练权重 `weights\`（v8/11/26 × s/m）。
- **代码**（`scripts\`）：`autolabel.py` + `prepare_labeling_workspace.bat`（打标，默认模型见下）、`splits_gen1085\`（生成臂划分）、`run_phase8_gen1085.ps1`（生成臂训练）、`make_v3_configs.py`（v3 配置）、`eval_v3.py`（**现役** v3 成套评测）、`eval_gen1085.py`（v2 遗留，与 eval_v3 重叠，仅备查）、`check_test_independence.py`（test 独立性检验）、`run_v3_arms.ps1`（A/B 两臂训练）。
- **打标模型（生产件）**：`runs\detect\gen1085\yolo26s\weights\last.pt`（2026-09-18 选定：在 119 张未见过的生成图上的自评 mAP50-95 0.932 / P 0.970 / R 0.958，随 `autolabel.py` 一并交付；属工具件指标，不进论文结果表）；`autolabel.py` 与一键 bat 默认已指向它。
- **run 目录**（`runs\detect\`）：`gen1085\`（生成臂六权重）、`gen493\`（规模曲线第一点）、`v3\`（v3 评测输出）、`v3_check\`（体检）。
- **沙箱**：训练/评测/autolabel 需 danger-full-access；跨盘写（`D:\gas_cylinders`）也要升级。
- **踩坑（含 v1/v2 教训，v3 继续适用）**：
  1. 固定轮数协议必须 `patience=0` 关早停（小数据臂可能被 self-val fitness 误截断）。
  2. `data.yaml` 的 `path` 与清单行必须绝对路径（`path: .` 会解析到进程 CWD；相对清单行找不到标签）。
  3. 独立 python 脚本跑 ultralytics 必须 `__main__` 守卫 + `workers=0`（Windows spawn）。
  4. `.gitignore` 不支持行内注释。打标工作区根 `data.yaml`（`path: .` / `train: images`）仅供 annotator GUI 使用，勿用于训练。
  5. **A 臂训练曾于 2026-09-19 00:12 启动并被中断**（误启动）：yolov8s 跑到第 62 轮被终止、`real93v3\` 未落盘，日志已归档 `_trash\logs\v3_real93_*.log`；下一步工作从这里开始（重跑前确认该 run 目录不存在）。
  6. **测试集独立性只有"缩略图相关性"一条证据链**（`check_test_independence.py`，脚本零新依赖、跑一次约 30 s）：改动 test 集后必须重跑并把数字写回二.3，否则论文里的独立性声明没有依据。

## 六、文件地图

| 路径 | 内容 |
|---|---|
| `PROGRESS.md` | **本文件**：唯一进度台账 |
| `COMMANDS.md` | 命令表（AI agent 用） |
| `List_of_Experiments.md` | 待做实验一页清单（v3） |
| `Prompt.md` | 用户 prompt（私有，不入库） |
| `scripts\` | 全部代码（见五节） |
| `scripts\check_test_independence.py` | **test 独立性检验**（缩略图相关性，论文独立性主张的复现入口） |
| `scripts\run_v3_arms.ps1` | A/B 两臂六权重训练（v3 协议，可断点续跑） |
| `annotator\` | 标注 GUI（`start_annotator.bat` / `stop_server.bat`） |
| `runs\detect\` | `gen1085\`（生成臂六权重）、`gen493\`（规模曲线第一点）、`v3\`（v3 评测输出）、`v3_check\`（体检） |
| `phase10_v3_main.json` | **v3 结果汇总（权威数字）**：各臂 × 六权重 × 新 test |
| `weights\` | 预训练源权重（v8/11/26 × s/m） |
| `paper\` | 论文工作区（PAPER_PLAN / working_paper.tex / references.bib / reference\ 文献库） |
| `_trash\` | **弃用归档区**，弃用文件移入这里，禁止直接remove |
| `D:\gas_cylinders\new_test_set\` | **v3 test（61 张网络图片）** |
| `D:\gas_cylinders\v3\` | v3 配置（test61 / real93_train / 各臂 yaml） |
| `D:\gas_cylinders\gen1085_split\` | 生成臂划分（train 868 / val 217） |
| `D:\gas_cylinders\real_photo\93_real_photos\` | 93 张真实照片（real 臂 + 编辑源）；`v1_split\`/`v2_split\` 为 v1/v2 遗留，仅 `v1_split\all.txt` 仍被 v3 配置脚本读取 |
| `D:\gas_cylinders\Placement_Issues[_2]\` | 两批编辑合成图（493 + 592）；`Placement_Issues\gen493_split\` 为规模曲线第一点的 394 张划分（v1 建，重跑时沿用） |
| `D:\gas_cylinders\gen_sources.json` | 逐图来源记录（v2 末期废案产物，仅存档，见二.6） |
| `D:\gas_cylinders\Hardhat\` | 第二目标素材 |
