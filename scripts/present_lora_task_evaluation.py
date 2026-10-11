"""Task-oriented presentation amendment; source evaluations remain intact.

Three main metrics: CLIP, training usability, and the very-realistic count.
Prompt compliance and the original four-panel view remain supplementary.
"""
from pathlib import Path
import shutil
import itertools
import eval_lora_compare as e
import finalize_lora_evaluation as f

OUT=e.OUT
FIG=e.FIGURES
ARCHIVE=OUT/'versions/before_task_presentation'


def vectors(summary,final,mapping):
    return {s['config']:(float(s['clip_t_mean']),int(s['usable_n']),sum(final[m['image_id']]['realism']=='very_realistic' for m in mapping.values() if m['config']==s['config'])) for s in summary}


def pareto_front(values):
    return [c for c,x in values.items() if not any(all(a>=b for a,b in zip(y,x)) and any(a>b for a,b in zip(y,x)) for d,y in values.items() if d!=c)]


def render_three_metrics(summary,final,mapping):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'pdf.fonttype':42,'svg.fonttype':'path'})
    values=vectors(summary,final,mapping)
    fig=plt.figure(figsize=(7.2,5.1),layout='constrained')
    grid=fig.add_gridspec(2,3,height_ratios=[1.45,1.04],hspace=.14,wspace=.10)
    panels=[('(a) CLIP-T mean',0,'cividis',None),('(b) Training usable',1,'Blues',(0,9)),('(c) Rated very realistic',2,'Blues',(0,9))]
    for j,(title,metric,cmap,limits) in enumerate(panels):
        ax=fig.add_subplot(grid[0,j]);matrix=np.array([[values[f'{s}-{v:.1f}'][metric] for v in e.STRENGTHS] for s in e.STEPS])
        lo,hi=(float(matrix.min()),float(matrix.max())) if limits is None else limits
        im=ax.imshow(matrix,cmap=cmap,vmin=lo,vmax=hi)
        ax.set_xticks(range(4),[str(v) for v in e.STRENGTHS]);ax.set_yticks(range(4),[str(s) for s in e.STEPS])
        ax.set_title(title,loc='left',fontsize=8,weight='bold',pad=24)
        base=f'{values["no-lora"][metric]:.2f}' if metric==0 else f'{values["no-lora"][metric]}/9'
        ax.text(0,1.05,'No-LoRA baseline: '+base,transform=ax.transAxes,fontsize=7)
        ax.set_xlabel('LoRA strength')
        if j==0:ax.set_ylabel('Training step')
        for i,k in itertools.product(range(4),repeat=2):
            rgba=im.cmap(im.norm(matrix[i,k]));lum=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
            text=f'{matrix[i,k]:.2f}' if metric==0 else f'{int(matrix[i,k])}/9'
            ax.text(k,i,text,ha='center',va='center',fontsize=7.5,color='black' if lum>.5 else 'white')
        ax.add_patch(Rectangle((1.5,2.5),1,1,fill=False,edgecolor='#bb4b00',linewidth=1.7))
        bar=fig.colorbar(im,ax=ax,fraction=.042,pad=.04,shrink=.94)
        bar.ax.tick_params(labelsize=6)
        if limits:bar.set_ticks([0,3,6,9])
    ax=fig.add_subplot(grid[1,:]);ax.axis('off')
    ax.text(0,.98,'Preferred candidate for detection data: step 1860 / strength 0.8',transform=ax.transAxes,fontsize=9,weight='bold',color='#173c50',va='top')
    ax.text(0,.84,'Three metrics give complementary evidence; no weighted composite score is used.',transform=ax.transAxes,fontsize=7,va='top')
    competitors=[('1860-0.8','Preferred candidate'),('1500-0.8','Highest CLIP-T'),('1860-0.2','Most training-usable'),('no-lora','Baseline')]
    cells=[[('No LoRA' if c=='no-lora' else c.replace('-',' / ')),role,f'{values[c][0]:.2f}',f'{values[c][1]}/9',f'{values[c][2]}/9'] for c,role in competitors]
    table=ax.table(cellText=cells,colLabels=['Step / strength','Role','CLIP-T','Usable','Very realistic'],colWidths=[.19,.35,.15,.15,.16],cellLoc='left',colLoc='left',bbox=[0,.19,1,.58])
    table.auto_set_font_size(False);table.set_fontsize(7)
    for (i,j),cell in table.get_celld().items():
        cell.set_edgecolor('#d7e2e7');cell.set_linewidth(.5)
        if i==0:cell.set_facecolor('#173c50');cell.get_text().set_color('white');cell.get_text().set_weight('bold')
        elif i==1:cell.set_facecolor('#edf4f7');cell.get_text().set_weight('bold')
        else:cell.set_facecolor('white')
    ax.text(0,.10,'vs 1500 / 0.8: -0.35 CLIP-T, +2 usable, +2 very realistic.\nvs 1860 / 0.2: +0.83 CLIP-T, -1 usable, +3 very realistic.',transform=ax.transAxes,fontsize=7,va='top',linespacing=1.5)
    fig.suptitle('Task-oriented LoRA configuration assessment\n153 images | 9 per setting | two raters + human adjudication',fontsize=10)
    fig.supxlabel('Orange outline identifies the preferred candidate. Prompt compliance is reported in the supplement.',fontsize=6.7)
    for ext in ['pdf','svg','png']:fig.savefig(FIG/f'lora_final_evaluation.{ext}',dpi=300)
    plt.close(fig)


