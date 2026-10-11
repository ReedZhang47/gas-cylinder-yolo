"""Editable research diagrams. Reference figures supply styling only."""
import json
from pathlib import Path
from prepare_figures import Scene, HERE, asset

BLACK='#181818'
RULE='#B7B7B7'
SERIF='Times New Roman'
BLUE='#536F8E'
PALEBLUE='#E2EDF6'
PEACH='#F5E6D5'
GREEN='#E9F0DF'
TEAL='#E0EEEE'


def base(old,width,height,notes):
    s=Scene(old['number'],old['stem'],old['title'],old['old_number'],notes)
    s.objects.clear(); s.data.update(width=width,height=height)
    return s


def tx(s,x,y,w,h,text,size=16,bold=False,font=SERIF,color=BLACK,align='left',italic=False):
    s.text(x,y,w,h,text,size,color,bold,italic,align,font)


def label(s,x,y,w,text,size=13,color=BLACK,bold=False,align='left',h=24):
    tx(s,x,y,w,h,text,size,bold,'Arial',color,align)


def photo(s,name,x,y,w,h,shadow=False):
    p=HERE/'media'/name
    result=s.photo(p,x,y,w,h,border=False)
    pic=s.objects[-1]; pic['shadow']=shadow
    px,py,pw,ph,*_=result
    s.rect(px,py,pw,ph,stroke='#696969',weight=.65)
    return result


def down(s,x,y1,y2,color=BLACK,weight=1):
    s.line(x,y1,x,y2,color=color,weight=weight,arrow=True)


