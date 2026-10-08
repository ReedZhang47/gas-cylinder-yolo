"""Three distinct native PowerPoint figures; all labels remain editable."""
import json
from prepare_figures import Scene, HERE, COLORS

BLACK = '#181818'
RULE = '#B7BCC0'
TEAL = '#266A71'
PURPLE = '#624978'
SERIF = 'Times New Roman'


def base(old, width, height):
    s = Scene(old['number'], old['stem'], old['title'], old['old_number'], old['notes'])
    s.objects.clear()
    s.data.update(width=width, height=height)
    return s


def tx(s, x, y, w, h, text, size=14, bold=False, font=SERIF, color=BLACK,
       align='left', italic=False):
    s.text(x, y, w, h, text, size, color, bold, italic, align, font)


def label(s, x, y, w, text, size=12, color=BLACK, bold=False, align='left', h=23):
    tx(s, x, y, w, h, text, size, bold, 'Arial', color, align)


def photo(s, name, x, y, w, h):
    return s.photo(HERE/'media'/name, x, y, w, h, border=True)


def down(s, x, y1, y2, color=BLACK):
    s.line(x, y1, x, y2, color=color, weight=.75, arrow=True)


def fig1(old):
    """Open horizontal research scheme with arm rows, a model matrix and branches."""
    s = base(old, 1330, 408)
    for x, w, title in [(24,550,'(a) Data construction'),
                         (634,254,'(b) Controlled training'),
                         (950,356,'(c) Development evaluation')]:
        tx(s,x,15,w,30,title,18,bold=True)
        s.line(x,52,x+w,52,color=BLACK,weight=.8)
    tx(s,28,127,145,29,'real93',22,bold=True,align='center')
    photo(s,'source_on_site.jpg',28,166,145,98)
    tx(s,24,278,157,52,'93 real photographs\nOn-site and web sources',13,align='center')
    s.line(181,215,201,215)
    s.line(201,111,201,336)
    rows=[('A',78,'Real-only baseline','Reviewed labels','93'),
          ('B',153,'Classical augmentation','Offline transformations','1,085'),
          ('C',228,'Image editing','Reviewed synthetic images','1,085'),
          ('D',303,'LoRA text-to-image','1,308 candidates; screening pending','1,085*')]
    for arm,y,title,detail,count in rows:
        col=COLORS[arm]
        s.line(201,y+33,229,y+33,color=col,arrow=True)
        s.rect(233,y+5,27,27,fill=col,stroke=None)
        label(s,233,y+6,27,arm,14,'#FFFFFF',True,'center',25)
        tx(s,270,y,238,29,title,16,bold=True)
        tx(s,270,y+31,253,26,detail,12)
        tx(s,512,y+2,68,28,count,19,color=col,align='right')
        s.line(270,y+61,580,y+61,color=RULE,weight=.45,dash=arm=='D')
        s.line(582,y+33,606,y+33,color=col,dash=arm=='D')
    s.line(606,111,606,336,weight=.65)
    s.line(606,210,632,210,arrow=True)
    label(s,637,74,245,'Six detectors per arm',13,bold=True,align='center')
    label(s,650,111,126,'Model family',11,bold=True)
    label(s,794,111,32,'s',13,bold=True,align='center')
    label(s,850,111,32,'m',13,bold=True,align='center')
    s.line(647,139,885,139,weight=.65)
    for i,model in enumerate(['YOLOv8','YOLO11','YOLO26']):
        y=148+38*i
        tx(s,650,y,138,27,model,16)
        for x in [805,861]:
            s.ellipse(x,y+9,8,8,fill=BLACK,stroke=None)
        s.line(647,y+32,885,y+32,color=RULE,weight=.4)
    down(s,765,259,279)
    tx(s,650,286,236,28,'300 epochs per run',17,bold=True,align='center')
    tx(s,646,320,245,43,'Checkpoints every 10 epochs\nand final last.pt',14,align='center')
    s.route([(890,333),(920,333),(920,145),(967,145)],weight=.7)
    s.rect(950,76,356,48,fill='#F3F3F1',stroke=None)
    tx(s,961,82,71,29,'dev61',20,bold=True)
    tx(s,1040,80,255,33,'61 development images\nExcluded from detector training',12)
    s.route([(1128,124),(1128,145),(967,145),(967,335)],arrow=False)
    for y,title,line1,line2 in [
        (167,'Fixed endpoint','last.pt evaluated on dev61',''),
        (240,'Five-fold cross-fitting','Joint model + checkpoint; pooled OOF','Paired bootstrap: 10,000 resamples'),
        (321,'Deployment selection','All dev61; development score','')]:
        s.line(967,y+14,992,y+14,arrow=True)
        tx(s,1001,y-2,305,27,title,17,bold=True)
        tx(s,1001,y+28,305,23,line1,13)
        if line2:tx(s,1001,y+49,305,23,line2,12)
    tx(s,24,379,1282,20,'* D target: 1,085 images after screening and reviewed annotation; detector results remain pending.',11,italic=True)
    return s


