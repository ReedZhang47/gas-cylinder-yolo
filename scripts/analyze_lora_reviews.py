"""Summarize real LC-review-v3 ratings without inventing adjudicated labels.

Run after import-review. Optional --adjudication imports a real ADJ export,
then executes the original frozen aggregation. Automatic CLIP is never rerun.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
import eval_lora_compare as e

DEST=e.OUT/'human_analysis'
REALISM={x['code']:x['label'] for x in e.REALISM_OPTIONS}
VALUES=list(REALISM)
LABEL={'pass':'通过','fail':'不通过','uncertain':'不确定'}


def agreement(a,b,categories,weighted=False):
    n=len(a);assert n==len(b) and n
    ca,cb=Counter(a),Counter(b)
    if weighted:
        weight=lambda x,y:abs(categories.index(x)-categories.index(y))/(len(categories)-1)
        observed=sum(weight(x,y) for x,y in zip(a,b))/n
        expected=sum(ca[x]*cb[y]*weight(x,y) for x in categories for y in categories)/n**2
        kappa=None if not expected else 1-observed/expected
    else:
        observed=sum(x==y for x,y in zip(a,b))/n
        expected=sum(ca[x]*cb[x] for x in categories)/n**2
        kappa=None if len(ca)==1 or len(cb)==1 or expected==1 else (observed-expected)/(1-expected)
    return dict(n=n,exact_agreement=sum(x==y for x,y in zip(a,b))/n,kappa=kappa,
                weighting='linear ordinal' if weighted else 'unweighted',
                confusion={str(x):{str(y):sum(u==x and v==y for u,v in zip(a,b)) for y in categories} for x in categories})


def describe(records,ids):
    return dict(n=len(ids),usable=sum(e.all_pass(records[i]['usability']) for i in ids),
                prompt_pass=sum(e.all_pass(records[i]['requirements']) for i in ids),
                usability_items=[dict(Counter(records[i]['usability'][j] for i in ids)) for j in range(2)],
                requirement_items=[dict(Counter(records[i]['requirements'][j] for i in ids)) for j in range(4)],
                realism={v:sum(records[i]['realism']==v for i in ids) for v in VALUES},
                reasons=[dict(Counter(c for i in ids for c in records[i]['usability_reasons'][j])) for j in range(2)])


def make_adjudication(mapping,raters,disagreements,human):
    target=e.OUT/'review/ADJ';target.mkdir(parents=True,exist_ok=True)
    (target/'images').mkdir(exist_ok=True)
    items=[]
    for item in disagreements:
        bid=item['blind_id'];m=mapping[bid]
        source=e.OUT/'review/R1/images'/f'{bid}.png';dest=target/'images'/source.name
        if not dest.exists():shutil.copy2(source,dest)
        items.append(dict(id=bid,image=f'images/{bid}.png',checks=human['prompt_checks'][m['prompt_id']],R1=raters['R1'][bid],R2=raters['R2'][bid]))
    payload=dict(rule=e.REVIEW_RULE,protocol=e.sha(e.OUT/'review_protocol.json'),items=items,
                 usability=e.USABLE_CHECKS,reasonOptions=e.REASON_OPTIONS,realismOptions=e.REALISM_OPTIONS,realismQuestion=e.REALISM_QUESTION)
    template=Path(__file__).with_name('lora_adjudication.html').read_text(encoding='utf-8')
    (target/'index.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')),encoding='utf-8')
    (target/'README.txt').write_text('这是分歧裁决页，只有匿名图片和双方原始判断，无模型配置或自动分数。\n逐图选择最终判断；可点击采用 R1/R2 整张答案，再按项修改，确认后才计入完成。原始判断仍保留。\n前两题非通过需原因，真实性三选一；四道提示词题二选一。相同项预填，不同项留空。\n每次结束下载 JSON 备份，完成后交回 anonymous_adjudication_v3.json；不需要重评无分歧图片。\n',encoding='utf-8')


def analyze():
    _,rows=e.frozen();human=e.review_protocol()
    DEST.mkdir(exist_ok=True)
    mapping={r['blind_id']:r for r in e.csvread(e.OUT/'restricted/blind_mapping.csv')}
    raters={}
    for name in ['R1','R2']:
        data=e.read(e.OUT/'restricted'/f'{name}_current.json')
        e.validate_review(data,mapping,e.sha(e.OUT/'review_protocol.json'))
        rec={r['blind_id']:r for r in data['records']}
        assert set(rec)==set(mapping) and all(e.review_complete(x) for x in rec.values())
        assert data['completed']==153 and data['total']==153
        raters[name]=rec
    final,status=e.human_results()
    disagreements=e.read(e.OUT/'restricted/disagreements.json')
    scores=e.csvread(e.OUT/'clip_scores.csv');summary=[]
    for c in e.CONFIGS:
        ids=[bid for bid,m in mapping.items() if m['config']==c]
        clip=[float(s['clip_t']) for s in scores if s['config']==c]
        item=dict(config=c,n=9,clip_mean=statistics.mean(clip),clip_sd=statistics.stdev(clip),
                  **{r:describe(raters[r],ids) for r in raters})
        if final:
            labels=[final[mapping[i]['image_id']] for i in ids]
            item['adjudicated']=dict(usable=sum(x['usable'] for x in labels),prompt_pass=sum(x['prompt_pass'] for x in labels),
                                    realism={v:sum(x['realism']==v for x in labels) for v in VALUES})
        summary.append(item)
    clip_ranks={c:e.rank_range({s['config']:s['clip_mean'] for s in summary if s['config']!='no-lora'},c) for c in e.CONFIGS[1:]}
    comparisons={r:{field:{c:e.rank_range({s['config']:s[r][field] for s in summary if s['config']!='no-lora'},c,tol=0) for c in e.CONFIGS[1:]} for field in ['usable','prompt_pass']} for r in raters}
    ids=list(mapping);metrics={}
    for field in ['usability','requirements']:
        metrics[field]=agreement([e.all_pass(raters['R1'][i][field]) for i in ids],[e.all_pass(raters['R2'][i][field]) for i in ids],[0,1])
    for j in range(2):metrics[f'usability_{j+1}']=agreement([raters['R1'][i]['usability'][j] for i in ids],[raters['R2'][i]['usability'][j] for i in ids],['pass','fail','uncertain'])
    for j in range(4):metrics[f'requirements_{j+1}']=agreement([raters['R1'][i]['requirements'][j] for i in ids],[raters['R2'][i]['requirements'][j] for i in ids],['pass','fail'])
    metrics['realism']=agreement([raters['R1'][i]['realism'] for i in ids],[raters['R2'][i]['realism'] for i in ids],VALUES)
    metrics['realism_linear_weighted']=agreement([raters['R1'][i]['realism'] for i in ids],[raters['R2'][i]['realism'] for i in ids],VALUES,True)
    stratified={p:{c:{r:describe(raters[r],[bid for bid,m in mapping.items() if m['prompt_id']==p and m['config']==c]) for r in raters} for c in e.CONFIGS} for p in e.PROMPTS}
    seed_summary={str(seed):{c:{r:describe(raters[r],[bid for bid,m in mapping.items() if int(m['seed'])==seed and m['config']==c]) for r in raters} for c in e.CONFIGS} for seed in e.SEEDS}
    for r in raters:
        total=describe(raters[r],ids)
        assert sum(s[r]['n'] for s in summary)==153
        for field in ['usable','prompt_pass']:
            assert sum(s[r][field] for s in summary)==total[field]
        for v in VALUES:
            assert sum(s[r]['realism'][v] for s in summary)==total['realism'][v]
        assert all(sum(s[r]['realism'].values())==9 for s in summary)
    provenance=dict(created_at=e.now(),status=status,analysis_script_sha256=e.sha(__file__),
                    automatic_protocol_sha256=e.sha(e.OUT/'protocol.json'),human_protocol_sha256=e.sha(e.OUT/'review_protocol.json'),
                    clip_scores_sha256=e.sha(e.OUT/'clip_scores.csv'),
                    reviews={r:e.sha(e.OUT/'restricted'/f'{r}_current.json') for r in raters},
                    description='Original frozen endpoints retained. Per-rater and ordinal descriptions are supplementary; no synthesized human labels or composite winner.')
    e.write(DEST/'results.json',dict(provenance=provenance,summary=summary,agreement=metrics,rankings= comparisons,clip_rankings=clip_ranks,by_prompt=stratified,by_seed=seed_summary))
    make_adjudication(mapping,raters,disagreements,human)
    rank=lambda pair: str(pair[0]) if pair[0]==pair[1] else f'{pair[0]}–{pair[1]}'
    ref=next(x for x in summary if x['config']==e.REFERENCE)
    text=['# LoRA 自动评价与双人评审综合报告',f'生成时间：{e.now()}。当前状态：'+('人工裁决已完成。' if final else f'双人原始评价已完成；{len(disagreements)} 张分歧图片仍待真实人工裁决。'),
          '\n两名真实评分者各评价 153 张，共 306 次图片评价。每个配置仍只有 9 张独立图片（3 提示词 × 3 seed），评分者人数不增加图片样本数。气瓶数量不属于人工评价指标。',
          '\n## 可以直接得出的结论',
          f'- 当前使用的 **1860 / 0.8** 的 CLIP-T 为 **{ref["clip_mean"]:.2f} ± {ref["clip_sd"]:.2f}**，在 16 个 LoRA 配置中排名 **{rank(clip_ranks[e.REFERENCE])}**。',
          '- 两位评分者均认为当前配置有 **6/9 张可用于训练**。两人分别将其排在训练可用性 **'+rank(comparisons['R1']['usable'][e.REFERENCE])+'** 与 **'+rank(comparisons['R2']['usable'][e.REFERENCE])+'** 的并列范围，不能写成明确的单一名次。',
          '- 当前配置提示词四项全部满足为 **R1 6/9、R2 3/9**；真实性“不太真实/还算真实/很真实”分别为 **'+ '/'.join(str(ref['R1']['realism'][v]) for v in VALUES)+'** 与 **'+ '/'.join(str(ref['R2']['realism'][v]) for v in VALUES)+'**。提示词和真实性判断仍受评分者分歧影响。',
          '- **现有数据支持继续保留 1860 / 0.8 作为已有 D 臂的给定配置，但不足以称其为综合最优或已证明近优。** CLIP 排名较高，训练可用性没有明确优势；无需仅凭这次小样本描述重训既有 D 臂。',
          '- 无 LoRA 的 CLIP-T 为 28.99，训练可用分别为 6/9、8/9，提示词全部满足为 6/9、7/9。这三条提示词的数据尚不能支持“LoRA 已全面提升生成图的任务可用性”。',
          '- CLIP 最优为 1500 / 0.8（30.76），但训练可用仅 4/9、5/9；自动文本相似度最高没有转化为最高训练可用性。',
          '- 两位评分者下，强度 1.0 的训练可用数普遍偏低。若开展独立确认实验，可把 1860 / 0.2、1000 / 0.2 和无 LoRA 作为任务可用性的对照，1500 / 0.8 作为 CLIP 对照；这些是观察后的候选，仍需新提示词验证。',
          '\n## 17 个配置的完整结果',
          '人工列显示 R1 / R2；分母均为 9。保留固定配置顺序，不合成任意加权总分。',
          '| 配置（步数 / 强度） | CLIP-T 均值 ± SD | 训练可用 R1/R2 | 提示词全部满足 R1/R2 | 很真实 R1/R2 |',
          '|---|---:|---:|---:|---:|']
    for s in summary:text.append(f'| {s["config"]} | {s["clip_mean"]:.2f} ± {s["clip_sd"]:.2f} | {s["R1"]["usable"]}/9 · {s["R2"]["usable"]}/9 | {s["R1"]["prompt_pass"]}/9 · {s["R2"]["prompt_pass"]}/9 | {s["R1"]["realism"]["very_realistic"]}/9 · {s["R2"]["realism"]["very_realistic"]}/9 |')
    text+=['\n## 评分一致性','| 指标 | 原始一致率 | Cohen κ |','|---|---:|---:|']
    for k,name in [('usability','训练可用（两题都通过）'),('requirements','提示词符合（四题都通过）'),('realism','三档真实性')]:
        m=metrics[k];text.append(f'| {name} | {m["exact_agreement"]:.1%} | '+('NA' if m['kappa'] is None else f'{m["kappa"]:.3f}')+' |')
    text+= [f'真实性线性加权 κ = {metrics["realism_linear_weighted"]["kappa"]:.3f}，作为新增有序三档指标的补充描述；不将其换算成训练可用的通过门槛。',
           f'共 {len(disagreements)} 张至少一个具体评分项不同：可用性原题 64 张、提示词原题 39 张、真实性 73 张；类别相互重叠，不能相加。按两题合取后的训练可用标签仅 29 张不同，按四题合取后的提示词全部满足标签为 30 张不同。',
           '\n## 场景与强度的差异','当前 1860 / 0.8 按提示词分层：','| 提示词 | 训练可用 R1/R2（每人 n=3） | 提示词全部满足 R1/R2 |','|---|---:|---:|']
    for p in e.PROMPTS:
        a,b=stratified[p][e.REFERENCE]['R1'],stratified[p][e.REFERENCE]['R2'];text.append(f'| {p} | {a["usable"]}/3 · {b["usable"]}/3 | {a["prompt_pass"]}/3 · {b["prompt_pass"]}/3 |')
    text+=['\n按强度合并四个 checkpoint（每强度 36 张），只作为描述，不当成独立确认实验：','| 强度 | 训练可用 R1/R2 | 提示词全部满足 R1/R2 |','|---|---:|---:|']
    for v in e.STRENGTHS:
        group=[s for s in summary if s['config']!='no-lora' and float(s['config'].split('-')[1])==v]
        text.append(f'| {v} | '+ ' · '.join(f'{sum(s[r]["usable"] for s in group)}/36' for r in raters)+' | '+' · '.join(f'{sum(s[r]["prompt_pass"] for s in group)}/36' for r in raters)+' |')
    text+=['\n## 正式最终表与裁决',
           '原计划要求任一评分项分歧进入人工裁决。因此不能直接取均值、随意选一人的判断、把“两人都通过”作为临时规则，或由机器代评，来填正式裁决后主表。现有 summary.csv 的人工列保持 pending，并记录 adjudication_pending。上述双人原始结果已经可以用于描述性判断。',
           '打开 ../review/ADJ/index.html。仅包含分歧图、短问题和双方原始判断，不展示配置或自动分数。相同项预填，不同项留空，可采用某一方整张答案并修改。每张确认最终判断后才计入完成，下载 anonymous_adjudication_v3.json。请由真实人工裁决。',
           '裁决完成后运行：`python scripts/analyze_lora_reviews.py --adjudication <真实裁决JSON路径>`。它保留裁决原件、更新冻结主表，并重建本报告。',
           '\n## 方法与解释边界',
           'CLIP 使用原冻结的 ViT-L/14 224 和短文本，CLIP-T=100×余弦相似度，SD 为样本标准差（ddof=1）。CLIP 文本仍有原数量措辞，人工已去掉数量判断；两者并非完全相同的评价口径。',
           '评价涵盖 16 个 LoRA 配置与无 LoRA 基线，只能说明三条提示词和三个 seed 范围内的结果。不使用误差条重叠、p>0.05 或任意阈值证明等效/非劣。真实性三档、两道可用性题的 v3 修订发生在作者试评十几张之后；旧评分按作者要求舍去。图片展示匿名配置，不能声称作者此前从未见过数据。',
           '机器未补充任何人工标签。所有原始 JSON、协议哈希、逐项与按 seed 的结果可溯源至 results.json 和 restricted/raw/。']
    if final:
        text+=['\n## 已完成的人工裁决后主表','| 配置 | 训练可用 | 提示词全部满足 | 不太真实 / 还算真实 / 很真实 |','|---|---:|---:|---:|']
        for s in summary:
            f=s['adjudicated'];text.append(f'| {s["config"]} | {f["usable"]}/9 | {f["prompt_pass"]}/9 | '+ ' / '.join(str(f['realism'][v]) for v in VALUES)+' |')
        text=[t.replace('现有 summary.csv 的人工列保持 pending，并记录 adjudication_pending。','真实裁决已经导入，summary.csv 已更新裁决后结果。') for t in text]
        f=ref['adjudicated']
        text.insert(3,f'正式裁决后，当前 1860 / 0.8：训练可用 {f["usable"]}/9、提示词全部满足 {f["prompt_pass"]}/9；真实性三档为 '+ '/'.join(str(f['realism'][v]) for v in VALUES)+'。下文双人原始评分保留作一致性与敏感性描述，正式主表见文末。')
    formatted=[]
    for paragraph in text:
        separator='\n' if formatted and paragraph.startswith('|') and formatted[-1].rstrip().split('\n')[-1].startswith('|') else '\n\n'
        formatted.append((separator if formatted else '')+paragraph.strip())
    (DEST/'report.md').write_text(''.join(formatted)+'\n',encoding='utf-8')
    e.write(DEST/'validation.json',dict(status=status,n_images=153,n_raters=2,n_complete_ratings=306,disagreement_images=len(disagreements),original_clip_unchanged=e.sha(e.OUT/'clip_scores.csv')==human['clip_scores_sha256'],
        source_files={r:e.sha(e.OUT/'restricted'/f'{r}_current.json') for r in raters},checks=['original protocol/code/input freeze verified','v3 schema and reasons valid','all 153 unique images covered per rater','all 306 complete','per-configuration n=9, sums agree with 153-image totals'],analysis_code_sha256=e.sha(__file__)))
    print('Report:',DEST/'report.md','status:',status,'disagreement images:',len(disagreements))
    print('Adjudication:',e.OUT/'review/ADJ/index.html')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--adjudication',type=Path);args=parser.parse_args()
    if args.adjudication:
        payload=e.read(args.adjudication);e.require(payload.get('rater')=='ADJ','Expected a real ADJ export')
        e.import_review(args.adjudication);e.aggregate()
    analyze()
