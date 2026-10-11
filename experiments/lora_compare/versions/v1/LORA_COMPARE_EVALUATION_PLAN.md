# LoRA 153 张三维评价：执行交接计划

制定日期：2026-10-10。状态：计划已整理，尚未计算分数、开展人工评价或生成结果图表。后续模型可直接按本文实现和执行自动化部分；人工评分返回前产出自动指标和评审包，随后暂停需要评分的汇总环节。

## 1. 目标、已确认事实与边界

评价现有 153 张图，形成一张论文参数对比图、一个 17 行结果表，以及可复核的逐图数据。分析既有 D 臂配置 step-1860 / strength 0.8 在本次比较中的位置；结论允许支持保留，也允许暴露不足，不能按目标排名调整规则。

- 输入：`D:\gas_cylinders\lora-compare`，原图只读。
- 16 个 LoRA 配置：step ∈ {500, 1000, 1500, 1860} × strength ∈ {0.2, 0.5, 0.8, 1.0}；加 1 个无 LoRA 基线。
- 3 条提示词：`new150_010`（N010）、`new24_001`（N151）、`new24_010`（N160）。
- 3 个 seed：99999、88888、77777。每配置 9 张，共 153 张。无 LoRA 共 9 张，不能重复算成四个 checkpoint 的基线。
- 文件示例：`1860-0.8_new150_010_seed99999_00001_.png`；基线前缀 `no-lora`。ComfyUI 末尾计数不是实验 seed，也不是独立重复编号。
- **作者于 2026-10-10 确认：`qwen_image_2.1.safetensors` 是 `qwen_image_2.1_int8_convrot.safetensors` 的手动改名，仍为原权重。**记录为作者确认的别名关系，无需再质疑文件名或要求重新证明；不能写成已执行双文件哈希核验。
- 三张参考 PNG 元数据已读取：1184×896、25 steps、CFG 1、Euler/simple、denoise 1、空负面提示词。执行时完整核对 153 张元数据及有效采样连线。
- 本研究是 D 臂完成后的补充参数敏感性分析。作者已看过部分图片；本计划属于计算汇总分数前制定的分析规则，不能称为生成前预注册或完全未见数据。
- 本轮不启动 ComfyUI、不读取 Desktop 日志、不新增生成、不训练 detector、不修改 D1085/D493 数据或既有实验结果。不得为获得理想排名删除 0.2 强度或失败图片。
- `scripts/queue_lora_compare_seeds.py` 是历史生成脚本，仍可能引用改名前的原始 51 个文件名。本任务直接读取现有 153 张，不运行该脚本。

## 2. 执行顺序和环境

1. 阅读项目指令、本文及 `docs/v5_prompts/generation_models.md`。查看 Git 当前改动，保留其他图件和 D493 工作。
2. 检查 `python` / `py` / `python3` 实际路径，优先使用项目兼容环境。实现、环境隔离、缓存和测试均在工作区；需要依赖时记录安装版本，不升级破坏既有 detector 环境。可建独立 `.venv-lora-eval`，加入精确忽略规则。
3. 实现 `scripts/eval_lora_compare.py`；建议子命令 `prepare`、`clip`、`review-pack`、`aggregate`、`report`，另写小型必要测试。**这些是待实现接口，不是已有可运行脚本。**
4. `prepare` 建立输入清单、提取原始提示词和工作流、检查矩阵；落实本文短文本和评审项，做 tokenizer 长度检查，保存 `protocol.json` 及 SHA256，再开始 `clip`。冻结后不因结果改文本、评分条件、模型或展示规则。
5. `clip` 计算全部 153 行；`review-pack` 生成两套匿名评审包。完成自动结果摘要和待人工字段为空的草稿表。将评审包实际路径交给作者，并说明操作方法。
6. 等待人工评分期间可完成图表程序、自动热图、完整定性附图。不得自行把视觉模型输出填入人工评分表。
7. 收到人工评分后校验、形成分歧清单；只就分歧请人工裁决。保留两名评分者原始记录与裁决记录，完成汇总、图表、Methods/Results 文本和复核说明。

自动化恢复必须按输入、协议、模型和脚本哈希判断缓存有效性，避免重复推理或静默复用旧协议分数。缺文件、重复实验单元、有效连线错误、未解释的采样差异先生成异常报告；保留全部原图，不自行补生成或选择较好的重复图。

## 3. 数据核对与冻结产物

