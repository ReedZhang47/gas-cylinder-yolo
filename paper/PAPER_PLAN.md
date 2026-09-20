# PAPER_PLAN.md — 论文写作计划（v3，2026-09-19 重写；v1/v2 沿革见 `PROGRESS.md` 三节）

> v3 口径一句话：**test = 61 张独立网络图**（不参与任何训练来源）；三臂同源对照 = real93 全量（93）/ 传统增广（868）/ Qwen-Image-Edit 编辑合成（868）；统一 100 轮、报 last.pt、不做选权。

> 定位：论文投稿的唯一规划文件。写作进展按项目惯例回写 `PROGRESS.md`；实验结果出来后更新本文件第三、四节状态。
> `working_paper.tex`为正文工作文件；投稿模板见第一节第 4 条。

## 一、投稿策略（用户已定打法：先高后低，预期首投被快拒）

1. **首投候选**（预期秒拒，但要拒得快）：
   - **Automation in Construction**（Elsevier，一区 Top，建筑领域 CV 应用标杆）：scope 完全贴合（工地安全监测），预期拒稿理由是新颖性/规模而非 scope——这个信号本身有价值。Elsevier 桌拒通常 1~3 周，且常附姊妹刊 transfer 选项。
   - 备选：Computer-Aided Civil and Infrastructure Engineering（Wiley，一区 Top）。
2. **落点候选**（二区开源 OA）：
   - **Sensors**（MDPI）：快（首决数周）、模板化、工程 CV 常见落点；
   - **Buildings**（MDPI）：建筑工程 scope 最贴合；
   - **Scientific Reports**（Nature Portfolio，综合二区）：接受面广；
   - IEEE Access（审稿快、OA 费中等；⚠️ 近年分区波动大且曾入预警名单争议，投前核实当前分区与口碑）。
   - ⚠️ 投前必做：核对**最新中科院分区表**（分区逐年变动，以上为写作时认知）+ **国际期刊预警名单** + 官网 "submission to first decision" 中位周期；确认 APC（约 2000~3000 CHF/USD 级）预算。
3. 无论落点在哪，投稿前挂 **arXiv 预印本**占位（Elsevier / Nature 系均允许；操作清单见第七节）。
4. 模板：首投用 Elsevier `elsarticle` 或直接 "Your Paper Your Way" 自由格式投稿即可；转投 MDPI 时再换官方模板（结构不变，搬运即可）。

## 二、篇章结构与篇幅

**通用 IMRaD 骨架（本论文定制版，英文标题已定）：**

1. **Introduction**——工地危险样本稀缺是趋势性问题、摆拍有安全与伦理问题、**编辑合成（state-level augmentation）**是出路；结尾放显式 contributions 列表（C1 编辑合成 + 预打标 + 人工复核的闭环管线；C2 **与源数据完全无关的独立 test + 可复现的独立性检验**（缩略图相关性）；C3 与经典增广的**同源对照** + 规模效应的实证；C4（第二目标完成后）跨目标通用性）。
2. **Related Work**——2.1 CV for construction safety（气瓶/PPE/安全帽检测）；2.2 synthetic & generative data for object detection（GAN/diffusion 扩增、sim2real、copy-paste）；2.3 auto-labeling 与 human-in-the-loop。
3. **Methodology**——3.1 问题与类别定义（监理口径：放置问题=未固定，含倒地）；3.2 真实种子数据（93 张人工标注；标注单位是框、图上可混合）；3.3 **编辑合成管线**（Qwen-Image-Edit-2509 图生图编辑真实巡检照片，合成"违规状态"；真实性红线：脏污/磨损，防"过净"域差；逐图来源记录，属数据管理）；3.4 自动预打标 + 人工复核闭环（labeler 模型 + annotator GUI）；3.5 评测协议（**独立 test = 61 张网络图**，与 93 张巡检照片及由其编辑出的全部生成图无来源/场景重叠，独立性由缩略图相关性检验复现；固定 100 轮 / imgsz 640 / batch 16、报 last.pt、不做选权；六权重统一超参）。
4. **Experiments**——4.1 setup（6 权重 × 统一超参、硬件）；4.2 **主结果：三臂同源对照**（A 真实 93 / B 真实+传统增广 868 / C 编辑合成 868，全体只在数据来源上不同）在新 test 上；4.3 **数据规模消融**（394 vs 868，✅ 已完成：六权重 mAP50-95 全涨 +0.07~+0.15）；4.4 推理分辨率分析（新 test 图分辨率远小于训练图，imgsz 扫描）；4.5 **跨目标扩展（安全帽）**【待实验】；4.6 消融与稳健性（复核价值 / 空标图 / 多种子 / 工作点 PR，见 `List_of_Experiments.md`）。
5. **Discussion**——domain gap 的两个来源（过净 + 小目标分辨率）；合成数据伦理与 AI 披露（生成图是方法组件，按各刊政策写明工具与模型并引用官方论文）；向其它行业稀缺目标推广。
6. **Conclusion**（最后写）。