def roundbox(s,x,y,w,h,fill=None,stroke=BLACK,weight=1):
    return s.obj('roundrect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,weight=weight,dash=False)


def boxtext(s,x,y,w,h,title,detail='',fill='#FFFFFF',stroke=BLACK,size=18):
    roundbox(s,x,y,w,h,fill,stroke)
    if detail:
        tx(s,x+10,y+7,w-20,29,title,size,True,align='center')
        tx(s,x+10,y+38,w-20,h-44,detail,14,align='center')
    else:tx(s,x+8,y+6,w-16,h-12,title,size,True,align='center')


def ensure_assets():
    gas=Path('D:/gas_cylinders')
    for n in [7,14,30,12,36]:
        name=f'real_photo_{n}.png'
        if not (HERE/'media'/name).exists():asset(gas/'real_photo/93_real_photos/images'/name)
    for n in [3,159,985,1006]:
        name=f'D_{n:04d}.png'
        if not (HERE/'media'/name).exists():asset(gas/'D1085/images'/name)
    name='Placement_Issues_0301.png'
    if not (HERE/'media'/name).exists():asset(gas/'Placement_Issues/images'/name)


def fig1(old):
    s=base(old,1330,408,
      'Four-arm study overview updated 2026-10-09. A=93; B/C/D=1085. D image review, annotation, six 300-epoch detector runs and evaluation are complete. '
      'Source photographs: real_photo_30 (front/top), real_photo_14 (middle), real_photo_7 (back/bottom). '
      'Six detectors: yolov8s/m, yolo11s/m, yolo26s/m. dev61 is a development benchmark, not a frozen external test. '
      'Evidence: EXPERIMENTS.md; experiments/v5_d/acceptance.md. Candidate checkpoint labels retain the existing zero-based filename convention.')
    for x,w,title in [(24,550,'(a) Data construction'),(634,254,'(b) Controlled training'),(950,356,'(c) Development evaluation')]:
        tx(s,x,15,w,30,title,18,True);s.line(x,52,x+w,52,color=BLACK,weight=.8)
    tx(s,24,106,157,30,'real93',22,True,align='center')
    # Draw back to front: 7, 14, 30. All three remain separate, full-colour images.
    for n,x,y,rot in [(7,29,206,-5),(14,38,184,-2),(30,47,162,2)]:
        frame=s.rect(x-3,y-3,130,100,fill='#FFFFFF',stroke='#888888',weight=.5)
        frame.update(rotation=rot,shadow=True)
        s.photo(HERE/'media'/f'real_photo_{n}.png',x,y,124,94,border=False)
        s.objects[-1]['rotation']=rot
    tx(s,24,315,157,43,'93 real photographs\nOn-site and web sources',12,align='center')
    s.line(181,215,201,215);s.line(201,111,201,336)
    rows=[('A',78,'Real-only baseline','Reviewed labels','93'),('B',153,'Classical augmentation','Offline transformations','1,085'),('C',228,'Image editing','Reviewed synthetic images','1,085'),('D',303,'LoRA text-to-image','Reviewed images and labels','1,085')]
    for arm,y,title,detail,count in rows:
        s.line(201,y+33,229,y+33,color=BLACK,arrow=True)
        s.rect(233,y+5,27,27,fill='#444444',stroke=None)
        label(s,233,y+6,27,arm,14,'#FFFFFF',True,'center',25)
        tx(s,270,y,238,29,title,16,True)
        tx(s,270,y+31,253,26,detail,12)
        tx(s,512,y+2,68,28,count,19,align='right')
        s.line(270,y+61,580,y+61,color=RULE,weight=.45)
        s.line(582,y+33,606,y+33,color=BLACK)
    s.line(606,111,606,336,weight=.65);s.line(606,210,632,210,arrow=True)
    label(s,637,74,245,'Six detectors per arm',13,bold=True,align='center')
    label(s,650,111,109,'Small (s)',12,bold=True,align='center')
    label(s,772,111,113,'Medium (m)',12,bold=True,align='center')
    s.line(647,139,885,139,weight=.65)
    for i,model in enumerate(['YOLOv8','YOLO11','YOLO26']):
        y=148+38*i
        tx(s,649,y,114,27,model+'s',15,align='center')
        tx(s,770,y,116,27,model+'m',15,align='center')
        s.line(647,y+32,885,y+32,color=RULE,weight=.4)
    down(s,765,259,279)
    tx(s,650,286,236,28,'300 epochs per run',17,True,align='center')
    tx(s,646,320,245,43,'Checkpoints every 10 epochs\nand final last.pt',14,align='center')
    s.route([(890,333),(920,333),(920,145),(967,145)],weight=.7)
    s.rect(950,76,356,48,fill='#F1F1F1',stroke=None)
    tx(s,961,82,71,29,'dev61',20,True)
    tx(s,1040,80,255,33,'61 development images\nExcluded from detector training',12)
    s.route([(1128,124),(1128,145),(967,145),(967,335)],arrow=False)
    for y,title,line1,line2 in [(167,'Fixed endpoint','last.pt evaluated on dev61',''),(240,'Five-fold cross-fitting','Joint model + checkpoint; pooled OOF','Paired bootstrap: 10,000 resamples'),(321,'Deployment selection','All dev61; development score','')]:
        s.line(967,y+14,992,y+14,arrow=True)
        tx(s,1001,y-2,305,27,title,17,True);tx(s,1001,y+28,305,23,line1,13)
        if line2:tx(s,1001,y+49,305,23,line2,12)
    tx(s,24,379,1282,20,'All four arms completed. dev61 supports development analysis; a frozen external test remains to be collected.',11,italic=True)
    return s


def fig2(old):
    s=base(old,1380,650,
      'Image-Edit workflow. Styling only adapted from supplied Li2025 reference: pale-blue field, separated input/processing regions, pastel modules and direct arrows. '
      'No reference scientific content is reused. C example Placement_Issues_0301.png: PNG prompt nodes 23 and 25 explicitly load real_photo_12.png and real_photo_36.png; node 7 conditions on both. '
      'The displayed instruction is an English summary, not a verbatim prompt. Model and encoders: docs/v5_prompts/generation_models.md. '
      'Lightning is optional across C; do not infer all 1085 images used the same sampling settings. Final C dataset has 1085 retained and annotated images.')
    roundbox(s,12,12,1356,626,'#E2EDF6',None)
    s.line(378,36,378,611,color='#748595',weight=1.25,dash=True)
    tx(s,36,31,316,36,'(a) Reference composition',22,True,align='center')
    tx(s,414,31,918,36,'(b) Conditioned image editing and dataset assembly',22,True,align='center')
    # Reference photographs retain their original aspect ratios.
    photo(s,'real_photo_12.png',40,115,174,153)
    photo(s,'real_photo_36.png',254,102,106,176)
    tx(s,216,160,34,48,'+',30,True,align='center')
    label(s,44,286,168,'Reference 12',12,align='center')
    label(s,243,286,125,'Reference 36',12,align='center')
    s.route([(124,316),(124,334),(305,334),(305,316)],arrow=False,weight=1)
    s.line(214,334,214,354,arrow=True)
    tx(s,43,354,303,28,'Joint visual conditioning',18,True,align='center')
    s.rect(41,414,313,115,fill='#FFF4D5',stroke=None)
    tx(s,52,424,291,30,'Edit instruction',20,True,align='center')
    tx(s,59,462,277,54,'Combine the cage and cylinders\nwith the reference scene',17,align='center')
    tx(s,42,555,311,44,'Two reference photographs\ncontribute to image 301',16,align='center',italic=True)
    # Input bus: both references and the edit instruction feed multimodal encoding.
    s.route([(354,471),(418,471),(418,172),(434,172)],weight=1.1)
    s.route([(354,367),(402,367),(402,143),(434,143)],weight=1.1)
    boxtext(s,434,105,338,80,'Multimodal encoder','Qwen2.5-VL 7B · FP8',PEACH)
    tx(s,475,189,256,26,'Visual + text conditioning',15,italic=True,align='center')
    s.route([(772,145),(857,145),(857,243)],weight=1.2)
    boxtext(s,435,285,187,78,'Image encoding','Scale + Qwen VAE',TEAL,size=18)
    s.route([(402,327),(435,327)],weight=1.1)
    s.line(622,327,683,327,arrow=True,weight=1.3)
    tx(s,438,370,179,25,'Reference latent',15,italic=True,align='center')
    # The block is a generic DiT/sampling schematic, not a copied U-Net architecture.
    roundbox(s,683,243,348,203,'#BFD3E8',BLUE,1.2)
    tx(s,697,251,320,32,'Qwen-Image-Edit-2509',22,True,align='center')
    tx(s,705,286,304,27,'FP8 diffusion backbone',17,align='center')
    s.rect(702,328,310,54,fill='#F7FAFD',stroke=BLUE,weight=.7)
    tx(s,712,336,290,35,'Conditioned denoising',20,True,align='center')
    label(s,706,401,302,'KSampler · Euler / simple',14,align='center')
    boxtext(s,683,497,348,74,'Sampling configuration','Standard / optional Lightning path',fill='#F3F0E7',size=19)
    down(s,857,497,446)
    boxtext(s,438,493,183,78,'Noise latent','Seed + output size',fill='#F4F4F4',size=17)
    s.route([(621,532),(648,532),(648,417),(683,417)],weight=1.1)
    s.route([(1031,355),(1060,355),(1060,147),(1090,147)],weight=1.2)
    boxtext(s,1090,109,242,76,'VAE decoding','Qwen image VAE',fill=TEAL,size=20)
    down(s,1211,185,233)
    photo(s,'Placement_Issues_0301.png',1087,234,248,186,True)
    tx(s,1087,429,248,28,'Generated image 301',18,True,align='center')
    down(s,1211,465,496)
    tx(s,1076,500,270,51,'Human review\nand YOLO annotation',18,True,align='center')
    down(s,1211,559,581)
    tx(s,1048,585,309,29,'Arm C: 1,085 images',22,True,align='center')
    tx(s,414,598,610,24,'Reference pairing shown for image 301; sampling settings can vary across C.',12,italic=True)
    return s


def fig3(old):
    s=base(old,1340,850,
      'LoRA fitting and completed D data construction, updated 2026-10-09. Styling only inspired by supplied Jeong2026 references: bordered parallel stages, muted blue frozen weights and peach low-rank update. '
      'All scientific content derives from this project. No real93 photo is displayed. LoRA: 93 reviewed image-caption pairs; DiffSynth-Studio SFT; AdamW; FlowMatchSFTLoss; constant LR 1e-4; rank16; batch1; max pixels1048576; 93x5x4=1860 steps. '
      'LoRA base is DiT; adapters cover attention and image-MLP projections, not text encoder. The W + BA diagram is conceptual, not a claim about exact attention architecture. '
      'Generation: Qwen-Image-2.1 INT8 convrot; Qwen3VL 8B INT8; step-1860 strength0.8; Euler/simple25 steps; CFG1; random seed; denoise1;1184x896; batch1; empty negative prompt; BF16 VAE. '
      'Actual sequence: planned generation, screening, supplementary generation, screening, 1085 accepted images. No intermediate candidate counts shown. '
      'Examples D_0003,D_0159,D_0985,D_1006 are accepted dataset images. Evidence docs/v5_prompts/qwen21_lora_training_validation.md; experiments/v5_d/acceptance.md. No reference contents reused.')
    # Two scientific panels, with titles integrated into the upper frame.
    s.rect(17,39,535,788,stroke='#C4CCD2',weight=1.6)
    s.rect(585,39,738,788,stroke='#C4CCD2',weight=1.6)
    boxtext(s,37,16,495,49,'(a) LoRA adaptation',fill='#FFFFFF',stroke='#8BA6C3',size=24)
    boxtext(s,605,16,698,49,'(b) Text-to-image dataset construction',fill='#FFFFFF',stroke='#8BA6C3',size=24)
    boxtext(s,64,91,441,74,'93 reviewed image–caption pairs','real93 · caption trigger: cylsite93',fill='#F4F6F7',size=20)
    down(s,284,165,195,BLUE,1.7)
    tx(s,51,195,467,31,'Qwen-Image-2.1 DiT',23,True,align='center')
    roundbox(s,43,240,483,250,'#FFFFFF','#A8BACB',1.3)
    # Frozen branch and trainable low-rank branch merge explicitly.
    s.rect(63,323,52,82,fill='#F5F5F5',stroke='#737373',weight=.9)
    tx(s,68,339,42,49,'x',26,italic=True,align='center')
    s.rect(181,266,165,71,fill='#BDD0E7',stroke='#87A4C6',weight=1)
    tx(s,187,269,153,28,'Frozen weights',17,True,align='center')
    tx(s,187,301,153,29,'W',23,italic=True,align='center')
    s.route([(115,350),(145,350),(145,303),(181,303)],color='#737373',weight=1.6)
    boxtext(s,161,401,86,55,'A',fill=PEACH,stroke='#CAA57F',size=23)
    boxtext(s,278,401,86,55,'B',fill=PEACH,stroke='#CAA57F',size=23)
    s.route([(115,381),(136,381),(136,429),(161,429)],color='#737373',weight=1.6)
    s.line(247,429,278,429,arrow=True,weight=1.4)
    tx(s,162,463,202,21,'Trainable update · rank 16',13,color='#795431',align='center')
    s.ellipse(389,346,32,32,fill='#FFFFFF',stroke=BLACK,weight=1)
    tx(s,390,346,30,29,'+',22,align='center')
    s.route([(346,303),(405,303),(405,346)],weight=1.4)
    s.route([(364,429),(405,429),(405,378)],weight=1.4)
    s.rect(458,323,45,82,fill=TEAL,stroke='#7AA0A3',weight=.9)
    tx(s,460,339,41,49,'h',26,italic=True,align='center')
    s.line(421,362,458,362,arrow=True,weight=1.4)
    tx(s,79,508,410,31,'h = Wx + BAx',23,italic=True,align='center')
    tx(s,61,552,449,30,'LoRA optimization',20,True)
    s.line(61,589,510,589,color='#A8BACB',weight=.8)
    settings=[('Framework / loss','DiffSynth-Studio / FlowMatchSFTLoss'),('Optimizer / learning rate','AdamW / 1e-4 (constant)'),('Batch / pixel limit','1 / 1,048,576'),('Training schedule','93 × 5 repeats × 4 epochs')]
    for i,(key,val) in enumerate(settings):
        y=599+29*i
        tx(s,61,y,177,25,key,13)
        tx(s,240,y,273,25,val,13)
    down(s,284,720,741,BLUE,1.5)
    boxtext(s,64,744,441,66,'Final adapter: step-1860','1,860 optimizer steps',fill=GREEN,size=20)
    # Generation pipeline. Adapter connection uses the inter-panel gutter.
    s.route([(505,773),(566,773),(566,227),(630,227)],color=BLUE,weight=1.4)
    roundbox(s,630,91,647,97,'#EFF3F5','#657889',1)
    tx(s,642,93,623,26,'Core components',19,True,align='center')
    boxtext(s,646,128,294,47,'Qwen-Image-2.1 · INT8',fill=PALEBLUE,stroke='#8296A9',size=18)
    boxtext(s,956,128,305,47,'Qwen3VL 8B · INT8',fill=TEAL,stroke='#8296A9',size=18)
    down(s,953,188,205)
    boxtext(s,630,205,647,45,'Load trained LoRA · strength 0.8',fill=GREEN,stroke='#82926D',size=21)
    down(s,953,250,288)
    # Prompt enters the sampler after encoding; no outdated source-group quotas.
    boxtext(s,609,289,207,70,'Text prompts','Scene and safety state',fill='#FFFFFF',size=18)
    s.line(816,324,845,324,arrow=True,weight=1.2)
    boxtext(s,845,288,432,77,'Conditioned sampling','Euler / simple · 25 steps · CFG 1',fill='#E9E7EF',stroke='#9390A0',size=21)
    tx(s,847,371,428,24,'Random seed · 1184 × 896 · batch 1',14,align='center')
    down(s,1061,401,418)
    boxtext(s,845,418,432,48,'VAE decoding',fill=PEACH,stroke='#AB9277',size=21)
    tx(s,610,423,208,35,'Qwen-Image-2.1 VAE',15,align='center')
    down(s,1061,466,488)
    tx(s,625,489,652,30,'Generation and quality review',20,True,align='center')
    s.route([(953,522),(600,522),(600,565),(610,565)],weight=1)
    stages=[(610,160,'Planned\ngeneration',PALEBLUE),(792,135,'Screening',GREEN),(949,181,'Supplementary\ngeneration',PEACH),(1152,135,'Screening',GREEN)]
    for x,w,t,fill in stages:
        boxtext(s,x,536,w,59,t,fill=fill,stroke='#87939B',size=17)
    for x1,x2 in [(770,792),(927,949),(1130,1152)]:s.line(x1,565,x2,565,arrow=True,weight=1.2)
    s.route([(1219,595),(1219,622),(953,622)],arrow=False,weight=1)
    down(s,953,622,641)
    tx(s,629,641,650,36,'Arm D: 1,085 accepted images',25,True,align='center')
    # Four-image strip: no overlap or source photos, unlike figures 1 and 2.
    for n,x in zip([3,159,985,1006],[610,783,956,1129]):
        photo(s,f'D_{n:04d}.png',x,691,163,123)
    return s


def revised_figures(figures):
    ensure_assets()
    old={f['number']:f for f in figures}
    return [fig1(old[1]),fig2(old[2]),fig3(old[3])]


def main():
    original=json.loads((HERE/'scene.json').read_text(encoding='utf-8'))
    revised={s.data['number']:s.data for s in revised_figures(original['figures'])}
    original['figures']=[revised.get(f['number'],f) for f in original['figures']]
    original['version']='2026-10-09'
    (HERE/'scene.json').write_text(json.dumps(original,ensure_ascii=False,indent=2),encoding='utf-8')
    print([(f['number'],f['width'],f['height']) for f in original['figures'][:3]])

if __name__=='__main__':main()