输出统一在 `experiments/lora_compare/`，避免新建多个交接目录。

`manifest.csv` 每图一行，至少包含：`image_id,filename,sha256,prompt_id,seed,step,strength,is_baseline,width,height,prompt_sha256,workflow_sha256`。模型名、文本编码器、VAE、采样参数、有效 LoRA 连线保存在 `metadata.json`。image_id 使用不随显示编号改变的唯一标识。

从 PNG 的 `prompt` API 图出发，追踪实际连接到 KSampler 的模型、文本和 latent；未连接的 LoRA 节点不代表生效。断言每个 (config,prompt,seed) 恰好一图、每配置 9 图、总计 153；同 prompt 下原始文本一致。SHA256 重复只标记，不自动删图：不同配置的相同输出也可能是实验结果，需检查是否复制错误或真实相同生成。

协议保存配置顺序、三个完整原始提示词、短文本、检查项、排序与并列规则、评审随机种子、图件展示清单、日期、脚本哈希。完整原始文本从 PNG 原样提取，不用概括内容替代来源。

## 4. 维度一：自动 CLIP 图文相似度

- 模型固定 OpenAI CLIP `ViT-L/14`（224 像素版本），优先官方实现。记录源码 commit/包版本、模型文件 SHA256、torch/torchvision/Pillow 版本、推理设备及 dtype。模型可下载到工作区缓存；下载失败如实报告，不悄悄换模型。
- 图像使用官方预处理：等比例缩放、中心裁剪、RGB、对应标准化。CLIP 看到中心裁剪内容；人工评价始终看完整图片，并在方法局限中说明这一差异。不可为某张图手工取最佳裁剪。
- `eval()`、无梯度推理，建议 float32；编码向量分别 L2 归一化。
- 指标名 **CLIP-T similarity**，公式 `100 × cosine(image_embedding, text_embedding)`。不使用 softmax 概率、模型 logit_scale 或额外截断/乘 2.5；不冒称与另一论文的不同实现绝对可比。
- 3 条短文本对所有配置共用，每图仅比较对应提示词，不在多个文本中挑最高值。保留完整原始文本，短文本只服务评价。
- CLIP 总上下文 77 token（含特殊符号）。检查真实 tokenizer；禁止静默截断。下面短文本若超限，只能在任何图像分数计算前做最小删减，并保存最终版本和 token 数。不要把这些短句称为实际生图原文。

固定短文本：

| prompt_id | CLIP 评价文本 |
|---|---|
| new150_010 | A realistic construction-site photograph of exactly one complete blue industrial gas cylinder lying horizontally on a roof deck beside insulated ductwork, with a clear gap, an unobstructed body, and no other cylinders. |
| new24_001 | A realistic construction-site photograph of twelve tall blue industrial gas cylinders standing upright in two rows inside an open-top rectangular blue steel storage cage, on wet concrete in rainy weather. |
| new24_010 | A realistic construction-site photograph of eight tall silver-gray industrial gas cylinders standing in a compact irregular cluster beside a concrete column in a partially covered storage area, with no enclosing cage or shared securing frame. |

`clip_scores.csv` 保存 153 个逐图分数、文本/模型/协议哈希。汇总：每配置 n=9 的算术均值、样本标准差（ddof=1）；另存每 prompt 的 3-seed 均值及各 seed 的 3-prompt 均值。均衡矩阵下总体均值等于三个 prompt 均值的等权平均。SD 描述本批分数离散程度，不是标准误或置信区间。

## 5. 人工评价包：两维度、逐图判断

### 5.1 谁来评、如何隐藏信息

推荐两名能识别气瓶和理解检测标注要求的人员，各自评完 153 张，共 306 次单图评审；之后裁决分歧。只有一人时仍可执行，明确写单人评价，不虚构第二人、一致性或独立盲评。

生成两份可本地打开的 HTML 评审页面及导出说明。图片用匿名编号 `LC001` 等，移除副本中的 PNG 工作流元数据，原图不动；评审页、资源文件名、工具提示、下载名称、网页源码均不包含 config/step/strength/原文件名/CLIP 分数。评审映射单独保存在 `restricted/`，不放入给评分者的包。

用 `random.Random(20261010)` 分配匿名编号；R1/R2 分别用 20261011/20261012 随机展示，记录实际顺序。包内显示完整原图，支持放大；隐藏提示词时先完成训练可用性判断，再显示提示词及检查项进行要求符合性评价。评审导出后显示已评数量、缺项，支持保存和继续。

