"""Prepare evidence and native-object layouts for the PowerPoint COM builder.

This script never flattens a figure into an image. Photos are copied unchanged;
labels, axes, bars, diagrams and detection boxes become separate PPT objects.
"""
from __future__ import annotations

import json
import math
import random
import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FIGURES = HERE.parent
ROOT = FIGURES.parent.parent
GAS = Path(r"D:\gas_cylinders")
MEDIA = HERE / "media"
MEDIA.mkdir(parents=True, exist_ok=True)
W, H = 960, 640
INK, GRAY, RULE = "#202020", "#626262", "#BDBDBD"
COLORS = {"A": "#4A667D", "B": "#AD8146", "C": "#377D78", "D": "#806B91"}
PALES = {"A": "#EFF3F5", "B": "#F7F3ED", "C": "#EDF4F3", "D": "#F4F1F6"}
ARM_KEYS = {"A": "real93v4", "B": "aug1085v4", "C": "gen1085v4"}


def reviewed_labels(path):
    label_path = path.parent.parent / 'labels' / (path.stem + '.txt')
    return [[float(v) for v in row.split()[1:]] for row in label_path.read_text(encoding='utf-8').splitlines()]


def shade(value):
    low, high = (243,248,250), (3,58,74)
    t = value ** .60
    return '#' + ''.join(f'{round(a*(1-t)+b*t):02X}' for a,b in zip(low,high))


def oof_rows(key):
    data=json.loads((ROOT/'experiments/v4_protocol/per_image'/f'per_image_{key}.json').read_text())
    rows=data['joint']['oof_rows']
    assert len(rows)==61 and sum(r['n_gt'] for r in rows.values())==72
    return rows


def count_at(rows,threshold):
    gt=sum(r['n_gt'] for r in rows.values())
    tp=pred=0
    for row in rows.values():
        for mask,confidence in zip(row['tp_masks'],row['conf']):
            if confidence>=threshold:
                pred+=1
                tp+=int(bool(mask&1))
    return tp,pred-tp,gt-tp,gt


def asset(path, name=None):
    path = Path(path)
    name = name or path.name
    destination = MEDIA / name
    if not destination.exists() or destination.read_bytes() != path.read_bytes():
        shutil.copy2(path, destination)
    return "media/" + name


class Scene:
    def __init__(self, number, stem, title, old_number, notes):
        self.data = dict(number=number, old_number=old_number, stem=stem,
                         title=title, width=W, height=H, notes=notes, objects=[])
        self.objects = self.data["objects"]
        self.text(28, 18, 900, 30, title, 22, font="Times New Roman")

    def obj(self, kind, **values):
        self.objects.append(dict(kind=kind, name=f"{kind}_{len(self.objects)+1:03d}", **values))
        return self.objects[-1]

    def text(self, x, y, w, h, text, size=13, color=INK, bold=False,
             italic=False, align="left", font="Arial", fill=None, rotation=0, orientation=None):
        return self.obj("text", x=x, y=y, w=w, h=h, text=text, size=size,
                        color=color, bold=bold, italic=italic, align=align,
                        font=font, fill=fill, rotation=rotation, orientation=orientation)

    def rect(self, x, y, w, h, fill=None, stroke=RULE, weight=.65, dash=False):
        return self.obj("rect", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke,
                        weight=weight, dash=dash)

    def line(self, x1, y1, x2, y2, color=INK, weight=.75, arrow=False, dash=False):
        return self.obj("line", x1=x1, y1=y1, x2=x2, y2=y2, color=color,
                        weight=weight, arrow=arrow, dash=dash)

    def route(self, points, color=INK, weight=.75, arrow=True, dash=False):
        for index, (start, end) in enumerate(zip(points, points[1:])):
            self.line(*start, *end, color, weight,
                      arrow and index == len(points)-2, dash)

    def ellipse(self, x, y, w, h, fill=None, stroke=INK, weight=.7):
        return self.obj("ellipse", x=x, y=y, w=w, h=h, fill=fill, stroke=stroke, weight=weight)

    def box(self, x, y, w, h, title, detail=None, color=INK, fill=None,
            size=13, dash=False):
        self.rect(x, y, w, h, fill, color, .7, dash)
        if detail:
            self.text(x+8, y+7, w-16, 20, title, size, color, True, align="center")
            self.text(x+8, y+29, w-16, h-34, detail, 11.5, GRAY, align="center")
        else:
            self.text(x+7, y+(h-24)/2, w-14, 24, title, size, color, align="center")

    def photo(self, path, x, y, w, h, name=None, border=False):
        with Image.open(path) as im:
            iw, ih = im.size
        scale = min(w/iw, h/ih)
        pw, ph = iw*scale, ih*scale
        px, py = x+(w-pw)/2, y+(h-ph)/2
        self.obj("picture", x=px, y=py, w=pw, h=ph, path=asset(path, name))
        if border:
            self.rect(px, py, pw, ph, stroke=RULE, weight=.35)
        return px, py, pw, ph, iw, ih

    def panel(self, x, y, w, text):
        self.text(x, y, w, 25, text, 17, font="Times New Roman")

    def foot(self, text, y=605):
        self.text(28, y, 904, 29, text, 10.5, GRAY)


