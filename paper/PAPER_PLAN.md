# PAPER_PLAN.md — 论文写作计划（v5）

> 当前口径（2026-09-25）：v4 的 A/B/C 三臂与 493 张规模实验已完成，61 张外部图称 **dev61**，不是 sealed final test。v5 新增 real93 LoRA + Qwen-Image-2.1 文生图 D 臂，目标质检后 1085 张；目前只有 LoRA 与本机少量试生成，D 的 YOLO 结果尚不存在。Fig. 1 已改为四臂设计示意，Fig. 2 已改为 C/D 生成方法示意；正文数字、9 表和其余结果图仍是 v4 三臂版本，不能标为四臂结论。

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

1. **Introduction**——工地危险样本稀缺、摆拍有安全与伦理问题；提出可复核的合成数据与人工复核流程。现有贡献来自 A/B/C 与规模实验；D 臂完成并验证后再决定是否增加“文本生成拓展场景”的贡献，不能在当前摘要中提前声称胜出。
2. **Related Work**——2.1 CV for construction safety（气瓶/PPE/安全帽检测）；2.2 synthetic & generative data for object detection（GAN/diffusion 扩增、sim2real、copy-paste）；2.3 auto-labeling 与 human-in-the-loop。
3. **Methodology**——3.1 问题与类别定义；3.2 真实种子数据；3.3 C 臂编辑合成，以及待完成的 D 臂 LoRA 文生图与生成来源记录；3.4 自动预打标 + 人工复核；3.5 **v4 已定评估协议与 v5 扩展的时间顺序**（dev61 的统计角色；固定终点；分层 5 折交叉拟合；pooled OOF AP；全 dev61 部署选择；detector+checkpoint 联合选择）。
4. **Experiments**——4.1 setup；4.2 **已完成三臂同源对照**；4.3 **493 vs 1085 编辑合成规模实验**；新增 D 臂与 C 臂文生图/编辑合成对照须等完整数据和结果后入正文；之后再写选权稳定性、分辨率、跨目标与稳健性。
5. **Discussion**——固定终点、OOF 估计和部署选择的角色差异；dev61 规模限制与 winner's curse；domain gap；合成数据伦理与 AI 披露；向其它行业稀缺目标推广。
6. **Conclusion**（最后写）。

**篇幅（按落点）：**

| 落点 | 正文 | 图/表 | 参考文献 |
|---|---|---|---|
| Automation in Construction（首投） | 8000~10000 词 | 图 8~12、表 4~6 | 60~90 条 |
| Sensors / Buildings（MDPI 落点） | 5000~7000 词 | 图 6~10、表 3~5 | 40~60 条 |
| Scientific Reports | 正文约 4000~5000 词 + Methods 独立后置节 | 同上偏少 | 40~60 条 |

**图表素材清单（2026-09-25 更新）**：图 1 四臂总流程已重绘为矢量 PDF，D 臂虚线标为待完成；图 2 已重绘为共同数据来源、C 臂编辑和 D 臂 LoRA 文生图流程，D 的正式数据步骤以虚线标示。两图均有 `paper/figures/new fig1/`、`paper/figures/new fig2/` 下的绘图脚本与可编辑 SVG。原 `fig2_arms_samples.pdf` 保留为 v4 样例素材，不再作为正文图 2。图 3 选权、图 4 CI、图 5 定性检出、图 6 规模曲线及 9 张表仍是 v4 三臂版本。D 臂完成后按证据更新样例、主表和配对区间，不把旧结果图直接改题为四臂。

## 三、写作状态：现在能写 vs 等实验