作者已见过图片，不能保证认不出配置。因此方法表述为“隐去配置标签后独立评价”，不夸大为评分者从未见过数据。评分提交前不给排名和 CLIP 结果。执行模型本身看到分数不等于人类评分者必须看到。

### 5.2 维度二：关键要求符合率

每项填 `pass / fail / uncertain`，记录可见气瓶数（整数或 uncertain）及简短理由。只评价表内预先列出的关键要求；完整 prompt 中其它细节可备注，不事后扩充主评分条件。

| prompt_id | 固定关键检查项 |
|---|---|
| new150_010 | (1) 恰好一个气瓶且无其它气瓶；(2) 蓝色、横卧；(3) 瓶身完整在画内、轮廓可辨、无物体横穿遮挡；(4) 屋面施工场景，邻近保温风管，气瓶与其它材料有可见间隙 |
| new24_001 | (1) 可确认恰好十二个气瓶；(2) 蓝色且竖直；(3) 呈两排排列；(4) 整组位于蓝色矩形钢制储存笼架内，开放顶、立柱与横杆可辨；(5) 湿混凝土地面及阴雨环境外观 |
| new24_010 | (1) 可确认恰好八个气瓶；(2) 银灰色且竖直；(3) 紧凑不规则聚集；(4) 整组无围合储瓶笼架、无共同固定框架；(5) 混凝土柱附近、部分遮盖的施工储存场景 |

遮挡导致无法确认数量就填 uncertain，不猜测隐藏瓶数。普通背景脚手架不自动等同储瓶笼架。形状自然的重叠与融合畸形分别判断。

每图 `prompt_pass=1` 当且仅当全部关键项 pass；有 fail 或 uncertain 则 `prompt_pass=0`，同时保留 uncertain 原因。主表列“可确认全部满足 n/9”；补充表逐项列通过、失败、不确定数，明确 0 包含未能确认，不把所有 uncertain 描述为确定生成错误。由于各 prompt 检查项数不同，不跨 prompt 池化所有检查项作为主指标。

### 5.3 维度三：检测训练可用率

目标是判断图片能否进入当前气瓶检测数据构建流程。参考既有 D 臂人工筛选和实际标注规则；历史记录未形成可直接照抄的完整量表，因此本节是本次明确化的操作规则，不能声称原 D1085 已按此量表逐图打分。

图片通过需要同时满足：

1. 至少一个可识别的工业气瓶，瓶体、瓶肩/阀门等可见部分不存在破坏目标身份的明显畸形或不可能融合。
2. 所有达到现有标注可见性要求的气瓶，实例及边界足够清楚，可按项目现有类别规则一致标注；合理透视、遮挡和画面边缘截断本身不一票否决。
3. 整体可作为真实施工场景照片，没有严重拼贴接缝、浮空、重复残肢式结构、覆盖目标的伪文字/表格或导致标注不可靠的画质缺陷。轻微污渍、锈迹、文字不可读等不单独否决。

每项 `pass / fail / uncertain`，记录原因代码：`no_target,malformed_target,fused_instances,ambiguous_annotation,severe_scene_artifact,other`。严重程度以是否妨碍上述用途为准，不因强度高或低判定，也不把风格偏好当缺陷。没有气瓶的图片在本次正目标提示词实验中不算可用正样本；不因此推断项目中空标负样本没有价值。

所有项 pass 才 `usable=1`；其它为 0，并单独保存不确定状态。气瓶数量、颜色、摆放与提示词不符，不自动影响 usable；例如自然的十瓶图可不满足十二瓶要求但可正确标注。不要依据 CLIP 分数、step、强度或作者想保留的配置评 usable。

每名评分者导出 `blind_id,rater_id,criterion_id,value,visible_count,note` 的长表或等价 JSON；附评分起止时间和规则版本。统计两人原始二分类判断的原始一致率与 Cohen's kappa（prompt_pass、usable 各自计算；分母 153；类别无变化导致 kappa 无定义时写 NA）。多项原始判断有任何分歧均进入裁决清单，裁决由人工按相同匿名编号完成；仍不能确认的保留 uncertain。主表用裁决后结果，同时留两人的原始汇总供审查。一人模式不算 kappa。

视觉语言模型若被用于额外探索，必须另列为机器辅助评价并记录模型、提示词和版本；不可替代这里的正式人工标签或伪装成第二名评分者。

## 6. 统计汇总与 1860 / 0.8 的解释

