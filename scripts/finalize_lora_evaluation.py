"""Finalize tables, figures and conclusions from real adjudicated human labels.

This postprocessing step preserves the frozen automatic/human evaluation code.
"""
from collections import Counter
from pathlib import Path
import inspect
import itertools
import shutil
import statistics
import eval_lora_compare as e

OUT=e.OUT
DEST=OUT/'human_analysis'
REALISM=['not_realistic','somewhat_realistic','very_realistic']


def verify_final():
    e.frozen();protocol=e.review_protocol()
    mapping={r['blind_id']:r for r in e.csvread(OUT/'restricted/blind_mapping.csv')}
    raw={r:e.read(OUT/'restricted'/f'{r}_current.json') for r in ['R1','R2','ADJ']}
    for r,p in raw.items():
        e.validate_review(p,mapping,e.sha(OUT/'review_protocol.json'))
        assert all(e.review_complete(x) for x in p['records'])
    raters={r:{x['blind_id']:x for x in p['records']} for r,p in raw.items()}
    needed={bid for bid in mapping if any(raters['R1'][bid][k]!=raters['R2'][bid][k] for k in ['usability','requirements','realism'])}
    assert set(raters['ADJ'])==needed and raw['ADJ']['completed']==raw['ADJ']['total']==len(needed)==110
    final=e.read(OUT/'restricted/final_labels.json')
    assert set(final)=={m['image_id'] for m in mapping.values()} and len(final)==153
    chosen={}
    for bid,m in mapping.items():
        original=raters['ADJ'][bid] if bid in needed else raters['R1'][bid]
        actual=final[m['image_id']]
        assert all(actual[k]==original[k] for k in ['usability','requirements','realism'])
        assert actual['usable']==int(all(v=='pass' for v in original['usability']))
        assert actual['prompt_pass']==int(all(v=='pass' for v in original['requirements']))
        chosen[bid]=original
    assert e.sha(OUT/'clip_scores.csv')==protocol['clip_scores_sha256']
    summary=e.csvread(OUT/'summary.csv')
    assert len(summary)==17 and all(r['human_status']=='two_raters_adjudicated' for r in summary)
    for row in summary:
        ids=[bid for bid,m in mapping.items() if m['config']==row['config']]
        assert len(ids)==int(row['n'])==9
        assert sum(final[mapping[i]['image_id']]['usable'] for i in ids)==int(row['usable_n'])
        assert sum(final[mapping[i]['image_id']]['prompt_pass'] for i in ids)==int(row['prompt_pass_n'])
    return summary,final,mapping,chosen,raw


def archive_previous():
    directory=OUT/'versions/before_final';directory.mkdir(parents=True,exist_ok=True)
    for p in [OUT/'acceptance.json',OUT/'report.md',OUT/'methods_results.md',DEST/'report.md',e.FIGURES/'lora_parameter_sensitivity.pdf',e.FIGURES/'lora_parameter_sensitivity_supplement.pdf']:
        target=directory/('human_report.md' if p==DEST/'report.md' else p.name)
        if p.exists() and not target.exists():shutil.copy2(p,target)


