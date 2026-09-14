# PAPER_PLAN.md — 论文写作计划（2026-09-14 立）

> 定位：论文投稿的唯一规划文件。写作进展按项目惯例回写 `PROGRESS.md`；实验结果出来后更新本文件第三、四节状态。
> `working_paper.tex`（用户自建）为正文工作文件；投稿模板见第一节第 4 条。

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

1. **Introduction**——工地危险样本稀缺是趋势性问题、摆拍有安全与伦理问题、生成式扩量是出路；结尾放显式 contributions 列表（C1 打标闭环管线；C2 干净 test 评测协议与泄露分析；C3 数量取胜的实证 + （第二目标完成后）跨目标通用性）。
2. **Related Work**——2.1 CV for construction safety（气瓶/PPE/安全帽检测）；2.2 synthetic & generative data for object detection（GAN/diffusion 扩增、sim2real、copy-paste）；2.3 auto-labeling 与 human-in-the-loop。
3. **Methodology**——3.1 问题与类别定义（监理口径：放置问题=未固定，含倒地）；3.2 真实种子数据（93 张人工标注，正/负样本设计）；3.3 生成管线（z-image-turbo 文生图、qwen-image-edit 编辑真实照片、canny ControlNet 试验；真实性红线：脏污/磨损，防"过净"域差）；3.4 自动预打标 + 人工复核闭环（labeler 模型 + annotator GUI）；3.5 评测协议（分层划分、**93 张真实照片绝不参与训练**的红线、全量口径 vs val18 干净口径的泄露分析）。
4. **Experiments**——4.1 setup（6 权重 × 统一超参、硬件）；4.2 labeler 基线与泄露分析（93 全量 vs val18 双口径）；4.3 主结果：生成数据增益（gen493 复核修订版六权重全表，val18 两轮 6/6 全胜）；4.4 **数据规模消融**【待实验】；4.5 推理分辨率分析（imgsz 扫描；真实照片 17% 小目标在 640 下被压没的发现）；4.6 **跨目标扩展（安全帽）**【待实验】；4.7 **基线对照**【待实验，审稿人必问：经典增广、公开数据】。
5. **Discussion**——domain gap 的两个来源（过净 + 小目标分辨率）；合成数据伦理与 AI 披露（生成图是方法组件，按各刊政策写明工具与模型并引用官方论文）；向其它行业稀缺目标推广。
6. **Conclusion**（最后写）。

**篇幅（按落点）：**

| 落点 | 正文 | 图/表 | 参考文献 |
|---|---|---|---|
| Automation in Construction（首投） | 8000~10000 词 | 图 8~12、表 4~6 | 60~90 条 |
| Sensors / Buildings（MDPI 落点） | 5000~7000 词 | 图 6~10、表 3~5 | 40~60 条 |
| Scientific Reports | 正文约 4000~5000 词 + Methods 独立后置节 | 同上偏少 | 40~60 条 |

**图表素材清单**（可先攒）：图 1 管线总图（必画，Methodology 骨架）；生成样本拼图（展示脏污真实感）；泄露示意（75/93 在基线训练集内）；六权重结果表；val18 对比表；imgsz 扫描曲线；真实照片检出示例；【待】规模-性能曲线；【待】安全帽样本与结果。

## 三、写作状态：现在能写 vs 等实验

| 部分 | 状态 | 依据/素材 |
|---|---|---|
| Related Work（全部） | ✅ 可写，需先文献调研 | 检索词：construction site safety detection；synthetic data for object detection；diffusion data augmentation；sim2real；auto-labeling human-in-the-loop |
| Methodology（3.1~3.5 全部） | ✅ 可写 | `PROGRESS.md`（项目/数据节）+ `COMMANDS.md`（协议与数字全有） |
| Experiments 4.1 / 4.2 / 4.3 / 4.5 | ✅ 可写 | `phase6_gen493_summary.json`（权威数字）+ `PROGRESS.md` 三（结果与结论） |
| Introduction | ✅ 初稿（C3 贡献留占位，等规模实验） | 项目"一句话+主故事线" |
| Discussion | ✅ 初稿 | v0/v1 教训 + imgsz 发现 |
| Experiments 4.4 规模消融 | ⛔ 等实验 | 最便宜且最撑「数量取胜」（见第四节） |
| Experiments 4.6 第二目标 | ⛔ 等实验 | 跨目标证据，三级定位第 2 级的门槛（见第五节） |
| Experiments 4.7 基线对照（经典增广 / 公开数据） | ⛔ 等实验 | 审稿人必问，第四节 3/4 |
| Conclusion | 最后写 | — |

## 四、投稿前必须补的实验（按优先级）

