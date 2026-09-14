# Figure 1 — 管线总图（mermaid 草图，2026-09-14）

> 用途：先用 mermaid 把思路直观记下来；定稿前用 TikZ 正式重绘为 `figures/fig1_pipeline.pdf`，替换 `working_paper.tex` 中 Fig.1 占位。
> 红线：图只表达流程；具体数字不写进图（数字以 PROGRESS.md 三（结果与结论）为准）。

```mermaid
flowchart TD
    subgraph SEED["① Real seed data"]
        R1["Real inspection photos"] --> R2["Manual annotation<br/>(human experts)"]
    end

    subgraph GEN["② Generative expansion"]
        G1["Text-to-image generation<br/>(Z-Image-Turbo)"]
        G2["Real-photo editing<br/>(Qwen-Image-Edit)"]
        G1 --> G3["Raw generated images"]
        G2 --> G3
        G3 --> G4["Realism QC<br/>(wear/stain/rust check;<br/>reject 'too clean' samples)"]
    end

    subgraph REV["③ Auto-labeling + human-in-the-loop review"]
        L1["Review passes to labeler model<br/>(trained on all data)"]
        L1 --> L2["Auto pre-labeling"]
        L2 --> L3["Human review in GUI<br/>(every image checked / corrected)"]
        L3 --> D1["Reviewed synthetic dataset<br/>(pos + neg samples)"]
    end

    subgraph TRAIN["④ Training & leakage-aware evaluation"]
        T1["Detector training<br/>(multiple YOLO variants,<br/>unified hyperparameters)"]
        T2["Real-only baseline<br/>(same detectors)"]
        T1 --> E1["Selection on synthetic val"]
        T1 --> E2["Clean real test<br/>(real photos NEVER trained on)"]
        T2 --> E2
        E2 --> E3["Leakage-aware dual reporting<br/>(full-set vs unseen-subset)"]
        E3 --> E4["Scaling ablation<br/>(quantity over quality)"]
    end

    subgraph USE["⑤ Deployment & reuse"]
        U1["Scarce-hazard detection<br/>on construction sites"]
        U2["Re-instantiate pipeline<br/>for other scarce targets<br/>(e.g., helmet non-use)"]
    end

    R2 --> L1
    R2 --> T2
    R2 -.-> G2
    G4 --> L2
    D1 --> T1
    E4 --> U1
    U1 -.-> U2
    U2 -.-> R1

    %% dashed = optional / later-stage connections
    %% ②-to-③ pipeline is the contribution: generation output is never
    %% used untagged -> auto-label -> 100% human review is the quality gate.
```

## 节点释义（写 Caption / Methodology 时用）

| 环节 | 实际做法 | 论文里的说法 |
|---|---|---|
| ① Real seed data | 93 张真实巡检照片人工标注（57 正 + 36 负） | small real seed set with expert annotation |
| ② Generative expansion | Z-Image-Turbo 文生图 + Qwen-Image-Edit 编辑真实照片（+canny ControlNet 试验）；垃圾/磨损/锈迹真实感红线 | diffusion-based synthesis with realism constraints |
| ③ Labeling loop | 打标模型预标注 → GUI 逐张人工复核（100% 复核率） | auto-labeling with human-in-the-loop verification |
| ④ Training & evaluation | 多检测器统一超参；93 张真实照片绝不参与训练与选型；双口径泄露感知报告 | leakage-aware protocol: clean real test, dual reporting |
| ⑤ Deployment & reuse | 工地危险目标检出；管线复用到下一稀缺目标（安全帽） | reusable augmentation recipe for scarce targets |

## Fig.1 英文 Caption 草稿（定稿时可改）

**Fig. 1.** Overview of the proposed pipeline. A small expert-annotated real seed set (①) drives a diffusion-based expansion stage (②) that synthesizes scarce hazardous-scenario images under realism constraints. Every generated image passes through an auto-labeling stage with human-in-the-loop verification (③) before entering training, yielding a reviewed synthetic dataset. Detectors are trained and evaluated under a leakage-aware protocol (④) in which real photos are never used for training, allowing the effect of generated-data quantity to be measured on clean real-world data. The recipe is designed to be re-instantiated for other scarce hazardous targets (⑤).

## TikZ 重绘提醒

- 建议布局：纵向四段（Seed → Generate → Review → Train/Eval），右侧竖排画 dashed 的 "reuse loop" 回到 Seed。
- 关键视觉对比：实线 = 主流程；虚线 = 可选/复用路径；把 "human review" 与 "clean real test" 两个质量门用同一种醒目标记（如盾牌/对勾底色框）。
- 图中不放具体数字（500/93 等），数字留给正文与表。