def figures(summary,rows):
    # Retain the frozen qualitative layout and all original selected images.
    # Only its completion annotations change in this final presentation step.
    source=inspect.getsource(e.make_figures)
    source=source.replace('Human assessment pending:\\nrequirements and training usability.','Human assessment complete:\\n2 raters + adjudication.\\nCurrent setting: usable 6/9;\\nrequirements met 4/9.')
    source=source.replace('Human assessment pending.','Human assessment complete.\\n2 raters + adjudication.')
    scope=dict(e.__dict__);exec(compile(source,str(Path(__file__))+'::final_annotations','exec'),scope)
    scope['make_figures'](summary,rows)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
    by={s['config']:s for s in summary}
    final=e.read(OUT/'restricted/final_labels.json')
    manifest=e.csvread(OUT/'manifest.csv')
    very={c:sum(final[r['image_id']]['realism']=='very_realistic' for r in manifest if r['config']==c) for c in e.CONFIGS}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'svg.fonttype':'path'})
    fig,axes=plt.subplots(2,2,figsize=(7.1,7),layout='constrained')
    panels=[('clip_t_mean','(a) CLIP-T mean','cividis',None),('usable_n','(b) Training usable','Blues',(0,9)),('prompt_pass_n','(c) All four requirements met','Blues',(0,9)),('very','(d) Rated very realistic','Blues',(0,9))]
    for ax,(field,title,cmap,limits) in zip(axes.flat,panels):
        get=lambda c:very[c] if field=='very' else float(by[c][field])
        values=np.array([[get(f'{s}-{v:.1f}') for v in e.STRENGTHS] for s in e.STEPS])
        low,high=(float(values.min()),float(values.max())) if limits is None else limits
        im=ax.imshow(values,cmap=cmap,vmin=low,vmax=high)
        ax.set_xticks(range(4),[str(v) for v in e.STRENGTHS]);ax.set_yticks(range(4),[str(s) for s in e.STEPS])
        ax.set_xlabel('LoRA strength');ax.set_ylabel('Training step');ax.set_title(title,loc='left',weight='bold',pad=24)
        base=f'{get("no-lora"):.2f}' if field=='clip_t_mean' else f'{int(get("no-lora"))}/9'
        ax.text(0,1.04,'No-LoRA baseline: '+base,transform=ax.transAxes,fontsize=8)
        for i,j in itertools.product(range(4),repeat=2):
            rgb=im.cmap(im.norm(values[i,j]));lum=.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]
            value=f'{values[i,j]:.2f}' if field=='clip_t_mean' else f'{int(values[i,j])}/9'
            ax.text(j,i,value,ha='center',va='center',color='black' if lum>.5 else 'white',fontsize=9)
        ax.add_patch(Rectangle((1.5,2.5),1,1,fill=False,edgecolor='#858585',linewidth=1.5))
        bar=fig.colorbar(im,ax=ax,fraction=.043,pad=.04)
        if limits:bar.set_ticks([0,3,6,9])
    fig.suptitle('LoRA parameter evaluation | n = 9 images per setting\nHuman ratings: two independent raters, then real adjudication',fontsize=10)
    fig.supxlabel('Gray outline: existing step-1860 / strength-0.8 setting; not a winner label.',fontsize=7)
    for ext in ['pdf','svg','png']:fig.savefig(e.FIGURES/f'lora_final_evaluation.{ext}',dpi=300)
    plt.close(fig)