| 部分 | 状态 | 依据/素材 |
|---|---|---|
| Related Work（全部） | ✅ 可写，需先文献调研 | 检索词：construction site safety detection；synthetic data for object detection；diffusion data augmentation；sim2real；auto-labeling human-in-the-loop |
| Methodology（3.1~3.5 全部） | ✅ 可写（v4 协议已定稿） | `EXPERIMENTS.md` + `COMMANDS.md` |
| Experiments 4.1 / 4.2 主结果 | ✅ 已完成 | `experiments/v4_protocol/`（三臂三层结果）+ `bootstrap_paired.json`；C−A +0.211、C−B +0.308 的 CI 不含 0，B−A −0.097 跨 0 |
| Experiments 4.3 规模消融 | ✅ 已完成 | 联合 OOF 0.5019 → 0.6429，Δ +0.1410，CI [+0.060, +0.249]（`bootstrap_paired_L3.json`） |
| Experiments 4.4 选权稳定性 | ✅ 已完成 | 各臂五折选权与部署 epoch：A 五折一致 280；B 200/200/180/200/180；C 260/240/260/260/270；L3 220/200/200/200/260（493 点五折跨 yolo26s/yolo26m，选权不稳） |
| v5 D 臂生成与 YOLO 对照 | ⏳ 准备完成一部分 | LoRA 已训练、ComfyUI 已试生成；1085 张质检/标注、六 detector、三层评估与 D−A/B/C 区间均待完成 |
| Experiments 4.5 分辨率分析 | 待主批次后执行 | `NEXT_STEPS.md` |
| Introduction | ✅ 初稿；C3 占位可补（A/B/C 与规模结果已齐） | 项目"一句话+主故事线" + `PROGRESS.md` v4 阶段性结果 |
| Discussion | ✅ 初稿 | 编辑合成 vs 传统增广的机制 + dev61 域差（小图） |
| Experiments 4.6 第二目标 | ⛔ 等素材 | 跨目标证据，三级定位第 2 级的门槛 |
| Experiments 4.7 消融与稳健性 | 待主批次完成后排序 | `NEXT_STEPS.md` |
| Conclusion | 最后写 | — |

## 四、实验状态与后续材料（按优先级）

> 当前执行顺序见仓库根 `NEXT_STEPS.md`；本节只保留论文所需设计要点。

**v5 当前优先：D 臂。**以 real93 微调的 Qwen-Image-2.1 LoRA 文生图，目标质检后 1085 张。93 条种子图描述各保留 5 张（465），新增场景提示词保留 620；两部分实际生成数量都需高于保留数量。生成工作流、种子、提示词、加速设置、筛选与逐张人工标注记录需要可复核。沿用六 detector 的 300 轮训练与 v4 三层评估、相同 dev61 折定义，报告 D−A、D−B、D−C 的配对聚类 bootstrap。D 臂在 A/B/C 结果已知后提出，因此是 v5 扩展，不能写成 v4 预注册比较；“新场景覆盖”及“优于 C”均须等审计和检测结果支持。

D 臂 LoRA 已按 Qwen-Image 标准流程训练：2000 steps、learning rate 0.0004、rank 16、无裁剪；打标算法为“通义千问”，阈值 0.30。C 臂的 Qwen-Image-Edit-2509 主模型、Qwen 2.5 VL 编码器、VAE 和四步 Lightning LoRA 的精确文件名及 Fig. 2 绘图说明见 `paper/figures/new fig2/README.md`。模式切换与阈值节点须待工作流 JSON 固化，不能把四步采样写成所有 C 图像的统一设置。

Qwen-Image-2.1 于 2026-09-20 开源；官方 Qwen-Image-Bench 对比图可解释选型动机，但“超过 Nano Banana”需要写明具体基准、维度和版本。本项目尚未复测该跨模型结论，论文不把它当作本文实证。

1. **已完成的三臂同源对照（v4 主实验）**——回答"为什么用编辑合成，而不是免费的传统增广"。三臂都以 real93 为唯一数据来源，只差"怎么扩"：

   | 臂 | 训练数据 | 状态 |
   |---|---|---|
   | A 真实基线 | real93 全量 **93 张** | 已完成（联合 OOF mAP50-95 0.4320） |
   | B 真实+传统增广 | 93 → **1085 张** | 已完成（0.3349） |
   | C 编辑合成 | gen1085 全量 **1085 张** | 已完成（0.6429） |

   - **实际结果与解读预案的对齐**：C > B 与 C > A 均成立且 CI 不含 0；但 **B 与 A 无法区分**（主终点 Δ −0.097，CI [−0.197, +0.017]；逐 detector 4/6 跨 0，2/6 反而 B 更好，无一项显著偏向 A）。因此落点不是「C > B > A」，而是「**编辑合成显著优于传统增广，而传统增广相对不扩的 93 张真实图无可检测增益**」——即传统增广能补量、补不了状态多样性，且补量本身在本数据规模上不产生可检出收益。写论文时不要写成「B 比 A 差」。

   - 协议：300 epoch / imgsz 640 / batch 16，`patience=0`，`save_period=10`；报告 fixed endpoint、5 折 pooled OOF 和部署选择。
   - 增广类型：hflip、±10° 旋转、缩放平移、亮度/对比度/HSV；**不用上下翻转**（工地实景有重力方向）；几何变换同步变框。
   - **B 臂对齐口径**：总量与 C 臂一致（1085 张），不按“单图有无标签”配正负比。
   - 机制句（写进论文）：传统增广不产生**新的违规状态**（未固定/倒地等状态语义），编辑合成产生——这是两者本质差异，也是 B 臂的天花板。
   - 统计：dev61 仍偏小；主要选权估计使用 pooled OOF。三臂差值做按图片/场景聚类的 paired bootstrap；若从六个 detector 中挑最佳者，选择步骤必须包含在内层交叉拟合中。

