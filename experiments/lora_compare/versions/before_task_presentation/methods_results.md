# Methods and final results

We evaluated 153 existing images across 16 LoRA settings and a no-LoRA baseline, with three prompts and three matched seeds per setting (n=9). The original hashed inputs, CLIP ViT-L/14 (224) preprocessing, fixed texts, and scores were preserved. CLIP-T was 100 times the cosine similarity of L2-normalized features; means and sample SDs used ddof=1.

Two real raters independently assessed all 153 anonymous images using LC-review-v3. Usability required both usability questions to pass; fail or uncertain counted as unusable while the original category was retained. Prompt compliance required all four binary questions to pass. Exact cylinder counts were excluded. Construction-photo realism was assessed separately as not realistic, somewhat realistic, or very realistic. Any item disagreement triggered adjudication: 110 images received real adjudication, and the remaining 43 retained agreed ratings. Machine-generated labels were not used. The two raters do not increase the number of independent images from 153 to 306.

The current step-1860 / strength-0.8 setting had CLIP-T 30.41 (SD 1.51), rank 2 among 16 LoRA settings. Final usability was 6/9 (tied ranks 2-6), prompt compliance was 4/9 (tied ranks 12-14), and realism counts were 2/1/6. Step-1860 / strength-0.2 had the highest observed usability (7/9), prompt compliance 6/9, and CLIP-T 29.58. The no-LoRA baseline had usability 6/9, prompt compliance 6/9, and CLIP-T 28.99 (SD 2.14). Step-1500 / strength-0.8 had the highest CLIP-T (30.76) but usability 4/9.

Original inter-rater exact agreement was 81.0% (Cohen kappa 0.613) for usability, 80.4% (kappa 0.599) for prompt compliance, and 52.3% (kappa 0.250) for three-category realism. Linear-weighted realism kappa was 0.337 as supplementary ordinal description. Agreement was measured before adjudication.

The existing setting is reasonable to retain for the D detector experiment, but these three prompts and nine images per setting do not establish overall optimality or noninferiority. The results do not show a uniform LoRA advantage over the baseline in task usability. Candidate confirmation should use new prompts and matched seeds; this analysis does not measure downstream detector benefit. Human rule amendments occurred after some trial images had been judged and are documented separately from the original automatic protocol. Original CLIP texts retain count wording although human counts are excluded.

## Final table

| Step | Strength | CLIP-T mean ± SD | All requirements met | Training usable |
|---|---|---|---|---|
| No LoRA | -- | 28.99 ± 2.14 | **6/9** | 6/9 |
| 500 | 0.2 | 28.65 ± 1.56 | 5/9 | 6/9 |
| 500 | 0.5 | 29.93 ± 2.37 | 5/9 | 4/9 |
| 500 | 0.8 | 30.22 ± 1.04 | 3/9 | 5/9 |
| 500 | 1.0 | 29.86 ± 1.59 | 3/9 | 3/9 |
| 1000 | 0.2 | 29.06 ± 1.53 | 5/9 | 6/9 |
| 1000 | 0.5 | 28.68 ± 2.51 | **6/9** | 6/9 |
| 1000 | 0.8 | 29.56 ± 2.60 | 4/9 | 3/9 |
| 1000 | 1.0 | 29.85 ± 2.07 | **6/9** | 3/9 |
| 1500 | 0.2 | 29.22 ± 1.68 | **6/9** | 6/9 |
| 1500 | 0.5 | 29.04 ± 2.67 | 5/9 | 5/9 |
| 1500 | 0.8 | **30.76 ± 2.02** | 5/9 | 4/9 |
| 1500 | 1.0 | 29.42 ± 1.67 | 4/9 | 2/9 |
| 1860 | 0.2 | 29.58 ± 1.72 | **6/9** | **7/9** |
| 1860 | 0.5 | 28.96 ± 3.43 | **6/9** | 5/9 |
| 1860 | 0.8 | 30.41 ± 1.51 | 4/9 | 6/9 |
| 1860 | 1.0 | 30.23 ± 1.62 | 5/9 | 3/9 |

## Figure caption

LoRA checkpoint and strength sensitivity on 153 existing images. Each setting has nine images (three prompts and three matched seeds). Human labels use two independent real raters with real adjudication of 110 disputed images; the remaining 43 use agreed ratings. CLIP-T is 100 times cosine similarity; SD is sample SD. Usability requires both usability items to pass; prompt compliance requires all four binary requirements to pass. Realism is reported separately in three ordered categories. Gray outlines identify the existing step-1860 / strength-0.8 setting, not a winning configuration.

For lora_final_evaluation, panels show (a) mean CLIP-T, (b) training-usable images, (c) images satisfying all four prompt requirements, and (d) images rated very realistic. Human counts are per nine images. All three realism categories are retained in the full table. For lora_parameter_sensitivity, qualitative panels retain the two fixed prompts and seed 99999; the full nine-page supplement retains all 17 settings for every prompt/seed pair.

## Table caption

CLIP-T mean and sample SD and adjudicated human outcomes over n=9 images per setting. Bold indicates the largest observed value within each column, including ties; it does not establish superiority. No-LoRA baseline is represented once.