def main():
    summary,final,mapping,chosen,raw=verify_final();archive_previous()
    table=e.manuscript_tables(summary)
    e_table=e.ROOT/'paper/tables/lora_parameter_sensitivity.tex'
    tex=e_table.read_text(encoding='utf-8').replace('human fields pending until real reviews.','human fields are final labels from two real raters and adjudication.')
    e_table.write_text(tex,encoding='utf-8')
    by={r['config']:r for r in summary};ref=by[e.REFERENCE];baseline=by['no-lora']
    summaries=[]
    for row in summary:
        labels=[x for image,x in final.items() if image in {m['image_id'] for m in mapping.values() if m['config']==row['config']}]
        counts={v:sum(x['realism']==v for x in labels) for v in REALISM}
        ranks={field:e.rank_range({s['config']:float(s[field]) for s in summary if s['config']!='no-lora'},row['config'],tol=1e-6 if field=='clip_t_mean' else 0) if row['config']!='no-lora' else None for field in ['clip_t_mean','usable_n','prompt_pass_n']}
        summaries.append(dict(row,realism=counts,ranks=ranks))
    reference=next(s for s in summaries if s['config']==e.REFERENCE)
    stratified=[]
    for c,p in itertools.product(e.CONFIGS,e.PROMPTS):
        selected=[final[m['image_id']] for m in mapping.values() if m['config']==c and m['prompt_id']==p]
        stratified.append(dict(config=c,prompt_id=p,n=3,usable=sum(x['usable'] for x in selected),prompt_pass=sum(x['prompt_pass'] for x in selected),realism={v:sum(x['realism']==v for x in selected) for v in REALISM},requirements_pass=[sum(x['requirements'][i]=='pass' for x in selected) for i in range(4)]))
    provenance=dict(completed_at=e.now(),status='complete',human_status='two_raters_adjudicated',original_protocol_sha256=e.sha(OUT/'protocol.json'),human_protocol_sha256=e.sha(OUT/'review_protocol.json'),clip_scores_sha256=e.sha(OUT/'clip_scores.csv'),analysis_code_sha256=e.sha(__file__),
                    input_exports={p.name:e.sha(p) for p in (OUT/'review').glob('anonymous*.json')},human_records={r:e.sha(OUT/'restricted'/f'{r}_current.json') for r in raw})
    by_seed=[]
    for c,seed in itertools.product(e.CONFIGS,e.SEEDS):
        selected=[final[m['image_id']] for m in mapping.values() if m['config']==c and int(m['seed'])==seed]
        by_seed.append(dict(config=c,seed=seed,n=3,usable=sum(x['usable'] for x in selected),prompt_pass=sum(x['prompt_pass'] for x in selected),realism={v:sum(x['realism']==v for x in selected) for v in REALISM}))
    e.write(DEST/'final_results.json',dict(provenance=provenance,summary=summaries,by_prompt=stratified,by_seed=by_seed,n_images=153,n_raters=2,n_adjudicated_images=110,totals={field:sum(x[field] for x in final.values()) for field in ['usable','prompt_pass']},realism_totals={v:sum(x['realism']==v for x in final.values()) for v in REALISM}))
    strength=[]
    for v in e.STRENGTHS:
        members=[s for s in summaries if s['config']!='no-lora' and float(s['strength'])==v]
        strength.append(dict(strength=v,n=36,usable=sum(int(s['usable_n']) for s in members),prompt=sum(int(s['prompt_pass_n']) for s in members)))
    agreement=e.read(DEST/'results.json')['agreement']
    rank=lambda pair:str(pair[0]) if pair[0]==pair[1] else f'{pair[0]}–{pair[1]}'
    realism_text=lambda s:' / '.join(str(s['realism'][v]) for v in REALISM)
    lines=['# LoRA 最终评价：自动分数、双人评审及人工裁决',f'完成时间：{e.now()}（北京时间）。状态：全部完成。',
           '两位真实评分者各完成 153 张，110 张至少一个项目存在分歧并已完成人工裁决；其余 43 张采用双方一致的评分。最终分析仍为 153 张图，每配置 9 张（3 提示词 × 3 seed），不是 306 张独立样本。机器没有补充任何人工标签。',
           '## 最终结论',
           '**现用 1860 / 0.8 可以继续作为既有 D 臂的给定配置；它的 CLIP 表现较高、训练可用性处于本次样本中的较高组，但不能称为综合最优或已证明近优。**',
           f'- 当前配置 CLIP-T 为 **{float(ref["clip_t_mean"]):.2f} ± {float(ref["clip_t_sd"]):.2f}**，在 16 个 LoRA 配置中排名 **{rank(reference["ranks"]["clip_t_mean"])}**。',
           f'- 最终训练可用 **{ref["usable_n"]}/9（66.7%）**，在 LoRA 配置中并列 **{rank(reference["ranks"]["usable_n"])}**；提示词四项全部满足 **{ref["prompt_pass_n"]}/9（44.4%）**，并列 **{rank(reference["ranks"]["prompt_pass_n"])}**。',
           f'- 当前配置真实性“不太真实 / 还算真实 / 很真实”为 **{realism_text(reference)}**，很真实为 6/9。此三档指标独立报告，不转成训练可用的通过门槛。',
           '- 当前配置被判为“很真实”的图片为 **6/9**，无 LoRA 基线为 **1/9**。本次样本显示了较好的照片真实性表现，但这种描述性差异不等于训练可用数或 detector 收益的提高。',
           '- 训练可用数最高为 **1860 / 0.2：7/9**；它的提示词全部满足为 **6/9**，CLIP-T 为 **29.58**。若优先考虑目标检测训练数据的任务可用性，这是下一轮独立确认的合理候选。它只比当前配置多一张可用图，不能据此认定存在稳定优势。',
           '- CLIP 最高为 **1500 / 0.8：30.76 ± 2.02**，但训练可用仅 **4/9**。CLIP-T 排名不能直接代替训练可用性判断。',
           '- 无 LoRA 基线训练可用 **6/9**、提示词全部满足 **6/9**、CLIP-T **28.99 ± 2.14**。当前配置相对基线 CLIP 高 1.42，但训练可用数相同，提示词全部满足少两张；本次数据**不支持 LoRA 全面提高任务可用性**。',
           '- 不需要仅凭这次小样本参数比较重训已有 D 臂，也不把这次结果宣称为 detector 收益或正式受控消融。若进一步选参，应使用新提示词与匹配 seed，对当前配置、1860 / 0.2、无 LoRA 进行独立确认。',
           '## 17 个配置的最终主表',
           '人工数为裁决后的最终标签，分母均为 9；真实性按“不太真实 / 还算真实 / 很真实”列出。配置固定排序，不合成任意权重总分。',
           '| 配置 | CLIP-T 均值 ± SD | 训练可用 | 提示词全部满足 | 三档真实性 |','|---|---:|---:|---:|---:|']
    for s in summaries:lines.append(f'| {s["config"]} | {float(s["clip_t_mean"]):.2f} ± {float(s["clip_t_sd"]):.2f} | {s["usable_n"]}/9 | {s["prompt_pass_n"]}/9 | {realism_text(s)} |')
    lines+=['## 当前配置与对照的匹配比较','差值方向为“当前 1860 / 0.8 减对照”，逐图按提示词与 seed 匹配，每对照 n=9。人工净差是描述性图数差，不是显著性或非劣检验。',
            '| 对照 | CLIP 均值差 | 训练可用图数差 | 提示词全部满足图数差 |','|---|---:|---:|---:|']
    for c in ['no-lora','1860-0.2','1500-0.8']:
        r=by[c];lines.append(f'| {c} | {float(ref["clip_t_mean"])-float(r["clip_t_mean"]):+.2f} | {int(ref["usable_n"])-int(r["usable_n"]):+d} | {int(ref["prompt_pass_n"])-int(r["prompt_pass_n"]):+d} |')
    lines+=['## 场景与强度的差异','当前 1860 / 0.8 的逐场景最终结果：','| 提示词 | 训练可用 | 提示词全部满足 | 三档真实性 |','|---|---:|---:|---:|']
    for s in stratified:
        if s['config']==e.REFERENCE:lines.append(f'| {s["prompt_id"]} | {s["usable"]}/3 | {s["prompt_pass"]}/3 | {realism_text(s)} |')
    lines+=['按强度合并四个 checkpoint（每强度 36 张），作为共享场景下的描述性汇总：','| 强度 | 训练可用 | 提示词全部满足 |','|---|---:|---:|']
    for s in strength:lines.append(f'| {s["strength"]} | {s["usable"]}/36 | {s["prompt"]}/36 |')
    lines+=['较高强度不意味着较高任务可用性；强度 1.0 在本次样本中训练可用数最低。此趋势不是独立因果估计。',
            '## 双人原始评分一致性','一致性使用人工裁决前的原始评分计算，不能用裁决后的一致结果代替评分者间一致性。',
            '| 指标 | 原始一致率 | Cohen κ |','|---|---:|---:|']
    for k,title in [('usability','训练可用'),('requirements','提示词全部满足'),('realism','三档真实性')]:
        a=agreement[k];lines.append(f'| {title} | {a["exact_agreement"]:.1%} | {a["kappa"]:.3f} |')
    lines+= [f'真实性线性加权 κ 为 {agreement["realism_linear_weighted"]["kappa"]:.3f}，作为 v3 新增三档指标的补充描述。原始评分按项分歧：可用性 64 张、提示词 39 张、真实性 73 张；互有重叠，共 110 张进入裁决。',
             '## 方法、溯源与解释边界',
             'CLIP 为原冻结 OpenAI ViT-L/14（224），CLIP-T=100×L2 归一化图像/文本特征的余弦相似度；均值及样本 SD（ddof=1）按每配置 9 张计算。原 CLIP 分数、输入图片和评价协议未改。',
             '训练可用需两项均 pass，任一 fail 或 uncertain 均记 0，同时保留原始 uncertain。提示词符合需四道二选一题均 pass。不评价具体气瓶数量。真实性独立三档，不与前两指标合成总分。CLIP 文本仍含原数量措辞，因此人工与 CLIP 的评价口径并非完全一致。',
             'v3 人评修订发生在作者试评十几张后；旧评分按作者要求舍去。图片配置标签匿名，不能声称作者从未见过数据。每个配置只有 9 图、3 提示词；两名评分者和一次裁决不增加独立图片样本数。',
             '本报告为上述三条提示词范围的补充参数敏感性评价。误差条重叠、p>0.05、任意百分比阈值均不能证明等效/非劣；本任务没有运行或重训 detector。',
             '## 产物',
             '- summary.csv / summary.md 与 paper/tables/lora_parameter_sensitivity.tex：最终主表。',
             '- human_analysis/final_results.json：最终三档真实性、逐提示词与逐要求结果，以及来源哈希。',
             '- reference_comparison.csv / matched_differences.csv / reference_rank_sensitivity.csv：匹配计数、CLIP 差值和原场景/seed 敏感性。',
             '- human_analysis/results.json：双方原始评分及一致性、分层数据；restricted/raw/ 保留实际导入原件，final_labels.json 保存 153 张最终标签。',
             '- paper/figures/lora_compare/lora_final_evaluation.pdf / .svg / .png：CLIP 与三个裁决后人工指标的四面板图。原图像对照与完整九页网格已更新完成人工评价标识。',
             '评价已完成，无剩余评分或裁决。']
    markdown=''
    for i,line in enumerate(lines):markdown+= ('\n' if i and line.startswith('|') and lines[i-1].startswith('|') else '\n\n' if i else '')+line
    for p in [DEST/'report.md',OUT/'report.md']:p.write_text(markdown+'\n',encoding='utf-8')
    caption='LoRA checkpoint and strength sensitivity on 153 existing images. Each setting has nine images (three prompts and three matched seeds). Human labels use two independent real raters with real adjudication of 110 disputed images; the remaining 43 use agreed ratings. CLIP-T is 100 times cosine similarity; SD is sample SD. Usability requires both usability items to pass; prompt compliance requires all four binary requirements to pass. Realism is reported separately in three ordered categories. Gray outlines identify the existing step-1860 / strength-0.8 setting, not a winning configuration.'
    methods=f'''# Methods and final results

We evaluated 153 existing images across 16 LoRA settings and a no-LoRA baseline, with three prompts and three matched seeds per setting (n=9). The original hashed inputs, CLIP ViT-L/14 (224) preprocessing, fixed texts, and scores were preserved. CLIP-T was 100 times the cosine similarity of L2-normalized features; means and sample SDs used ddof=1.

Two real raters independently assessed all 153 anonymous images using LC-review-v3. Usability required both usability questions to pass; fail or uncertain counted as unusable while the original category was retained. Prompt compliance required all four binary questions to pass. Exact cylinder counts were excluded. Construction-photo realism was assessed separately as not realistic, somewhat realistic, or very realistic. Any item disagreement triggered adjudication: 110 images received real adjudication, and the remaining 43 retained agreed ratings. Machine-generated labels were not used. The two raters do not increase the number of independent images from 153 to 306.

The current step-1860 / strength-0.8 setting had CLIP-T {float(ref['clip_t_mean']):.2f} (SD {float(ref['clip_t_sd']):.2f}), rank 2 among 16 LoRA settings. Final usability was 6/9 (tied ranks 2-6), prompt compliance was 4/9 (tied ranks 12-14), and realism counts were 2/1/6. Step-1860 / strength-0.2 had the highest observed usability (7/9), prompt compliance 6/9, and CLIP-T 29.58. The no-LoRA baseline had usability 6/9, prompt compliance 6/9, and CLIP-T 28.99 (SD 2.14). Step-1500 / strength-0.8 had the highest CLIP-T (30.76) but usability 4/9.

Original inter-rater exact agreement was 81.0% (Cohen kappa 0.613) for usability, 80.4% (kappa 0.599) for prompt compliance, and 52.3% (kappa 0.250) for three-category realism. Linear-weighted realism kappa was 0.337 as supplementary ordinal description. Agreement was measured before adjudication.

The existing setting is reasonable to retain for the D detector experiment, but these three prompts and nine images per setting do not establish overall optimality or noninferiority. The results do not show a uniform LoRA advantage over the baseline in task usability. Candidate confirmation should use new prompts and matched seeds; this analysis does not measure downstream detector benefit. Human rule amendments occurred after some trial images had been judged and are documented separately from the original automatic protocol. Original CLIP texts retain count wording although human counts are excluded.

## Final table

{table}

## Figure caption

{caption}

For lora_final_evaluation, panels show (a) mean CLIP-T, (b) training-usable images, (c) images satisfying all four prompt requirements, and (d) images rated very realistic. Human counts are per nine images. All three realism categories are retained in the full table. For lora_parameter_sensitivity, qualitative panels retain the two fixed prompts and seed 99999; the full nine-page supplement retains all 17 settings for every prompt/seed pair.

## Table caption

CLIP-T mean and sample SD and adjudicated human outcomes over n=9 images per setting. Bold indicates the largest observed value within each column, including ties; it does not establish superiority. No-LoRA baseline is represented once.
'''
    (OUT/'methods_results.md').write_text(methods,encoding='utf-8')
    figures(summary,e.csvread(OUT/'manifest.csv'))
    e.state('complete',human_status='two_raters_adjudicated',final_report_completed_at=e.now(),human_review_images=153,adjudicated_images=110,remaining_adjudication_images=0)
    print('Final reports, table and figures generated; current setting usable 6/9, requirements 4/9')


if __name__=='__main__':main()