**篇幅（按落点）：**

| 落点 | 正文 | 图/表 | 参考文献 |
|---|---|---|---|
| Automation in Construction（首投） | 8000~10000 词 | 图 8~12、表 4~6 | 60~90 条 |
| Sensors / Buildings（MDPI 落点） | 5000~7000 词 | 图 6~10、表 3~5 | 40~60 条 |
| Scientific Reports | 正文约 4000~5000 词 + Methods 独立后置节 | 同上偏少 | 40~60 条 |

**图表素材清单**（可先攒）：图 1 管线总图（必画，Methodology 骨架；草稿见 `fig1_pipeline.md`）；编辑合成样本拼图（展示脏污真实感 + 与源照片对照）；**三臂结果表（六权重 × 新 test，A/B/C 三列）**；**规模曲线（394 vs 868）**；imgsz 扫描曲线；新 test 检出示例（TP/FP/FN）；【待】安全帽样本与结果。

## 三、写作状态：现在能写 vs 等实验

| 部分 | 状态 | 依据/素材 |
|---|---|---|
| Related Work（全部） | ✅ 可写，需先文献调研 | 检索词：construction site safety detection；synthetic data for object detection；diffusion data augmentation；sim2real；auto-labeling human-in-the-loop |
| Methodology（3.1~3.5 全部） | ✅ 可写（v3 口径） | `PROGRESS.md` 一/二 + `COMMANDS.md` |
| Experiments 4.1 / 4.2 主结果 | ⛔ 等 A/B 两臂（C 臂六权重 + 新 test 数字已出） | `phase10_v3_main.json` + `PROGRESS.md` 三 |
| Experiments 4.3 规模消融 | 半（394 vs 868 完成、六权重全涨；协议脚注见第四节 2，待按 v3 重跑 gen493） | `phase10_v3_main.json` |
| Experiments 4.4 分辨率分析 | 半（新 test imgsz 扫描待补） | imgsz 扫描命令见 `COMMANDS.md` |
| Introduction | ✅ 初稿（C3 留占位，等 A/B 臂） | 项目"一句话+主故事线" |
| Discussion | ✅ 初稿 | 编辑合成 vs 传统增广的机制 + 新 test 域差（小图） |
| Experiments 4.5 第二目标 | ⛔ 等实验 | 跨目标证据，三级定位第 2 级的门槛（见第五节） |
| Experiments 4.6 消融与稳健性 | 🔄 清单已列，逐项开跑 | `List_of_Experiments.md` 第二节 |
| Experiments 4.7 传统增广对照 | ⛔ 等 B 臂 | 与 4.2 主对照同源，写作时可合并叙述 |
| Conclusion | 最后写 | — |

## 四、投稿前必须补的实验（按优先级）

> 完整清单（含每项的可开始状态、建议新增实验、共享 GPU 窗口的排期）见仓库根 `List_of_Experiments.md`（2026-09-17 立）；本节只保留设计要点。

