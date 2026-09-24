# PAPER_PLAN.md — 论文写作计划（v4）

> 当前口径：61 张独立来源网络图为 **dev61**，不是 sealed final test。三臂统一训练 300 轮、每 10 轮保存快照；报告固定终点 benchmark、5 折 pooled OOF 选权估计和全 dev61 部署模型三层结果。

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

1. **Introduction**——工地危险样本稀缺是趋势性问题、摆拍有安全与伦理问题、**编辑合成（state-level augmentation）**是出路；结尾放显式 contributions 列表（C1 编辑合成 + 预打标 + 人工复核的闭环管线；C2 **独立来源 dev benchmark + 可复现的来源独立性检验 + 小样本交叉拟合评估**；C3 与经典增广的同源对照 + 规模效应；C4（第二目标完成后）跨目标通用性）。
2. **Related Work**——2.1 CV for construction safety（气瓶/PPE/安全帽检测）；2.2 synthetic & generative data for object detection（GAN/diffusion 扩增、sim2real、copy-paste）；2.3 auto-labeling 与 human-in-the-loop。
3. **Methodology**——3.1 问题与类别定义；3.2 真实种子数据；3.3 编辑合成管线；3.4 自动预打标 + 人工复核；3.5 **v4 评估协议**（dev61 的统计角色；固定终点；分层 5 折交叉拟合；pooled OOF AP；全 dev61 部署选择；detector+checkpoint 联合选择）。
4. **Experiments**——4.1 setup；4.2 **主结果：三臂同源对照**（每 detector fixed endpoint + OOF，另报 arm 级联合 OOF）；4.3 **数据规模消融**（493 vs 1085，同一 v4 协议）；4.4 选权稳定性与 deployment epoch 分布；4.5 推理分辨率分析；4.6 跨目标扩展【待素材】；4.7 消融与稳健性。
5. **Discussion**——固定终点、OOF 估计和部署选择的角色差异；dev61 规模限制与 winner's curse；domain gap；合成数据伦理与 AI 披露；向其它行业稀缺目标推广。
6. **Conclusion**（最后写）。

**篇幅（按落点）：**

| 落点 | 正文 | 图/表 | 参考文献 |
|---|---|---|---|
| Automation in Construction（首投） | 8000~10000 词 | 图 8~12、表 4~6 | 60~90 条 |
| Sensors / Buildings（MDPI 落点） | 5000~7000 词 | 图 6~10、表 3~5 | 40~60 条 |
| Scientific Reports | 正文约 4000~5000 词 + Methods 独立后置节 | 同上偏少 | 40~60 条 |

**图表素材清单（2026-09-24 更新）**：图 1 管线总图（工作区外绘制，占位已可编译，中列仍空）；图 2 三臂样例对比（脚本出＋人工定稿，已压到 1.15 MB，去留未定）；图 3 选权曲线（三臂版，脚本出，正文已引用）；图 4 主结果 CI 图（脚本出，正文已引用）；图 5 定性检出图（文件为 `fig5_detection_comparison.pdf`，尚未接线）；图 6 规模曲线（脚本出，两指标，正文已引用）；**表格 9 张全部由 `--fig tables` 生成**：选权、主表（两指标两角色）、arm 级嵌套选择、bootstrap 对照、规模消融、数据集清单、独立性、协议、训练成本——**超过本文目标 4–6 张，需合并或移入补充材料**；【待】安全帽样本与结果。

## 三、写作状态：现在能写 vs 等实验

