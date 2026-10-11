# LoRA parameter evaluation: automatic stage complete

Prepared and evaluated 2026-10-10T19:26:07.222695+08:00 (UTC+8). CLIP is complete for all 153 images. Human requirements and training-usability assessments are pending. No human score was inferred.

17 configurations, each n=9 (three prompts x three matched seeds). Current setting step 1860 / strength 0.8: CLIP-T 30.4079 +/- 1.5086 (sample SD), descriptive rank 2-2 among 16 LoRA settings. No-LoRA baseline 28.9924 +/- 2.1395, reported separately.

This report and configured figures must not be distributed to human raters before scoring. Give each rater only review/R1 or review/R2, respectively.

## Human handoff

Open review/R1/index.html and review/R2/index.html in Chrome or Edge. Each rater independently reviews 153 images under LC-review-v3. Complete two short training-usability questions and one separate three-level realism rating, selecting item-specific reasons for fail/uncertain; text is required only for Other. Then answer exactly four binary prompt-related questions. Cylinder counts and second-stage explanations are not collected. Click the image to enlarge. Download JSON at the end of each session; local saving is a convenience. V1 exports are retained separately and cannot be imported as V2. Submit the completed JSON files to the author. One actual rater is allowed with explicit single-rater reporting.

Continue with: `.venv/Scripts/python.exe scripts/eval_lora_compare.py import-review PATH_TO_JSON`, then `aggregate`. Original imports are retained. If disagreements exist, only the disputed IDs wait for human adjudication. `report` can then rebuild the final table and figures.

## Automatic table (human cells pending)

| Step | Strength | CLIP-T mean ± SD | All requirements met | Training usable |
|---|---|---|---|---|
| No LoRA | -- | 28.99 ± 2.14 | pending | pending |
| 500 | 0.2 | 28.65 ± 1.56 | pending | pending |
| 500 | 0.5 | 29.93 ± 2.37 | pending | pending |
| 500 | 0.8 | 30.22 ± 1.04 | pending | pending |
| 500 | 1.0 | 29.86 ± 1.59 | pending | pending |
| 1000 | 0.2 | 29.06 ± 1.53 | pending | pending |
| 1000 | 0.5 | 28.68 ± 2.51 | pending | pending |
| 1000 | 0.8 | 29.56 ± 2.60 | pending | pending |
| 1000 | 1.0 | 29.85 ± 2.07 | pending | pending |
| 1500 | 0.2 | 29.22 ± 1.68 | pending | pending |
| 1500 | 0.5 | 29.04 ± 2.67 | pending | pending |
| 1500 | 0.8 | **30.76 ± 2.02** | pending | pending |
| 1500 | 1.0 | 29.42 ± 1.67 | pending | pending |
| 1860 | 0.2 | 29.58 ± 1.72 | pending | pending |
| 1860 | 0.5 | 28.96 ± 3.43 | pending | pending |
| 1860 | 0.8 | 30.41 ± 1.51 | pending | pending |
| 1860 | 1.0 | 30.23 ± 1.62 | pending | pending |

## Rank sensitivity

- overall: rank 2-2, mean 30.4079, n=9.
- prompt:new150_010: rank 3-3, mean 30.7138, n=3.
- prompt:new24_001: rank 7-7, mean 28.8432, n=3.
- prompt:new24_010: rank 1-1, mean 31.6668, n=3.
- seed:99999: rank 3-3, mean 29.7010, n=3.
- seed:88888: rank 2-2, mean 30.2807, n=3.
- seed:77777: rank 4-4, mean 31.2421, n=3.
- leave_out:new150_010: rank 2-2, mean 30.2550, n=6.
- leave_out:new24_001: rank 2-2, mean 31.1903, n=6.
- leave_out:new24_010: rank 4-4, mean 29.7785, n=6.

## Interpretation limits

Only these three prompts and nine images/configuration support this descriptive comparison. CLIP uses a center crop while raters see full images. The SD is not an SE or confidence interval. Ranking ties within 1e-6 are numerical ties, not evidence of equivalence. The prompts are shared across configurations. Seed and leave-one-prompt-out summaries reuse the same observations. These data do not support a strong noninferiority claim or independently select the best setting for detector training. This is a supplementary sensitivity analysis planned before computing scores, with some images already seen; it is not a generation preregistration. The base-model alias is author-confirmed, not dual-file hash verification. Detector results remain those for the existing D configuration.

For independent confirmation, choose a candidate after reporting all three dimensions, collect new prompts and matched seeds, and specify a task-grounded margin, primary endpoint and sample-size calculation before scoring. No generation or detector retraining was started here.

## Reproduction and sources

Official OpenAI CLIP ViT-L/14 (224), commit `d05afc436d78f1c48dc0dbf8e5980a9d471f35f6`, model SHA256 `b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836`. Float32 on cuda; formula 100 times cosine of L2-normalized features; no softmax or logit scale.

[OpenAI CLIP implementation](https://github.com/openai/CLIP/blob/d05afc436d78f1c48dc0dbf8e5980a9d471f35f6/clip/clip.py). Input, protocol, source, model and result hashes are recorded. All input file hashes are rechecked after evaluation.


## Human review amendment (2026-10-10)

The author requested LC-review-v2 after automatic CLIP computation and before any real human labels were imported. Usability questions are shortened and use item-specific reason choices; only Other requires free text. All images have exactly four binary prompt-related questions, excluding exact cylinder counts and explanation fields. The original automatic protocol, CLIP texts (including original count wording) and scores are unchanged; human rules are frozen separately in review_protocol.json. This amendment is not represented as part of the original pre-score protocol. Old sources and review packages are retained under versions/v1/. No real human scores have been generated or imported.


## 2026-10-11 人工评价修订（v3）

按作者在试评十几张后的要求，删除第一阶段边界题；保留气瓶正常与场景无重大缺陷两题，并新增“以工地照片的角度来看，你如何评价这张图的真实性”：不太真实、还算真实、很真实。真实性单独记录，不作为训练可用性的通过门槛。第二阶段仍为四道是非题。已评数据按作者要求舍去，新版从零评分，不导入 v1/v2 JSON。原自动评价不变，v2 规则和代码保存在 versions/v2。