1. **三臂同源对照（主实验）**——回答"为什么用编辑合成，而不是免费的传统增广"。三臂都以 real93 为唯一数据来源，只差"怎么扩"：

   | 臂 | 训练数据 | 状态 |
   |---|---|---|
   | A 真实基线 | real93 全量 **93 张** | 待训（`v3\data_real93.yaml`） |
   | B 真实+传统增广 | 93 → **868 张**（总量与 C 臂一致即可） | 待做（增广脚本待写） |
   | C 编辑合成 | gen1085 train **868 张** | ✅ 六权重已在新 test 复评（mAP50 0.768~0.927 / mAP50-95 0.555~0.698） |

   - 协议：100 epoch / imgsz 640 / batch 16，`patience=0`，报 last.pt；三臂均带 ultralytics 默认在线增强（B 臂的离线增广是"额外补量"）。
   - 增广类型：hflip、±10° 旋转、缩放平移、亮度/对比度/HSV；**不用上下翻转**（工地实景有重力方向）；几何变换同步变框。
   - **B 臂对齐口径**：只要求**总量与 C 臂一致（868 张）**，**不按"单图有无标签"配正负比**——标注单位是框，一张图上可同时有违规气瓶与规范气瓶（混合样本），按图配比没有意义。
   - **解读预案**：C > B > A → 同量级下编辑合成优于传统增广；B ≈ C → 口径改为"传统增广能补量、补不了状态多样性"；B 明显低于 C → 最常见、故事最顺。
   - 机制句（写进论文）：传统增广不产生**新的违规状态**（未固定/倒地等状态语义），编辑合成产生——这是两者本质差异，也是 B 臂的天花板。
   - 统计：test 61 张/72 框仍偏小，对比结论附 bootstrap 置信区间或逐图 AP 离散度；必要时给 s 家族补随机种子。

2. **数据规模消融**【✅ 已完成 2026-09-20】——gen493（train 394）vs gen1085（train 868）在独立新 test 上：六权重 mAP50-95 **全涨 +0.07~+0.15**（yolo26s 0.557→0.698）。gen493 已按 v3 协议重跑，**两点同协议**（重跑与旧点等价：test 指标逐位相同、PR 曲线逐点最大差 0）。
3. **消融与稳健性**（见 `List_of_Experiments.md` 第二节）：复核价值（autolabel vs 复核标签）、空标图消融、多随机种子、工作点 PR、**分辨率敏感性**（新 test 分辨率跨度极大：192×137~2160×2880、中位 509×516、34/61 张两边都 <640，已确认要补）、误差分析图。
4. **安全帽第二目标**（`Hardhat\` 素材已起步）——跨目标证据，支撑方法通用性；样本到手后的实验（含跨目标迁移、双目标统一模型）见清单第三节。

## 五、立论口径（红线）

- 主张 **methodology + empirical evidence**，不主张"合成数据优于真实"；"扩量有效/数量取胜"必须先有第四节 1/2 的实验支撑才可写进 contributions。
- **诚实口径**：编辑合成图的多样性上界 = 源照片数量（93 张），补的是**状态多样性**而非场景多样性；论文里要同时报"源照片数 + 变体数"，不能只报总张数。
- **独立性主张走"外部 test + 可复现检验"**：合成数据的编辑源就是真实种子照片，所以**不能**拿同源真实照片当 test；v3 用与源数据无关的外部 test（61 张网络图），并用缩略图相关性把它变成一次可跑的检查（`scripts\check_test_independence.py`）。
- **三级定位**：
  1. **Application paper**（单目标，第四节 1~3 完成即可成文首投）；
  2. **Method paper**（加安全帽跨目标证据 → "可推广到其它稀缺目标的编辑合成管线"，素材全复用）；
  3. **通用数据增广协议**（升格为正式贡献需要**第二个非工地域**的证据；当前只作 Discussion 愿景与 future work，避免 overclaim）。
- 建议路径：首投版按 Application 写；等首投结果期间跑消融与稳健性；转投升级视第二目标完成度决定。
- 通用性主张靠"跨行业数据稀缺"的动机论述（Introduction/Discussion）+ 跨目标证据（4.5）两头支撑。
- 合成数据按各刊 **AI 使用披露政策**写明生成工具/模型/版本并引用官方论文（Qwen-Image-Edit-2509；授权已确认，仅需引用论文/模型卡）。

## 六、工作流

- 英文初稿直接写在 `working_paper.tex`；中文素材（PROGRESS/COMMANDS）可喂给 LLM 起草再人工重写。
- 参考文献：`paper/references.bib`（44 条，已逐条核验）；加新文献时可用 `paper/fetch_refs.py` 半自动抓取（Crossref/DataCite），但**必须人工复核**（重跑会覆盖已校对内容）。