1. **250 vs 493 减半对比**（现批次减半；最佳权重或 s 家族 2~3 个，GPU 1~2 h）——量-效曲线第一个点，最便宜、最能支撑"数量取胜"。
2. **再生成 500 张扩到约 1000（现 493 + 500）重训**（`scripts\prepare_labeling_workspace.bat` → 复核 → 全量重训，管线现成）——第二个点；若增益停滞，故事以减半对比为主。
3. **经典增广对照**（审稿人必问）：75 张真实图上做 flip / mosaic / copy-paste 等传统增广训练对照——回答"为什么生成式扩量，而不是免费的传统增广"。
4. **公开数据对照**（审稿人必问）：Roboflow 气瓶数据集（数据区两个、共约 1.3 万张，仅"气瓶"框无放置口径）预训练或混入对照——回答"为什么生成而不用现成公开数据集"。
5. **安全帽第二目标**（生成 200~500 张 + 复核 + 训练；`安全帽\` 素材已起步）——跨目标证据，支撑方法通用性。
6. （可选，应对审稿人必然之问）**混合训练口径**：493 生成 + 75 真实，test 退 val18——回答"为什么不混真实数据"。

## 五、立论口径（红线）

- 主张 **methodology + empirical evidence**，不主张"合成数据优于真实"；"数量取胜"必须先有第四节 1/2 的实验支撑才可写进 contributions。
- **三级定位**（与路线图第 5 步口径一致）：
  1. **Application paper**（单目标，第四节 1/3/4 完成即可成文首投）；
  2. **Method paper**（加安全帽跨目标证据 → "可推广到其它稀缺目标的增广管线"，素材全复用）；
  3. **通用数据增广协议**（"各行各业数据稀缺都适用"——升格为正式贡献需要**第二个非工地域**的证据；当前只作 Discussion 愿景与 future work，避免审稿人攻击 overclaim）。
- 建议路径：首投版按 Application 写；等待首投结果期间跑第四节 2/5；转投升级视第二目标完成度决定。
- 通用性主张靠"跨行业数据稀缺"的动机论述（Introduction/Discussion）+ 跨目标证据（4.6）两头支撑，不靠行业内单一数据集硬撑。
- 合成数据按各刊 **AI 使用披露政策**写明生成工具/模型/版本并引用官方论文（qwen-image-edit 授权已确认，仅需引用论文）。

## 六、工作流

- 每完成一节：勾掉第三节状态表对应行，回写 `PROGRESS.md` 截止行一句话。
- 数字一律取自 `phase6_gen493_summary.json`（最新复核修订版；`phase5_gen500_summary.json` 为复核前 500 张初版）/ 后续 summary 文件，不在正文手抄（防口径漂移）。
- 英文初稿直接写在 `working_paper.tex`；中文素材（PROGRESS/COMMANDS）可喂给 LLM 起草再人工重写。
- 参考文献：`paper/references.bib`（44 条，已逐条核验）；加新文献时可用 `paper/fetch_refs.py` 半自动抓取（Crossref/DataCite），但**必须人工复核**（重跑会覆盖已校对内容）。本地还没有 PDF 的文献清单：`reference/TO_DOWNLOAD.md`。

## 七、arXiv 预印本操作清单（"怎么搞，要搞什么"）

**定位**：arXiv 是预印本平台，非期刊；挂预印本不影响 AiC 投稿（Elsevier 允许，不算 prior publication；但不要把出版社排版版传上去）。作用：占时间戳、立优先权、便于分享。

**要准备的核心三样**（按动手顺序）：
1. **账号**：注册 arXiv 账号，用机构邮箱，绑定 ORCID。
2. **背书（endorsement）**：新用户投 **cs.CV 需要背书**——找已在 arXiv 发过文的合作者/导师在你的账号页面 endorse；部分机构邮箱可自动放行。**这步最耗时，提前办**。
3. **能干净编译的 LaTeX 包**：`.tex` + `references.bib` + `.bbl` + `figures/`（elsarticle 官方支持；本地先完整编译一遍；不要绝对路径）。把 `.bbl` 一起打包更稳（arXiv 自动跑 bibtex，失败时有兜底）。

**流程**：上传 → 选 primary category（cs.CV，必要时 cross-list）→ 填标题/摘要（摘要 ≤1920 字符）/作者/备注 → 选 license（arXiv 默认非独占许可；注意与 AiC 的兼容性）→ 提交。首次投递需 moderation，通常 1~3 个工作日；通过后按 announcement 排期（美东时间工作日 14:00 截点，次工作日放出）。

**版本与后续**：修改用 replace 出 v2/v3…；论文录用后回头补 journal-ref 与 DOI。

**时机建议**：与首投同步或略早（等待秒拒的几周不浪费）；不必等审稿结果。
