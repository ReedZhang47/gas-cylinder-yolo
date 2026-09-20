# Figure 1 — 管线总图（mermaid 草图，v3 口径）

> 用途：先用 mermaid 把思路直观记下来；定稿前用 TikZ 正式重绘为 `figures/fig1_pipeline.pdf`，替换 `working_paper.tex` 中 Fig.1 占位。
> 红线：图只表达流程；具体数字不写进图（数字以 `PROGRESS.md` 三（结果与结论）为准）。
> v3 口径提醒：**test = 61 张网络来源图**（与 93 张巡检照片、以及由它们编辑出的 1085 张生成图都无来源/场景重叠）；三臂只差训练数据来源；统一 100 轮 / `patience=0` / 报 last.pt / 不做选权。

```mermaid
flowchart TD
    subgraph SEED["① Real seed data"]
        R1["93 real inspection photos"] --> R2["Expert annotation<br/>(1 class: placement issues)"]
    end

    subgraph EXPAND["② Three same-source expansion arms"]
        A1["A: as-is<br/>(93 photos)"]
        A2["B: classical offline augmentation<br/>(flip / rotate / scale-shift / HSV<br/>-> 868 images)"]
        A3["C: state-editing synthesis<br/>(Qwen-Image-Edit-2509 edits of the<br/>same 93 photos -> 1085)<br/>realism constraint: wear / stain / rust"]
    end

    subgraph REV["③ Auto-labeling + human-in-the-loop review (arm C)"]
        L1["Labeler model pre-labels<br/>generated images"]
        L1 --> L2["Human review in GUI<br/>(every image checked / corrected)"]
        L2 --> D1["Reviewed synthetic dataset<br/>(868 train / 217 val)"]
    end

    subgraph EVAL["④ Unified protocol + independent test"]
        T1["Six detectors, identical hyperparameters<br/>(100 epochs, imgsz 640, batch 16,<br/>patience=0, report last.pt)"]
        T2["Independent test:<br/>61 web images, 72 boxes<br/>(no source / scene overlap with<br/>the seed photos or their edits)"]
        T3["Reproducible independence check<br/>(thumbnail correlation)"]
        T1 --> T2
        T3 -.-> T2
    end

    subgraph USE["⑤ Deployment & reuse"]
        U1["Scarce-hazard detection<br/>on construction sites"]
        U2["Re-instantiate the recipe<br/>for other scarce targets<br/>(e.g., helmet non-use)"]
    end

    R2 --> A1
    R2 --> A2
    R2 --> A3
    A1 --> T1
    A2 --> T1
    A3 --> L1
    D1 --> T1
    T2 --> U1
    U1 -.-> U2
    U2 -.-> R1

    %% dashed = check / optional / later-stage connections
    %% ②-to-③ pipeline is the contribution: generated images are never used
    %% untagged -> auto-label -> 100% human review is the quality gate.
```

## 节点释义（写 Caption / Methodology 时用）

| 环节 | 实际做法 | 论文里的说法 |
|---|---|---|
| ① Real seed data | 93 张真实巡检照片人工标注（57 有框/179 框 + 36 空标）；**同时是 A/B 臂训练集与 C 臂编辑源** | small expert-annotated real seed set |
| ② Three arms | A = 原样 93 张；B = 传统离线增广到 868 张（几何+色彩，同步变框，不用上下翻转，只对总量）；C = Qwen-Image-Edit-2509 图生图编辑这 93 张得 1085 张（train 868） | same-source augmentation arms: none / classical / state-editing |
| ③ Labeling loop | 打标模型预标注 → GUI 逐张人工复核（100% 复核率） | auto-labeling with human-in-the-loop verification |
| ④ Unified protocol | 六权重统一超参、固定轮数报 last.pt；test 为外部网络图片，独立性由缩略图相关性检验复现 | unified protocol on an independently sourced test set |
| ⑤ Deployment & reuse | 工地危险目标检出；管线复用到下一稀缺目标（安全帽） | reusable augmentation recipe for scarce targets |

## Fig.1 英文 Caption 草稿（定稿时可改）

**Fig. 1.** Overview of the proposed pipeline. A small expert-annotated real seed set (①) is expanded along three same-source arms (②): no augmentation, classical offline augmentation, and state-editing synthesis that rewrites the *violation state* of the seed photos under a realism constraint (wear, stains, rust). Generated images pass through auto-labeling with human-in-the-loop verification (③) before entering training. All arms are trained under one unified protocol on six detectors and evaluated on an independently sourced test set — web images sharing neither source nor scene with the seed photos or with any image edited from them (④), with the independence claim backed by a reproducible thumbnail-correlation check. The recipe is designed to be re-instantiated for other scarce hazardous targets (⑤).

## TikZ 重绘提醒

- 建议布局：纵向四段（Seed → Expand → Review → Train/Evaluate），右侧竖排画 dashed 的 "reuse loop" 回到 Seed。
- 关键视觉对比：实线 = 主流程；虚线 = 检查/可选/复用路径；把 "human review" 与 "independent test (+ independence check)" 两个质量门用同一种醒目标记（如盾牌/对勾底色框）。
- ② 建议画成从同一批 93 张分出的三条并行支路（A/B/C 并排），这是论文的核心对照，一眼要能看出"同源、只差怎么扩"。
- 图中不放具体数字（93/868/1085 等），数字留给正文与表。