def circuit_box(s,x,y,w,h,title,detail='',fill='#EEF5F5',color=TEAL):
    s.rect(x,y,w,h,fill=fill,stroke=color,weight=.65)
    label(s,x+12,y+7,w-24,title,12,color,True,h=25)
    if detail:tx(s,x+12,y+35,w-24,h-40,detail,14)


def fig2(old):
    """Signal-flow schematic: conditioning branches and a denoising core."""
    s=base(old, 920, 754)
    label(s,24,14,449,'(a) Conditioning and model preparation',16,bold=True,h=30)
    label(s,529,14,367,'(b) Sampling and dataset assembly',16,bold=True,h=30)
    s.line(24,53,465,53,color=TEAL,weight=1.1)
    s.line(529,53,896,53,color=TEAL,weight=1.1)
    photo(s,'source_on_site.jpg',51,77,138,92)
    tx(s,44,176,153,25,'Reference photograph',14,align='center')
    s.rect(252,81,193,94,fill='#F6F6F3',stroke=RULE,weight=.45)
    label(s,265,88,167,'Edit instruction',12,bold=True)
    tx(s,265,118,163,46,'Target safety state\nand scene description',14)
    down(s,121,204,231)
    down(s,348,175,231)
    s.route([(190,125),(218,125),(218,219),(321,219),(321,231)],color=TEAL,weight=.65)
    circuit_box(s,49,231,160,81,'Image encoding','Scale + Qwen VAE')
    circuit_box(s,252,231,193,81,'Multimodal encoding','Qwen2.5-VL 7B\nFP8 text encoder')
    tx(s,54,319,150,25,'Image latent',13,italic=True,align='center')
    tx(s,266,319,167,25,'Text conditioning',13,italic=True,align='center')
    s.route([(121,344),(121,354),(31,354),(31,622),(56,622)],color=TEAL)
    s.route([(348,344),(348,354),(463,354),(463,594),(396,594),(396,606)],color=TEAL)
    s.rect(66,378,361,185,fill='#F7F9F9',stroke=RULE,weight=.5)
    label(s,81,384,331,'Qwen-Image-Edit-2509',14,TEAL,True)
    tx(s,81,412,331,24,'FP8 diffusion model',14)
    s.line(81,444,412,444,color=RULE,weight=.45)
    tx(s,82,454,139,25,'Standard path',14,bold=True)
    tx(s,246,454,164,25,'Lightning LoRA',14,bold=True)
    tx(s,246,480,164,23,'Optional four-step path',12,italic=True)
    s.line(231,453,231,507,color=RULE,weight=.45)
    down(s,151,506,523)
    down(s,328,506,523)
    s.rect(82,524,330,28,fill='#E3EEEE',stroke=None)
    label(s,88,526,318,'Model preparation: AuraFlow / CFGNorm',11.5,align='center')
    down(s,247,563,606,TEAL)
    s.rect(56,606,371,47,fill='#FFFFFF',stroke=TEAL,weight=.9)
    label(s,68,613,347,'Latent + conditioning + model',13,TEAL,True,h=30)
    s.route([(427,630),(494,630),(494,270),(529,270)],color=TEAL,weight=1)
    tx(s,62,674,359,40,'Prepared inputs enter the denoising process.',14,italic=True)
    for row in range(4):
        for col in range(4):
            shade=['#DCE8E9','#95B8BB','#BFD4D6','#EDF3F3'][(row*3+col)%4]
            s.rect(564+col*12,86+row*12,11,11,fill=shade,stroke=None)
    tx(s,641,82,242,29,'Noise latent',18,bold=True)
    tx(s,641,116,242,24,'Target size and random seed',14)
    s.route([(714,151),(714,197)],color=TEAL)
    s.rect(529,197,367,154,fill='#EAF3F3',stroke=TEAL,weight=1)
    label(s,546,207,333,'Denoising / KSampler',15,TEAL,True,h=28)
    tx(s,546,243,333,27,'Conditioned iterative sampling',15)
    for x,value in [(558,'T'),(685,'t'),(819,'0')]:
        s.rect(x,286,50,39,fill='#FFFFFF',stroke=TEAL,weight=.6)
        tx(s,x+12,289,22,30,'z',23,italic=True)
        tx(s,x+28,303,18,18,value,12,italic=True)
    s.line(608,306,685,306,color=TEAL,arrow=True)
    s.line(735,306,819,306,color=TEAL,arrow=True)
    down(s,714,351,383,TEAL)
    circuit_box(s,558,383,310,66,'VAE decode','Qwen image VAE',fill='#FFFFFF')
    down(s,714,449,478,TEAL)
    photo(s,'Placement_Issues_0001.png',550,480,161,122)
    tx(s,740,489,151,30,'Generated edit',17,bold=True)
    tx(s,740,529,151,66,'Scene content\nSafety state\nImage quality',14)
    down(s,714,603,628,TEAL)
    label(s,547,628,336,'Human review and YOLO annotation',12.5,bold=True,h=28)
    down(s,714,662,681,TEAL)
    tx(s,548,682,344,31,'Arm C: 1,085 retained images',20,bold=True,color=TEAL)
    s.line(548,717,891,717,color=TEAL,weight=1)
    tx(s,24,729,872,19,'Reference and retained example are unpaired; four-step acceleration is optional.',11,italic=True)
    return s