def render_prompt_supplement(summary,final,mapping):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
    by={s['config']:s for s in summary}
    counts=[]
    for p in e.PROMPTS:
        labels=[final[m['image_id']] for m in mapping.values() if m['prompt_id']==p]
        assert len(labels)==51
        counts.append([sum(x['requirements'][i]=='pass' for x in labels) for i in range(4)])
    fig=plt.figure(figsize=(7.2,4.7));grid=fig.add_gridspec(2,2,width_ratios=[1,1.3],height_ratios=[3,.9],left=.10,right=.97,bottom=.05,top=.76,wspace=.75,hspace=.45)
    ax=fig.add_subplot(grid[0,0]);v=np.array([[int(by[f'{s}-{w:.1f}']['prompt_pass_n']) for w in e.STRENGTHS] for s in e.STEPS])
    im=ax.imshow(v,cmap='Blues',vmin=0,vmax=9)
    ax.set_title('(a) All four requirements met',loc='left',fontsize=8,weight='bold',pad=24)
    ax.text(0,1.05,'No-LoRA baseline: 6/9',transform=ax.transAxes,fontsize=7)
    ax.set_xticks(range(4),[str(w) for w in e.STRENGTHS]);ax.set_yticks(range(4),[str(s) for s in e.STEPS]);ax.set_xlabel('LoRA strength');ax.set_ylabel('Training step')
    for i,j in itertools.product(range(4),repeat=2):ax.text(j,i,f'{v[i,j]}/9',ha='center',va='center',fontsize=8,color='white' if v[i,j]>=6 else 'black')
    ax.add_patch(Rectangle((1.5,2.5),1,1,fill=False,edgecolor='#bb4b00',linewidth=1.7))
    fig.colorbar(im,ax=ax,fraction=.044,pad=.04).set_ticks([0,3,6,9])
    ax=fig.add_subplot(grid[0,1]);matrix=np.array(counts);im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=51,aspect='equal')
    ax.set_title('(b) Individual requirements | all settings',loc='left',fontsize=8,weight='bold',pad=24)
    ax.text(0,1.06,'Each cell: passes among 51 images',transform=ax.transAxes,fontsize=7)
    ax.set_xticks(range(4),['Q1','Q2','Q3','Q4']);ax.set_yticks(range(3),['Single cylinder','Storage cage','Cylinder cluster'],fontsize=7);ax.set_xlabel('Prompt-specific question')
    for i,j in itertools.product(range(3),range(4)):ax.text(j,i,f'{matrix[i,j]}/51',ha='center',va='center',fontsize=8,color='white' if matrix[i,j]>32 else 'black')
    ax.add_patch(Rectangle((.5,.5),1,1,fill=False,edgecolor='#bb4b00',linewidth=1.5))
    note=fig.add_subplot(grid[1,:]);note.axis('off')
    note.text(0,.75,'Storage cage Q2 (two-row arrangement): 0/51; training usability for this scene: 30/51.\nAll-four prompt compliance is therefore zero for this scene, despite usable images.\nFull question definitions and all original labels remain in the frozen protocol and data.',transform=note.transAxes,fontsize=7,va='top',linespacing=1.6)
    fig.suptitle('Supplementary prompt-compliance analysis\nAdjudicated human labels | all 153 images retained',fontsize=10)
    for ext in ['pdf','svg','png']:fig.savefig(FIG/f'lora_prompt_compliance_supplement.{ext}',dpi=300)
    plt.close(fig)


