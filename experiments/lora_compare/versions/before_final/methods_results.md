# Methods and preliminary automatic results

We evaluated 153 existing images covering 16 LoRA settings (steps 500, 1000, 1500, 1860; strengths 0.2, 0.5, 0.8, 1.0) and one no-LoRA baseline. Every setting comprised three prompts and three matched seeds (n=9). PNG metadata were traced from the saved image to the active sampler, effective LoRA, text encoder, latent and VAE; sampling settings and prompt consistency were checked before scoring. The protocol and original images were hashed before evaluation. The alias of the base-model filename was confirmed by the author.

OpenAI CLIP ViT-L/14 (224) was evaluated in float32 with official image preprocessing. Evaluation texts were fixed short descriptions common to every setting; tokenizer lengths (including special tokens) were {'new150_010': 45, 'new24_001': 38, 'new24_010': 44}, with no truncation. Image and text embeddings were L2 normalized, and CLIP-T was computed as 100 times their cosine similarity. Means and sample SDs were computed over nine images per setting. Two independently ordered packages conceal configuration labels; actual human ratings and adjudication have not yet been collected. These two dimensions are pending, not zero.

The current step-1860/strength-0.8 setting had mean CLIP-T 30.4079 (SD 1.5086), rank 2-2 among the 16 LoRA settings. The baseline mean was 28.9924. Rank sensitivity by prompt, seed and prompt omission is reported separately. This result is limited to the three prompts, is descriptive, and neither establishes equivalence nor invalidates the existing D detector experiment. Human assessment is required before any combined interpretation of parameter suitability.

## Figure caption

Supplementary sensitivity analysis of LoRA checkpoint and strength. (a) Strength 0.8 at four training steps. (b) Step 1860 at four strengths, with the no-LoRA baseline. Both display panels use two fixed prompts and seed 99999, selected in the analysis plan after some images had been seen; full uncropped images are shown. (c) Mean CLIP-T similarity across three prompts and three seeds (n=9 per configuration); the baseline is reported once outside the heatmap. Gray outlines identify the configuration used for the D detector experiment, not a winning setting. CLIP-T = 100 times cosine similarity; SD in the table is sample SD (ddof=1). Human requirements and training-usability evaluation remain pending.

## Table caption

CLIP-T mean and sample SD over n=9 images per configuration. Human columns await actual reviewers. Bold identifies the best observed value within each completed dimension, including ties; it does not establish superiority. No-LoRA baseline is represented once.


## Human review amendment (2026-10-10)

The author requested LC-review-v2 after automatic CLIP computation and before any real human labels were imported. Usability questions are shortened and use item-specific reason choices; only Other requires free text. All images have exactly four binary prompt-related questions, excluding exact cylinder counts and explanation fields. The original automatic protocol, CLIP texts (including original count wording) and scores are unchanged; human rules are frozen separately in review_protocol.json. This amendment is not represented as part of the original pre-score protocol. Old sources and review packages are retained under versions/v1/. No real human scores have been generated or imported.


## 2026-10-11 人工评价修订（v3）

按作者在试评十几张后的要求，删除第一阶段边界题；保留气瓶正常与场景无重大缺陷两题，并新增“以工地照片的角度来看，你如何评价这张图的真实性”：不太真实、还算真实、很真实。真实性单独记录，不作为训练可用性的通过门槛。第二阶段仍为四道是非题。已评数据按作者要求舍去，新版从零评分，不导入 v1/v2 JSON。原自动评价不变，v2 规则和代码保存在 versions/v2。