def section_title(s,x,y,w,title):
    tx(s,x,y,w,28,title,17,bold=True)
    s.line(x,y+34,x+w,y+34,color=BLACK,weight=.65)


def kv(s,x,y,w,key,value,key_width=145):
    label(s,x,y,key_width-10,key,11.5,h=25)
    tx(s,x+key_width,y,w-key_width,25,value,14)


def fig3(old):
    """LoRA mechanism plus aligned parameter schedules for training/inference."""
    s=base(old,1080,896)
    tx(s,24,14,470,31,'(a) LoRA fitting on real93',20,bold=True)
    tx(s,588,14,468,31,'(b) Text-to-image generation',20,bold=True)
    s.line(24,54,494,54,color=PURPLE,weight=1)
    s.line(588,54,1056,54,color=PURPLE,weight=1)
    photo(s,'source_on_site.jpg',40,76,141,95)
    tx(s,211,72,277,29,'93 reviewed image–caption pairs',17,bold=True)
    kv(s,211,110,276,'Source','real93',95)
    kv(s,211,143,276,'Trigger','cylsite93',95)
    s.route([(111,176),(111,207)],color=BLACK)
    s.route([(356,176),(356,207)],color=BLACK)
    for x,w,title in [(39,181,'Image VAE encoder'),(273,220,'Text encoder')]:
        s.rect(x,207,w,42,fill='#F2F2F0',stroke=None)
        label(s,x+8,216,w-16,title,12.5,bold=True,align='center')
    s.route([(130,249),(130,268),(263,268)],arrow=False)
    s.route([(383,249),(383,268),(263,268),(263,294)])
    s.rect(39,294,454,185,stroke=PURPLE,weight=.75)
    tx(s,55,300,422,28,'Qwen-Image-2.1 DiT',19,bold=True,align='center')
    label(s,77,337,146,'Frozen base',12,bold=True,align='center')
    label(s,291,337,163,'Trainable adapter',12,PURPLE,True,'center')
    s.rect(121,369,59,59,fill='#E7E7E3',stroke=BLACK,weight=.55)
    tx(s,121,379,59,39,'W',28,italic=True,align='center')
    tx(s,224,378,48,42,'+',27,align='center')
    s.rect(312,373,14,55,fill='#E2D8EB',stroke=PURPLE,weight=.65)
    s.rect(349,373,55,14,fill='#E2D8EB',stroke=PURPLE,weight=.65)
    tx(s,329,389,18,28,'×',16,color=PURPLE,align='center')
    tx(s,301,432,45,28,'B',18,italic=True,color=PURPLE,align='center')
    tx(s,353,390,46,28,'A',18,italic=True,color=PURPLE,align='center')
    tx(s,400,404,79,27,'rank 16',13,color=PURPLE)
    down(s,263,479,505)
    section_title(s,39,506,454,'Optimization settings')
    for y,key,value in [
        (548,'Framework','DiffSynth-Studio SFT'),
        (579,'Loss','FlowMatchSFTLoss'),
        (610,'Optimizer','AdamW'),
        (641,'Learning rate','1e-4  (constant)'),
        (672,'Batch / max pixels','1 / 1,048,576')]:
        kv(s,48,y,434,key,value,151)
        s.line(48,y+29,481,y+29,color=RULE,weight=.35)
    label(s,48,712,426,'Images × repeats × epochs',11.5,bold=True)
    tx(s,48,738,430,33,'93 × 5 × 4 = 1,860 optimizer steps',20,color=PURPLE)
    down(s,263,776,801,PURPLE)
    s.rect(39,801,454,62,fill='#F2EDF6',stroke=None)
    label(s,54,805,424,'FINAL LORA CHECKPOINT',11,PURPLE,True)
    tx(s,54,834,424,24,'step-1860.safetensors',16)
    s.route([(493,832),(550,832),(550,322),(588,322)],color=PURPLE,weight=.9)
    for x,title,n,formula in [(600,'real93 prompts','558','93 prompts × 6'),
                            (849,'new150 prompts','750','150 prompts × 5')]:
        label(s,x,70,196,title,12,bold=True,align='center')
        tx(s,x,100,196,36,n,28,color=PURPLE,align='center')
        tx(s,x,142,196,23,formula,14,align='center')
    s.line(829,73,829,167,color=RULE,weight=.5)
    s.route([(698,171),(698,181),(829,181)],arrow=False)
    s.route([(947,171),(947,181),(829,181),(829,199)])
    s.rect(602,199,439,56,fill='#F2F2F0',stroke=None)
    label(s,615,203,413,'Text conditioning',12,bold=True)
    tx(s,615,229,413,23,'Qwen3VL 8B (INT8)',15)
    down(s,829,255,282)
    s.rect(588,282,468,89,stroke=PURPLE,weight=.75)
    tx(s,604,288,436,29,'Qwen-Image-2.1 + LoRA',19,bold=True)
    kv(s,604,326,437,'Base / adapter','INT8 convrot / step-1860',125)
    down(s,829,371,397,PURPLE)
    section_title(s,602,399,439,'Generation settings')
    for y,key,value in [
        (440,'Adapter strength','0.8'),
        (471,'Sampler / schedule','Euler / simple'),
        (502,'Steps / CFG','25 / 1'),
        (533,'Seed / denoise','Random / 1'),
        (564,'Size / batch','1184 × 896 / 1'),
        (595,'Negative prompt','Empty')]:
        kv(s,609,y,423,key,value,160)
        s.line(609,y+29,1035,y+29,color=RULE,weight=.35)
    down(s,829,628,649)
    label(s,605,652,438,'VAE decode → PNG with metadata',12.5,bold=True,h=28)
    tx(s,605,681,438,23,'Qwen-Image-2.1 VAE',13)
    down(s,829,706,725)
    photo(s,'D_candidate_R030.png',604,730,122,78)
    photo(s,'D_candidate_N114.png',741,730,122,78)
    tx(s,886,727,166,35,'1,308',25,bold=True,color=PURPLE)
    tx(s,886,766,166,43,'Generated candidates\nUnscreened examples',13)
    down(s,829,811,833,PURPLE)
    s.line(602,833,1041,833,color=PURPLE,weight=.65,dash=True)
    tx(s,602,839,439,26,'Review + annotation: target 465 + 620 = 1,085',16,bold=True)
    tx(s,602,870,439,19,'Dataset review and detector results pending.',11,italic=True)
    return s


def revised_figures(figures):
    old={f['number']:f for f in figures}
    return [fig1(old[1]),fig2(old[2]),fig3(old[3])]


def main():
    original=json.loads((HERE/'scene.json').read_text(encoding='utf-8'))
    revised={s.data['number']:s.data for s in revised_figures(original['figures'])}
    original['figures']=[revised.get(f['number'],f) for f in original['figures']]
    (HERE/'scene.json').write_text(json.dumps(original,ensure_ascii=False,indent=2),encoding='utf-8')
    print([(f['number'],f['width'],f['height']) for f in original['figures'][:3]])


if __name__=='__main__':main()