def samples():
    a_dir=GAS/'real_photo/93_real_photos'
    originals=sorted((a_dir/'images').glob('*.png'))
    assert len(originals)==93
    dropped=set(random.Random(42).sample(range(93*12),93*12-1085))
    mapped={p.stem:[] for p in originals}
    kept=0
    for pool_index in range(93*12):
        if pool_index not in dropped:
            mapped[originals[pool_index//12].stem].append(GAS/'aug1085/images'/f'aug1085_{kept:04d}.png')
            kept+=1
    s = Scene(4, "fig04_training_examples", "Training images and reviewed bounding boxes", 3,
              "Source: old fig03/draw_fig3.py; real93 seeds30/50/70 with paired aug1085 variants. "
              "C images0001/0554/0515 are independent edits, not paired to A in the same row. "
              "All image pixels remain original, with separate editable PPT rectangle labels at0.7pt. D remains reserved.")
    heads=["A  real93", "B  Classical augmentation", "C  Image editing", "D  LoRA text-to-image"]
    xs=[29, 264, 499, 734]
    for i,(x,head) in enumerate(zip(xs,heads)):
        a="ABCD"[i]
        s.text(x, 74, 199, 23, head, 12.5, bold=True)
        s.line(x, 101, x+198, 101, color=COLORS[a], weight=.7)
    for row,(seed,rank,cname) in enumerate(zip([30,50,70],[1,3,2],['Placement_Issues_0001.png','Placement_Issues_0554.png','Placement_Issues_0515.png'])):
        y=119+row*151
        ap=a_dir/"images"/f"real_photo_{seed}.png"
        cp=next(p for p in [GAS/'Placement_Issues/images'/cname,GAS/'Placement_Issues_2/images'/cname] if p.exists())
        paths=[ap,mapped[ap.stem][rank],cp]
        for col,path in enumerate(paths):
            px,py,pw,ph,iw,ih=s.photo(path,xs[col],y,199,119,border=True)
            for cx,cy,bw,bh in reviewed_labels(path):
                s.rect(px+(cx-bw/2)*pw,py+(cy-bh/2)*ph,bw*pw,bh*ph,
                       stroke="#B7212D",weight=.7)
            s.text(xs[col],y+124,199,20,path.stem,9.5,GRAY,align="center")
        s.rect(xs[3], y, 199, 119, stroke="#B6ACBE", weight=.5,dash=True)
        s.text(xs[3]+9,y+48,181,30,"D sample reserved",11,GRAY,align="center")
    s.foot("A and B are matched by real source. C samples are independent edits of other real93 images. Red boxes are reviewed labels.",y=605)
    return s


def axes(s,x,y,w,h,xlabels,ymin,ymax,ticks,ylabel):
    s.line(x,y,x,y+h,weight=.65)
    s.line(x,y+h,x+w,y+h,weight=.65)
    for v in ticks:
        yy=y+h-(v-ymin)/(ymax-ymin)*h
        s.line(x-4,yy,x,yy,weight=.6)
        s.text(x-49,yy-9,39,18,f"{v:g}",10.5,align="right")
        if abs(v)>1e-9:
            s.line(x,yy,x+w,yy,color="#E3E3E3",weight=.35)
    s.text(x-70,y+h/2-85,23,170,ylabel,11,orientation="upward",align="center")
    return lambda v:y+h-(v-ymin)/(ymax-ymin)*h


def main_results():
    source=json.loads((ROOT/"experiments/v4_protocol/bootstrap_paired.json").read_text())
    joint=[r for r in source["comparisons"] if r["target"]=="joint"]
    scores={}
    contrasts={}
    for r in joint:
        for key,point in [(r["arm_a"],r["point_a"]),(r["arm_b"],r["point_b"])]:
            scores[key]=point
        if r["arm_a"]=="real93v4":
            contrasts[r["arm_b"]]=r
    s=Scene(5,"fig05_oof_bar_comparison","Arm-level performance relative to the real93 baseline",4,
            "Source: experiments/v4_protocol/bootstrap_paired.json, target=joint. "
            "Panel a shows joint detector+checkpoint cross-fitted pooled OOF mAP50-95. "
            "Panel b shows observed paired differences against real93 and95% paired image-cluster bootstrap CIs. "
            "10000 bootstrap resamples,61 dev images. No marginal absolute AP CI is invented. D pending, not zero.")
    s.panel(29,74,432,"(a) Pooled OOF mAP50–95")
    s.panel(507,74,432,"(b) Difference from real93")
    yy=axes(s,92,150,343,347,None,0,1,[0,.2,.4,.6,.8,1],"mAP50–95")
    for i,a in enumerate("ABCD"):
        cx=132+i*82
        if a in ARM_KEYS:
            v=scores[ARM_KEYS[a]]["mAP50-95"]
            s.rect(cx-22,yy(v),44,yy(0)-yy(v),COLORS[a],None)
            s.text(cx-35,yy(v)-27,70,21,f"{v:.3f}",12,align="center")
        else:
            s.text(cx-37,410,74,30,"Pending",11,GRAY,italic=True,align="center")
        s.text(cx-37,508,74,20,a,12,bold=True,align="center")
        s.text(cx-39,535,78,32,{"A":"93 real","B":"1,085 aug.","C":"1,085 edits","D":"1,085 target"}[a],10.5,GRAY,align="center")
    y2=axes(s,565,150,360,347,None,-.25,.35,[-.2,-.1,0,.1,.2,.3],"Δ mAP50–95")
    s.line(565,y2(0),925,y2(0),color=INK,weight=.8)
    for i,a in enumerate("BCD"):
        cx=630+i*115
        if a in ARM_KEYS:
            r=contrasts[ARM_KEYS[a]]
            v=r["observed_delta"]["mAP50-95"]
            lo,hi=r["mAP50-95"]["ci95"]
            s.rect(cx-24,min(y2(v),y2(0)),48,abs(y2(v)-y2(0)),COLORS[a],None)
            s.line(cx,y2(lo),cx,y2(hi),weight=.7)
            s.line(cx-8,y2(lo),cx+8,y2(lo),weight=.7)
            s.line(cx-8,y2(hi),cx+8,y2(hi),weight=.7)
            ty=y2(hi)-24 if v>0 else y2(lo)+8
            s.text(cx-49,ty,98,22,f"{v:+.3f}",12,align="center")
        else:
            s.text(cx-45,270,90,28,"Pending",11,GRAY,italic=True,align="center")
        s.text(cx-49,508,98,22,a+" − A",12,align="center")
    secondary="  ".join(f"{a}: {scores[ARM_KEYS[a]]['mAP50']:.3f}" for a in "ABC")
    s.text(29,580,420,22,"Secondary mAP50: "+secondary,10.5,GRAY)
    s.text(507,580,425,22,"Error bars: paired 95% bootstrap interval",10.5,GRAY)
    s.foot("Development analysis on dev61 (n = 61). Model and checkpoint selection use five-fold cross-fitting. D results remain empty.")
    return s


def heatmaps():
    detectors=[('yolov8s','v8s'),('yolov8m','v8m'),('yolo11s','11s'),('yolo11m','11m'),('yolo26s','26s'),('yolo26m','26m')]
    values={}
    for a,key in ARM_KEYS.items():
        data=json.loads((ROOT/'experiments/v4_protocol'/f'v4_protocol_{key}.json').read_text())
        values[a]={}
        for name,_ in detectors:
            fixed=data['arms'][key]['detectors'][name]['fixed_endpoint']
            assert fixed['epoch']==300
            values[a][name]=fixed['metrics']
    s=Scene(6,"fig06_detector_comparison","Fixed-endpoint performance across six YOLO detectors",5,
            "Source: experiments/v4_protocol/v4_protocol_{real93v4,aug1085v4,gen1085v4}.json, fixed_endpoint at epoch300. "
            "Shared AP0..1 colour scale; numeric labels>=0.500 white, lower labels black, as requested by author. "
            "D cells empty; these are dev61 fixed-endpoint development scores, not joint OOF or final-test performance.")
    metrics=["mAP50-95","mAP50"]
    xpos=[160,556]
    rowys=[175,257,339,421]
    for pi,(metric,x) in enumerate(zip(metrics,xpos)):
        s.panel(x,83,362,f"({chr(97+pi)})  "+metric.replace("-","–"))
        for j,(_,name) in enumerate(detectors):
            xx=x+j*60
            s.text(xx,134,55,22,name,12,align="center")
        for row,a in enumerate("ABCD"):
            for j,(key,_) in enumerate(detectors):
                xx=x+j*60
                yy=rowys[row]
                if a in values:
                    v=values[a][key][metric]
                    s.rect(xx,yy,55,64,shade(v),None)
                    s.text(xx+1,yy+20,53,22,f"{v:.3f}",12,'#FFFFFF' if float(f'{v:.3f}')>=.5 else '#000000',align="center")
                else:
                    s.rect(xx,yy,55,64,stroke="#B6ACBE",weight=.5,dash=True)
    for i,a in enumerate("ABCD"):
        s.text(29,rowys[i]+11,120,24,a+"  "+{"A":"real93","B":"Augmented","C":"Image edit","D":"LoRA T2I"}[a],12,bold=True)
        s.text(29,rowys[i]+35,120,18,"93 images" if a=="A" else ("1,085 images" if a!="D" else "Pending"),10.5,GRAY)
    s.text(160,534,110,22,"Shared AP scale",11)
    for i in range(50):
        s.rect(280+i*4.0,540,4,12,shade(i/49),None)
    s.text(276,557,25,18,"0",10.5)
    s.text(466,557,25,18,"1",10.5,align="right")
    s.text(555,536,375,38,"D cells reserved\nLabel colour changes to white at AP ≥ 0.50",11,GRAY)
    s.foot("Epoch 300 (last.pt), dev61. Both panels use the same colour scale. Detector labels denote model family and size.")
    return s


def tradeoff():
    s=Scene(8,"fig08_operating_tradeoff","Missed objects and false positives across confidence thresholds",7,
            "Source: experiments/v4_protocol/per_image/per_image_{real93v4,aug1085v4,gen1085v4}.json joint OOF caches. "
            "61 development images,72 GT objects,IoU.50. Thresholds.05..95 plus.25,.50. "
            "Curves are native line segments, not images; only successive unique operating points retained. D pending.")
    s.panel(29,75,575,"(a) Pooled held-out operating curves")
    s.panel(695,75,240,"(b) Confidence ≥ 0.25")
    x,y,w,h=97,158,538,354
    s.line(x,y,x,y+h,weight=.65)
    s.line(x,y+h,x+w,y+h,weight=.65)
    for v in [0,.1,.2,.3,.4,.5,.6,.7]:
        xx=x+w*v/.7
        s.line(xx,y+h,xx,y+h+4,weight=.6)
        s.text(xx-16,y+h+9,32,19,f"{v:.1f}",10.5,align="center")
    for v in [0,.2,.4,.6,.8,1]:
        yy=y+h-v*h
        s.line(x-4,yy,x,yy,weight=.6)
        s.text(x-41,yy-9,30,18,f"{v:.1f}",10.5,align="right")
        if v not in [0,1]:s.line(x,yy,x+w,yy,color="#E1E1E1",weight=.35)
    s.text(153,556,485,24,"False positives per development image (FP / 61)",12,align="center")
    s.text(24,221,24,237,"Missed objects (FN / 72)",12,orientation="upward",align="center")
    s.text(699,145,229,22,"Arm        Missed      FP / image",11,bold=True)
    s.line(696,174,931,174,color=RULE,weight=.55)
    for i,a in enumerate("ABC"):
        data=oof_rows(ARM_KEYS[a])
        points=[]
        ts=sorted(set([.05+j*.90/130 for j in range(131)]+[.25,.5]))
        for t in ts:
            tp,fp,fn,gt=count_at(data,t)
            point=(fp/61,fn/gt)
            if not points or point!=points[-1]:points.append(point)
        for p1,p2 in zip(points,points[1:]):
            # The original cache's range fits the chosen FP axis.
            assert max(p1[0],p2[0])<=.7
            s.line(x+w*p1[0]/.7,y+h-p1[1]*h,x+w*p2[0]/.7,y+h-p2[1]*h,color=COLORS[a],weight=1.15)
        for t,filled in [(.25,True),(.5,False)]:
            tp,fp,fn,gt=count_at(data,t)
            xx=x+w*(fp/61)/.7
            yy=y+h-(fn/gt)*h
            s.ellipse(xx-4,yy-4,8,8,COLORS[a] if filled else "#FFFFFF",COLORS[a],.8)
        tp,fp,fn,gt=count_at(data,.25)
        yy=203+i*71
        s.text(699,yy,45,24,a,13,COLORS[a],True)
        s.text(760,yy,76,24,f"{fn}/{gt}",12,align="center")
        s.text(850,yy,78,24,f"{fp/61:.3f}",12,align="center")
        s.line(696,yy+40,931,yy+40,color="#D4D4D4",weight=.45)
    s.text(699,417,45,24,"D",13,COLORS["D"],True)
    s.text(760,417,76,24,"—",12,GRAY,align="center")
    s.text(850,417,78,24,"—",12,GRAY,align="center")
    s.text(699,464,231,27,"D curve and counts pending",11,GRAY)
    for i,a in enumerate("ABC"):
        xx=101+i*169
        s.line(xx,126,xx+28,126,color=COLORS[a],weight=1.1)
        s.text(xx+36,116,117,23,{"A":"A  real93","B":"B  Augmented","C":"C  Image edit"}[a],11.5)
    s.ellipse(717,546,8,8,INK,INK,.7)
    s.text(734,539,190,23,"Filled: confidence 0.25",10.5)
    s.ellipse(717,572,8,8,"#FFFFFF",INK,.7)
    s.text(734,566,190,23,"Open: confidence 0.50",10.5)
    s.foot("IoU = 0.50; confidence thresholds 0.05–0.95. Each dev61 image contributes only predictions from its held-out fold.")
    return s


def scale_effect():
    source=json.loads((ROOT/'experiments/v4_protocol/bootstrap_paired_L3.json').read_text())
    step=next(r for r in source['comparisons'] if r['target']=='joint')
    assert (step['arm_a'],step['arm_b'])==('gen493v4','gen1085v4')
    baseline_source=json.loads((ROOT/'experiments/v4_protocol/bootstrap_paired.json').read_text())
    baseline=next(r['point_a'] for r in baseline_source['comparisons'] if r['target']=='joint' and r['arm_a']=='real93v4')
    s=Scene(7,'fig07_image_edit_scale','Effect of the image-edit training-set size',6,
            'Sources: experiments/v4_protocol/bootstrap_paired_L3.json target=joint, bootstrap_paired.json for real93 context. '
            '493 is a subset of1085, same image-edit recipe and300-epoch protocol. Only493 and1085 form the synthesis size comparison. '
            'Real93 open marker is context and is not joined to the C scale line. Pooled held-out joint detector/checkpoint OOF, '
            'paired95% image-cluster bootstrap10000 resamples. No D size experiment has been performed.')
    s.ellipse(94,125,8,8,'#FFFFFF',COLORS['A'],.8)
    s.text(110,115,213,27,'Real93 context (arm A)',11.5)
    s.line(340,129,371,129,color=COLORS['C'],weight=1.1)
    s.ellipse(352,125,8,8,COLORS['C'],COLORS['C'],.8)
    s.text(380,115,301,27,'Image-edit size comparison (arm C)',11.5)
    for index,(metric,x) in enumerate([('mAP50-95',92),('mAP50',565)]):
        s.panel(x-63,75,420,f'({chr(97+index)})  '+metric.replace('-','–'))
        y=181;w=343;h=310
        yy=axes(s,x,y,w,h,None,0,1,[0,.2,.4,.6,.8,1],'Pooled OOF AP')
        xx=lambda n:x+w*n/1200
        s.line(xx(493),yy(step['point_a'][metric]),xx(1085),yy(step['point_b'][metric]),color=COLORS['C'],weight=1.1)
        for n,point,is_c in [(93,baseline,False),(493,step['point_a'],True),(1085,step['point_b'],True)]:
            v=point[metric]
            col=COLORS['C'] if is_c else COLORS['A']
            s.ellipse(xx(n)-4,yy(v)-4,8,8,col if is_c else '#FFFFFF',col,.8)
            s.text(xx(n)-35,yy(v)-28,70,21,f'{v:.3f}',12,align='center')
            s.line(xx(n),y+h,xx(n),y+h+4,weight=.6)
            s.text(xx(n)-37,506,74,20,f'{n:,}',11.5,align='center')
        s.text(x+45,532,258,22,'Number of training images',12,align='center')
        delta=step['observed_delta'][metric]
        lo,hi=step[metric]['ci95']
        s.text(x-63,566,427,24,f'493 → 1,085: Δ = {delta:+.3f}',13,align='center')
        s.text(x-63,591,427,23,f'Paired 95% CI [{lo:+.3f}, {hi:+.3f}]',11,GRAY,align='center')
    s.foot('dev61 development analysis. The real93 point provides context; only the two edited-image points form the size comparison.',y=615)
    return s


def cases():
    cache=json.loads((ROOT/'experiments/v4_protocol/qualitative_detections.json').read_text())
    examples=[('new_test_set_0014.jpg',2,{'real93v4':1,'aug1085v4':0,'gen1085v4':1}),
              ('new_test_set_0006.jpg',0,{'real93v4':1,'aug1085v4':0,'gen1085v4':0}),
              ('new_test_set_0005.jpg',1,{'real93v4':2,'aug1085v4':1,'gen1085v4':1})]
    s=Scene(11,"fig11_detection_cases","Detection examples on the development images",10,
            "Source: experiments/v4_protocol/qualitative_detections.json and reviewed GT labels, dev61 images0014/0006/0005. "
            "Deployment weights: A yolo26s epoch280, B yolo26s epoch200, C yolo26s epoch260, conf>=.25. "
            "These hand-selected cases are illustrative, not frequency estimates. Predictions here use deployment weights, "
            "while quantitative figures5/8 use held-out OOF. D blank. Image, each box and each confidence label are independent objects.")
    xs=[28,213,398,583,768]
    heads=["Reviewed GT","A  real93","B  Augmented","C  Image edit","D  LoRA T2I"]
    for i,(x,head) in enumerate(zip(xs,heads)):
        s.text(x,67,165,24,head,12,bold=True,align="center")
    for row,(name,ngt,ncounts) in enumerate(examples):
        y=119+row*153
        brief=["(a) Fallen cylinders", "(b) Background false positive", "(c) Multiple predictions"][row]
        s.text(28,y-21,610,21,brief,12,bold=True)
        s.text(651,y-21,282,21,name.removesuffix(".jpg"),9.5,GRAY,align="right")
        entry=cache["images"][name]
        path=Path(entry["path"])
        with Image.open(path) as im:iw,ih=im.size
        gt=[((cx-bw/2)*iw,(cy-bh/2)*ih,(cx+bw/2)*iw,(cy+bh/2)*ih) for cx,cy,bw,bh in reviewed_labels(path)]
        assert len(gt)==ngt
        allboxes=[[(b,None) for b in gt]]
        for a in "ABC":
            det=[d for d in entry["arms"][ARM_KEYS[a]] if d["conf"]>=.25]
            assert len(det)==ncounts[ARM_KEYS[a]]
            allboxes.append([(d["xyxy"],d["conf"]) for d in det])
        for col,rows in enumerate(allboxes):
            px,py,pw,ph,iw,ih=s.photo(path,xs[col],y,165,124,border=True)
            colr="#B7212D" if col==0 else COLORS["ABC"[col-1]]
            for box,conf in rows:
                x1,y1,x2,y2=box
                bx=px+x1/iw*pw
                by=py+y1/ih*ph
                bw=(x2-x1)/iw*pw
                bh=(y2-y1)/ih*ph
                s.rect(bx,by,bw,bh,stroke=colr,weight=.7,dash=col==0)
                if conf is not None:
                    # Explicit score textbox with white fill, no baked image labels.
                    ly=max(py,min(by-12,py+ph-15))
                    lx=min(bx,px+pw-32)
                    s.text(lx,ly,32,13,f"{conf:.2f}",8.5,colr,fill="#FFFFFF")
        s.rect(xs[4],y,165,124,stroke="#B6ACBE",weight=.5,dash=True)
        s.text(xs[4]+8,y+49,149,22,"D output reserved",11,GRAY,align="center")
    s.text(28,586,904,19,"Dashed red boxes: reviewed GT. Solid coloured boxes: detections at confidence ≥ 0.25.",10.5,GRAY)
    s.foot("Hand-selected illustrations using deployment checkpoints on dev61. Their occurrence does not estimate error rates.",y=610)
    return s


def main():
    existing=json.loads((HERE/'scene.json').read_text(encoding='utf-8'))
    from revise_first_three import revised_figures
    scenes=revised_figures(existing['figures'])+[samples(),main_results(),heatmaps(),scale_effect(),tradeoff(),cases()]
    data=dict(version="2026-10-06",description="Native editable PowerPoint figure drafts",figures=[s.data for s in scenes])
    (HERE/"scene.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps([dict(number=s.data['number'],objects=len(s.objects),stem=s.data['stem']) for s in scenes],indent=2))


if __name__=="__main__":main()