def apply_presentation():
    summary,final,mapping,chosen,raw=f.verify_final();ARCHIVE.mkdir(parents=True,exist_ok=True)
    archive_paths=[OUT/'report.md',OUT/'methods_results.md',OUT/'acceptance.json',OUT/'human_analysis/report.md',OUT/'summary.md',e.ROOT/'paper/tables/lora_parameter_sensitivity.tex',Path(__file__).with_name('finalize_lora_evaluation.py')]
    archive_paths += [FIG/f'lora_final_evaluation.{ext}' for ext in ['pdf','svg','png']]
    for p in archive_paths:
        name='human_report.md' if p==OUT/'human_analysis/report.md' else p.name
        if p.exists() and not (ARCHIVE/name).exists():shutil.copy2(p,ARCHIVE/name)
    all_values=vectors(summary,final,mapping);front=pareto_front(all_values)
    assert set(front)=={'1500-0.8','1860-0.2','1860-0.8'}
    count=sum(final[m['image_id']]['requirements'][1]=='pass' for m in mapping.values() if m['prompt_id']=='new24_001')
    assert count==0
    render_three_metrics(summary,final,mapping)
    render_prompt_supplement(summary,final,mapping)
    data=e.read(OUT/'human_analysis/final_results.json')
    amendment=dict(date='2026-10-11',requested_by='author after inspecting all evaluation results',scope='presentation only; endpoints and all original labels unchanged',
                   main_metrics=['clip_t_mean','usable_n','very_realistic_n'],supplementary_metric='prompt_pass_n',
                   reason='Detection-data utility is the main goal; prompt arrangement constraints can fail without preventing bounding-box training. Storage-cage two-row question has zero passes among 51 images.',
                   decision='Retain 1860/0.8 as the task-oriented preferred candidate; not a proven global optimum or a weighted composite winner',
                   pareto_front=front,counts=all_values,analysis_script_sha256=e.sha(__file__),
                   preserved_data_sha256={p.relative_to(e.ROOT).as_posix():e.sha(p) for p in [OUT/'protocol.json',OUT/'review_protocol.json',OUT/'clip_scores.csv',OUT/'summary.csv',OUT/'restricted/final_labels.json',OUT/'review/anonymous_review_v3_R1.json',OUT/'review/anonymous_review_v3_R2.json',OUT/'review/anonymous_adjudication_v3.json']})
    e.write(OUT/'human_analysis/presentation_amendment.json',amendment)
    # Keep the full numerical report, add a task-oriented lead and disclosure.
    lead='''## 面向目标检测数据生成的呈现调整（2026-10-11）

**主图聚焦 CLIP、训练可用性及照片真实性，保留 1860 / 0.8 作为优先候选。** 它是本次样本中“很真实”数量最高的配置（6/9），CLIP 第 2，训练可用 6/9。与 1500 / 0.8 相比，CLIP 差 -0.35、训练可用多 2 张、很真实多 2 张；与 1860 / 0.2 相比，CLIP 多 0.83、训练可用少 1 张、很真实多 3 张。与无 LoRA 相比，CLIP 多 1.42、训练可用相同、很真实多 5 张。

这三个配置构成本次三个主图指标的帕累托前沿：没有其他配置在三项上均不低于它们且至少一项更高。现用配置通过较高的文本相似度、可用性和最高的“很真实”数量体现有依据的取舍，可称为面向本研究用途的优先候选；未预先规定跨指标权重，因此不称为已证明的综合最优。

提示词全部满足指标保留在补充图、原始完整表和方法中，不作为主图决策指标。“两排排列”问题实际为 0/51，导致该场景的四题全部满足在所有配置下均为零；它衡量具体布局遵从，不能直接作为检测训练可用性门槛。作者在看到完整评价结果后要求此呈现调整：这是事后基于任务目的的展示与解释选择，不冒称评分前预定指标，也不删除未被强调的结果。

主图的三个面板重新连续编号为 (a) CLIP、(b) 训练可用、(c) 很真实；原四面板中的 (d) 内容现在位于第三面板。完整指标仍可按下文逐项核查。

'''
    for path in [OUT/'report.md',OUT/'human_analysis/report.md']:
        text=path.read_text(encoding='utf-8')
        if '## 面向目标检测数据生成的呈现调整' not in text:text=text.replace('## 最终结论',lead+'## 完整指标的最终结论',1)
        text=text.replace('CLIP 与三个裁决后人工指标的四面板图。','CLIP、训练可用及很真实的三面板主图；提示词满足位于 lora_prompt_compliance_supplement，完整数值仍保留。')
        path.write_text(text,encoding='utf-8')
    caption='''## Task-oriented presentation amendment (2026-10-11)

After examining the complete results, the author requested a main figure emphasizing CLIP-T, training usability, and photographic realism for detection-data generation. Prompt compliance is retained as a supplementary endpoint; neither its labels nor the full original table were discarded. The two-row arrangement requirement had zero passes among 51 storage-cage images, forcing this scene to fail the all-four-requirements endpoint without itself determining object-detection training usability. This is a post-results presentation choice, not an original preregistered endpoint change.

The existing step-1860 / strength-0.8 configuration is retained as the preferred task-oriented candidate. Its CLIP-T is 30.41 (rank 2), usability is 6/9, and the very-realistic count is 6/9, the highest observed. Relative to step-1500 / strength-0.8 it trades 0.35 CLIP-T for two additional usable and two additional very-realistic images. Relative to step-1860 / strength-0.2 it has 0.83 higher CLIP-T and three additional very-realistic images with one fewer usable image. These three configurations form the observed Pareto frontier for the three displayed metrics. This is an informed multi-criterion choice, not a weighted optimum or a claim of noninferiority.

### Revised main figure caption

Task-oriented assessment of LoRA checkpoints and strengths. Panels show (a) CLIP-T mean, (b) training-usable images, and (c) images rated very realistic. All 16 LoRA settings are displayed; the no-LoRA baseline is reported separately in each panel. Each setting has nine images (three prompts and three matched seeds), and all human counts use real adjudicated labels. The orange outline identifies the retained step-1860 / strength-0.8 candidate. The comparison table displays the CLIP-leading setting, usability-leading setting, and baseline without a combined score. Prompt compliance and the full three-category realism results remain in supplementary materials. The three-metric display was requested after results were available and should not be interpreted as a pre-specified superiority test.

### Supplementary prompt-compliance caption

Adjudicated prompt-compliance results. Panel (a) retains the all-four-requirements count for every setting. Panel (b) reports each prompt-specific binary question over all 51 images for that prompt. The storage-cage two-row question had zero passes; its effect on the combined endpoint is documented rather than omitted. Questions and complete original labels remain in the frozen review protocol and retained review exports.
'''
    p=OUT/'methods_results.md';text=p.read_text(encoding='utf-8')
    if '## Task-oriented presentation amendment' not in text:text+='\n\n'+caption
    text=text.replace('For lora_final_evaluation, panels show (a) mean CLIP-T, (b) training-usable images, (c) images satisfying all four prompt requirements, and (d) images rated very realistic.','The original four-panel presentation is archived under versions/before_task_presentation. For the revised lora_final_evaluation, panels show (a) mean CLIP-T, (b) training-usable images, and (c) images rated very realistic; all-four prompt compliance is displayed in lora_prompt_compliance_supplement.')
    p.write_text(text,encoding='utf-8')
    # Provide a main display table without replacing the frozen full results.
    table=['| 配置 | CLIP-T 均值 ± SD | 训练可用 | 很真实 |','|---|---:|---:|---:|']
    tex=[r'\begin{tabular}{llccc}',r'\hline',r'Step & Strength & CLIP-T mean $\pm$ SD & Usable & Very realistic \\',r'\hline']
    for s in summary:
        c=s['config'];clip,usable,very=all_values[c]
        table.append(f'| {c} | {clip:.2f} ± {float(s["clip_t_sd"]):.2f} | {usable}/9 | {very}/9 |')
        tex.append(f'{s["step"] or "No LoRA"} & {s["strength"] or "--"} & {clip:.2f} $\\pm$ {float(s["clip_t_sd"]):.2f} & {usable}/9 & {very}/9 '+r'\\')
    tex += [r'\hline',r'\end{tabular}','% Task-oriented presentation requested after results; full prompt compliance retained separately.']
    (OUT/'task_summary.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
    (e.ROOT/'paper/tables/lora_task_evaluation.tex').write_text('\n'.join(tex)+'\n',encoding='utf-8')
    print('Three-metric main figure and full prompt-compliance supplement generated; source data unchanged')


if __name__=='__main__':apply_presentation()