固定主表顺序：无 LoRA，然后 step 升序，每 step 内 strength 升序。17 行；列为 step、strength、CLIP-T mean±SD、关键要求全部满足 n/9、训练可用 n/9。必要时括号加百分比，不能只写百分比掩盖小分母。人工未完成的字段写 pending/NA，不填零。

三维度分别报告，不合成任意权重总分、不选择最有利的那一维充当整体冠军。训练可用率是任务直接指标，CLIP-T 是辅助一致性指标，关键要求通过率解释具体遵循能力。

另外输出 `reference_comparison.csv`，围绕 step1860_strength0.8：

- CLIP-T 在 16 个 LoRA 配置中的名次；无 LoRA 单独参照。按未四舍五入值排序，绝对差 ≤1e-6 仅视为数值并列，并列排名写区间。这个容差不是实质等效界值。
- 训练可用数、关键要求通过数分别的名次范围；同分并列，不靠 CLIP 拆解人工指标并列。
- 与每个候选的 9 个匹配 (prompt,seed) 分数差，逐 prompt 均值差、总体均值差；人工结果按匹配图列双方通过/失败的四格计数。
- 各 prompt 单独排名、各 seed 平均排名，以及逐次去掉一条 prompt 后剩余两条的描述性排名。报告排名范围，防止总体均值遮住场景差异；这些共享数据的结果不是独立重复实验。

本阶段不要求显著性检验、不生成“属于前几名的概率”、不凭 9 图做强非劣结论。153 是全体图数，每配置 n=9，只有 3 个提示词；两名评分者不会使每配置样本数变成 18。随机 seed 也不等于增加提示词覆盖。

允许的结果表述须由实际数字填入，例如：“现用配置在 16 个 LoRA 配置的平均 CLIP-T 排名 X，训练可用 Y/9（并列名次范围 A–B）；三种场景分别为……”。仅可称本次三个提示词范围内的结果。“前几名”必须指明哪一个维度及并列情况。

不允许用 p>0.05、误差条重叠、接近最高值的任意百分比阈值，或低精度四舍五入并列来宣称等效/非劣。没有外部任务依据时不凭空设 CLIP 差 1 分或 5% 的容忍线。既有 D 臂是给定配置下的检测实验，配置未排名第一不使其失效；最终保留/补实验由作者根据透明结果决定。

若要更强的近优证据，在本次结果之外制定独立确认方案：当前配置与筛出的候选使用新提示词、匹配 seed；事先确定主要终点、任务上有意义的非劣界值、样本量及多比较处理。选候选和确认同用这 153 张会有选择偏差。本轮只提出具体建议，不自动生成或重训，也不把检测 dev61 用于挑 LoRA。

## 7. 一张对比图、一个表与补充材料

固定图名 `lora_parameter_sensitivity`，暂不占用最终图号；`paper/FIGURES.md` 的现 Fig.13 预留项可记录为候选，最终编号由论文整体确定。

主图定性展示固定 seed **99999**，固定两条 prompt **new150_010 和 new24_001**（单瓶与笼装多瓶的预设场景对比）；这些已知图像的选择应如实说明，并非随机代表性抽样。每个面板同一行 prompt/seed 相同，不按配置挑各自最好 seed。

- (a) 两行 × 四列：strength 0.8，step 500/1000/1500/1860。
- (b) 两行 × 五列：step1860，无 LoRA/0.2/0.5/0.8/1.0。无 LoRA 列实际使用对应 baseline。
- (c) 4×4 热图：全部 9 图/配置平均 CLIP-T，标出当前配置，不把使用标记画成胜出标记；基线总体均值可独立注记，不重复入格。

使用完整图片保持比例，不为改善外观裁掉畸形、页脚或边缘目标；允许统一留白。0.2 保留。1.0 只标强度，不能预写“过拟合”。灰色细框指当前配置，各指标最佳值在表内加粗，基线及并列处理写入图注。

主表按第 6 节生成 CSV + LaTeX + Markdown。主图首选 Python 排版导出矢量 PDF（嵌入原图）、SVG 和 300 dpi PNG，字体嵌入、成稿通栏约 180 mm 宽时关键文字≥7 pt、所有图像比例一致、色盲友好。热图文字按所用色图实际对比度设黑/白，本表 CLIP 数值不是 0–1，勿照搬此前 Fig.5 的 0.50 阈值。最终需渲染检查标题、图注、图像细节与字体。

