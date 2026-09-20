# Figure 1 — 管线总图（mermaid 草图，v4 口径）

> 用途：先用 mermaid 把思路直观记下来；定稿前用 TikZ 正式重绘为 `figures/fig1_pipeline.pdf`，替换 `working_paper.tex` 中 Fig.1 占位。
> 红线：图只表达流程；具体数字不写进图（数字以 `PROGRESS.md` 三（结果与结论）为准）。
> 当前口径：**dev61 = 61 张网络来源图**；统一训练后分三层报告 fixed endpoint、cross-fitted pooled OOF 和 deployment selection。

```mermaid
flowchart TD
    subgraph SEED["① Real seed data"]
        R1["93 real inspection photos"] --> R2["Expert annotation<br/>(1 class: placement issues)"]
    end

    subgraph EXPAND["② Three same-source expansion arms"]
        A1["A: as-is<br/>(93 photos)"]
        A2["B: classical offline augmentation<br/>(flip / rotate / scale-shift / HSV<br/>-> 1085 images)"]
        A3["C: state-editing synthesis<br/>(Qwen-Image-Edit-2509 edits of the<br/>same 93 photos -> 1085)<br/>realism constraint: wear / stain / rust"]
    end

    subgraph REV["③ Auto-labeling + human-in-the-loop review (arm C)"]
        L1["Labeler model pre-labels<br/>generated images"]
        L1 --> L2["Human review in GUI<br/>(every image checked / corrected)"]
        L2 --> D1["Reviewed synthetic dataset<br/>(1085 training images)"]
    end

    subgraph EVAL["④ Unified training + cross-fitted evaluation"]
        T1["Six detectors, identical hyperparameters<br/>(300 epochs, imgsz 640, batch 16,<br/>patience=0, snapshots every 10 epochs)"]
        T2["Independent-source dev benchmark:<br/>61 web images, 72 boxes<br/>(no source / scene overlap)"]
        T4["Three reports:<br/>fixed endpoint / pooled OOF / deployment model"]
        T3["Reproducible independence check<br/>(thumbnail correlation)"]
        T1 --> T2 --> T4
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
| ② Three arms | A = 原样 93 张；B = 传统离线增广到 1085 张；C = Qwen-Image-Edit-2509 编辑合成 1085 张 | same-source augmentation arms: none / classical / state-editing |
| ③ Labeling loop | 打标模型预标注 → GUI 逐张人工复核（100% 复核率） | auto-labeling with human-in-the-loop verification |
| ④ Unified protocol | 六 detector 统一超参；dev61 做 fixed endpoint、5 折 pooled OOF 与部署选权；来源独立性由缩略图相关性检验支持 | unified training with cross-fitted held-out evaluation |
| ⑤ Deployment & reuse | 工地危险目标检出；管线复用到下一稀缺目标（安全帽） | reusable augmentation recipe for scarce targets |

## Fig.1 英文 Caption 草稿（定稿时可改）

**Fig. 1.** Overview of the proposed pipeline. A small expert-annotated real seed set (①) is expanded along three same-source arms (②): no augmentation, classical offline augmentation, and state-editing synthesis under a realism constraint. Generated images pass through auto-labeling with human-in-the-loop verification (③). All arms share one training protocol and are evaluated on an independently sourced development benchmark using a fixed endpoint, cross-fitted held-out predictions pooled for AP, and a separately identified deployment model (④). The recipe is designed to be re-instantiated for other scarce hazardous targets (⑤).

## TikZ 重绘提醒

- 建议布局：纵向四段（Seed → Expand → Review → Train/Evaluate），右侧竖排画 dashed 的 "reuse loop" 回到 Seed。
- 关键视觉对比：实线 = 主流程；虚线 = 检查/可选/复用路径；把 "human review" 与 "independent-source dev + cross-fitting" 两个质量门用同一种醒目标记。
- ② 建议画成从同一批 93 张分出的三条并行支路（A/B/C 并排），这是论文的核心对照，一眼要能看出"同源、只差怎么扩"。
- 最终绘图时可减少具体数字，把精确样本量留给正文与表。