2. **已完成的数据规模消融**——gen493 全量（493）vs gen1085 全量（1085），两点统一 300 轮和 v4 三层评估；1085 点复用主实验 C 臂。
3. **消融与稳健性**：复核价值、空标图消融、多随机种子、工作点 PR、分辨率敏感性和误差分析图。主批次完成后排序。
4. **安全帽第二目标**（`Hardhat\` 素材已起步）——跨目标证据，支撑方法通用性；样本到手后的实验（含跨目标迁移、双目标统一模型）见清单第三节。

## 五、立论口径（红线）

- 主张 **methodology + empirical evidence**，不主张"合成数据优于真实"；"扩量有效/数量取胜"必须先有第四节 1/2 的实验支撑才可写进 contributions。
- **诚实口径**：C 臂编辑合成图的底图来自 93 张真实照片，主要补**状态多样性**；D 臂虽然从文本生成，LoRA 仍由 real93 训练，场景覆盖是否增加必须实测。论文同时报源照片数、生成候选数、质检保留数和提示词构成，不能只报总张数。
- **评估主张走“独立来源 dev + cross-fitted held-out 估计”**：合成数据的编辑源就是真实种子照片，所以不能拿同源真实照片评估；dev61 的来源独立性和内部近重复由缩略图检查支持，但它已参与协议判断，因此不称最终 test。选权泛化主张只来自 pooled OOF。
- **部署与论文报数分离**：全 dev61 选择出的权重用于部署；其同集最大值只能称 development score。将来新增并冻结的数据才可成为最终 test。
- **三级定位**：
  1. **Application paper**（单目标，第四节 1~3 完成即可成文首投）；
  2. **Method paper**（加安全帽跨目标证据 → "可推广到其它稀缺目标的编辑合成管线"，素材全复用）；
  3. **通用数据增广协议**（升格为正式贡献需要**第二个非工地域**的证据；当前只作 Discussion 愿景与 future work，避免 overclaim）。
- 建议路径：首投版按 Application 写；等首投结果期间跑消融与稳健性；转投升级视第二目标完成度决定。
- 通用性主张靠"跨行业数据稀缺"的动机论述（Introduction/Discussion）+ 跨目标证据（4.5）两头支撑。
- 合成数据按各刊 **AI 使用披露政策**写明生成工具/模型/版本：C 臂引用 Qwen-Image 技术报告与 Qwen-Image-Edit-2509 模型卡；D 臂引用 Qwen-Image-2.1 官方模型卡/仓库、Qwen3-VL-8B 编码器模型卡及 Comfy-Org 的量化文件与 VAE 封装来源。Qwen-Image-2.1 模型卡当前标示 Qwen Research License；计划发布 LoRA、权重和数据前逐项核对许可，不能沿用 C 臂的许可判断。

## 六、工作流

- 英文初稿直接写在 `working_paper.tex`；中文素材（PROGRESS/COMMANDS）可喂给 LLM 起草再人工重写。
- 参考文献：`paper/references.bib` 已加入 D 臂所用官方模型/封装来源；Z-Image 论文不再作为实施工具依据。加新文献时可用 `paper/fetch_refs.py` 半自动抓取（Crossref/DataCite），但**必须人工复核**（重跑会覆盖已校对内容）。