本轮无需自动扩展为 PPT 任务；作者需要可编辑 PPT 时再按项目现行技能和规范处理。无需修改旧图构建器或覆盖现有图件。图注明确展示用 seed，热图/表使用全部三 seed，n=9，SD 定义，人工人数及裁决方式，分析是补充评价。

补充材料：按三个 prompt × 三个 seed 制作 9 页完整网格，每页 16 个 LoRA 配置加一个基线，共覆盖 153 张；附全部逐图 CLIP、匿名评价和逐 prompt 汇总。完整网格给读者，正式评分者不提前收到带配置的网格。

## 8. 交付目录、测试和停点

建议产物（评分包生成前不预称已存在）：

```text
docs/LORA_COMPARE_EVALUATION_PLAN.md     本计划
scripts/eval_lora_compare.py            唯一自动化入口及 --help
scripts/tests/test_lora_compare.py      必要的逻辑测试
experiments/lora_compare/
  protocol.json / protocol.sha256
  manifest.csv / metadata.json / prompts.json
  environment.json / execution.json
  clip_scores.csv / per_prompt.csv / summary.csv
  reference_comparison.csv
  restricted/                          匿名映射、原始评分、分歧与裁决
  review/                              R1/R2 本地 HTML 评审包及保存说明
  report.md                            当前阶段、实际数值与局限
  methods_results.md                   可放入论文的文本及图表标题
  acceptance.json                      完整性、数值重算、版本和图件检查
paper/tables/lora_parameter_sensitivity.tex
paper/figures/lora_compare/             主图 PDF/SVG/PNG、补充网格 PDF
```

脚本源、冻结协议、逐图/汇总数据、匿名评分和最终图表可纳入 Git；模型权重、独立虚拟环境、匿名图片副本和缩略图缓存只在本地，以精确规则忽略。restricted 表示避免进入评分包，不代表密码保护，也不应存真实评分者姓名等不必要个人信息。按项目 .gitignore 核对多层 PDF 跟踪规则；提交/推送由作者负责。

必要测试：矩阵缺失/重复可检测；无 LoRA 有效连线判定；文本超长报错；匹配差值方向；并列名次范围；uncertain 聚合及缺失人工标签不当零；导入未知/重复匿名 ID 拒绝；评分包无配置映射或 PNG 元数据泄漏。CLIP 冒烟只测输入输出及有限性，成功后执行全量一次；从逐图分数独立重算表格核对。原图前后哈希不变。

**明确停点：**自动化模型完成准备、CLIP、评审包、自动图表草稿后，只等待真实人工标签，不代填。人工完成前报告“CLIP 已完成，人工两维待评价”，不得称三维评价已完成。人工返回后继续导入、裁决与最终成稿；需人工裁决时只等待有争议项。整个任务不以“证明1860/0.8可保留”为验收条件。

## 9. 给执行模型的启动指令

> 请阅读 `D:\yolo\docs\LORA_COMPARE_EVALUATION_PLAN.md` 并据此实现、执行 LoRA 153 张三维评价。当前交付物是计划，脚本与评分尚未完成。直接推进输入冻结、CLIP 自动评价、两套匿名人工评审包及能完成的论文图表草稿；原图位于 `D:\gas_cylinders\lora-compare`。基础模型两种文件名是作者确认的同一权重改名。保存可复核逐图结果，原图只读，不读取 Comfy Desktop 日志，不新增生成或重训。真实人工评分是明确停点：届时给出可打开的评审入口、保存方法和需评分数量，等待作者提供评分；不得把你自己的视觉判断冒充人工评价。保护工作区已有改动，不提交或推送。

## 10. 方法来源

- [OpenAI CLIP 官方实现](https://github.com/openai/CLIP/blob/main/clip/clip.py)：模型、预处理和 tokenizer。执行时保存实际版本；网页 main 可变。
- [CLIPScore 原论文](https://aclanthology.org/2021.emnlp-main.595/)：图文一致性的评价依据；本计划明确使用自述缩放的 CLIP-T 余弦分数。
- [GenEval 原论文](https://arxiv.org/abs/2310.11513)：整体图文分数不足以覆盖数量、颜色和位置等细粒度要求，支持单列检查项；本实验不声称运行了标准 GenEval benchmark。
- [Lakens, Equivalence Tests](https://doi.org/10.1177/1948550617697177)：不显著不等于等效，实质界值应有依据并预先确定。本轮只做限定范围的描述性分析。