| 部分 | 状态 | 依据/素材 |
|---|---|---|
| Related Work（全部） | ✅ 可写，需先文献调研 | 检索词：construction site safety detection；synthetic data for object detection；diffusion data augmentation；sim2real；auto-labeling human-in-the-loop |
| Methodology（3.1~3.5 全部） | ✅ 可写（v4 协议已定稿） | `EXPERIMENTS.md` + `COMMANDS.md` |
| Experiments 4.1 / 4.2 主结果 | ⛔ 等 A/B/C 三臂统一协议结果 | `NEXT_STEPS.md` + `PROGRESS.md` |
| Experiments 4.3 规模消融 | ⛔ 等统一 300 轮的 493 点；1085 点复用 C 臂 | `NEXT_STEPS.md` |
| Experiments 4.4 选权稳定性 | ⛔ 等 v4 OOF 结果 | `experiments/v4_protocol/` |
| Experiments 4.5 分辨率分析 | 待主批次后执行 | `NEXT_STEPS.md` |
| Introduction | ✅ 初稿（C3 留占位，等 A/B 臂） | 项目"一句话+主故事线" |
| Discussion | ✅ 初稿 | 编辑合成 vs 传统增广的机制 + dev61 域差（小图） |
| Experiments 4.6 第二目标 | ⛔ 等素材 | 跨目标证据，三级定位第 2 级的门槛 |
| Experiments 4.7 消融与稳健性 | 待主批次完成后排序 | `NEXT_STEPS.md` |
| Conclusion | 最后写 | — |

## 四、投稿前必须补的实验（按优先级）

> 当前执行顺序见仓库根 `NEXT_STEPS.md`；本节只保留论文所需设计要点。

1. **三臂同源对照（主实验）**——回答"为什么用编辑合成，而不是免费的传统增广"。三臂都以 real93 为唯一数据来源，只差"怎么扩"：

   | 臂 | 训练数据 | 状态 |
   |---|---|---|
   | A 真实基线 | real93 全量 **93 张** | 待训（`v4\data_real93.yaml`） |
   | B 真实+传统增广 | 93 → **1085 张** | 生成脚本已实现，待重建核对与训练 |
   | C 编辑合成 | gen1085 全量 **1085 张** | 待按统一协议训练 |

   - 协议：300 epoch / imgsz 640 / batch 16，`patience=0`，`save_period=10`；报告 fixed endpoint、5 折 pooled OOF 和部署选择。
   - 增广类型：hflip、±10° 旋转、缩放平移、亮度/对比度/HSV；**不用上下翻转**（工地实景有重力方向）；几何变换同步变框。
   - **B 臂对齐口径**：总量与 C 臂一致（1085 张），不按“单图有无标签”配正负比。
   - **解读预案**：C > B > A → 同量级下编辑合成优于传统增广；B ≈ C → 口径改为"传统增广能补量、补不了状态多样性"；B 明显低于 C → 最常见、故事最顺。
   - 机制句（写进论文）：传统增广不产生**新的违规状态**（未固定/倒地等状态语义），编辑合成产生——这是两者本质差异，也是 B 臂的天花板。
   - 统计：dev61 仍偏小；主要选权估计使用 pooled OOF。三臂差值做按图片/场景聚类的 paired bootstrap；若从六个 detector 中挑最佳者，选择步骤必须包含在内层交叉拟合中。

2. **数据规模消融**——gen493 全量（493）vs gen1085 全量（1085），两点统一 300 轮和 v4 三层评估；1085 点复用主实验 C 臂。
3. **消融与稳健性**：复核价值、空标图消融、多随机种子、工作点 PR、分辨率敏感性和误差分析图。主批次完成后排序。
4. **安全帽第二目标**（`Hardhat\` 素材已起步）——跨目标证据，支撑方法通用性；样本到手后的实验（含跨目标迁移、双目标统一模型）见清单第三节。

## 五、立论口径（红线）

- 主张 **methodology + empirical evidence**，不主张"合成数据优于真实"；"扩量有效/数量取胜"必须先有第四节 1/2 的实验支撑才可写进 contributions。
- **诚实口径**：编辑合成图的多样性上界 = 源照片数量（93 张），补的是**状态多样性**而非场景多样性；论文里要同时报"源照片数 + 变体数"，不能只报总张数。
- **评估主张走“独立来源 dev + cross-fitted held-out 估计”**：合成数据的编辑源就是真实种子照片，所以不能拿同源真实照片评估；dev61 的来源独立性和内部近重复由缩略图检查支持，但它已参与协议判断，因此不称最终 test。选权泛化主张只来自 pooled OOF。
- **部署与论文报数分离**：全 dev61 选择出的权重用于部署；其同集最大值只能称 development score。将来新增并冻结的数据才可成为最终 test。
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
