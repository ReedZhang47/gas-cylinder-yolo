"""Package the three editable figures as self-contained PPTD companions.

The native PowerPoint output is authoritative for this COM-authored project.
PPTD pages mirror the native scene object-for-object and carry embedded assets.
"""
from pathlib import Path
import json,shutil,zipfile
from lxml import etree as ET

HERE=Path(__file__).resolve().parent
P='http://schemas.openxmlformats.org/presentationml/2006/main'
MC='http://schemas.openxmlformats.org/markup-compatibility/2006'


def root_fade(path):
    """Normalize Office AlternateContent to one schema-ordered fade transition."""
    with zipfile.ZipFile(path) as z:
        items=[(i,z.read(i.filename)) for i in z.infolist()]
    fixed=[]
    for info,data in items:
        if info.filename=='ppt/slides/slide1.xml':
            e=ET.fromstring(data)
            for child in list(e):
                if child.tag==f'{{{P}}}transition' or (child.tag==f'{{{MC}}}AlternateContent' and child.find(f'.//{{{P}}}transition') is not None):e.remove(child)
            tr=ET.Element(f'{{{P}}}transition',spd='med');ET.SubElement(tr,f'{{{P}}}fade')
            index=1
            if len(e)>1 and e[1].tag==f'{{{P}}}clrMapOvr':index=2
            e.insert(index,tr)
            data=ET.tostring(e,xml_declaration=True,encoding='UTF-8',standalone=True)
        fixed.append((info,data))
    temp=path.with_suffix('.finalizing.pptx')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        for info,data in fixed:z.writestr(info,data)
    temp.replace(path)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        e=ET.fromstring(z.read('ppt/slides/slide1.xml'))
        assert len(e.findall(f'{{{P}}}transition'))==1
        assert e.find(f'{{{P}}}transition/{{{P}}}fade') is not None
        assert any(n.startswith('ppt/fonts/') for n in z.namelist())


def element(o):
    kind=o['kind']; e={'elementId':o['name']}
    if kind=='line':
        x1,y1,x2,y2=[o[k] for k in ['x1','y1','x2','y2']]
        w,h=abs(x2-x1),abs(y2-y1)
        e.update(elementType='line',bounds=[min(x1,x2),min(y1,y2),w,h],viewBox=[max(w,1),max(h,1)],points=f'{x1-min(x1,x2)},{y1-min(y1,y2)} {x2-min(x1,x2)},{y2-min(y1,y2)}',curve='sharp',border={'style':'dash' if o.get('dash') else 'solid','width':o['weight'],'color':o['color']})
        if o.get('arrow'):e['arrow']=[None,'arrow']
        return e
    e['bounds']=[o[k] for k in ['x','y','w','h']]
    if o.get('rotation'):e['rotation']=o['rotation']
    if o.get('shadow'):e['shadow']={'blur':4,'color':'#0000002E','offset':[2,3]}
    if kind=='text':
        e.update(elementType='text',content={'text':o['text'],'fontFamily':o['font'],'fontSize':o['size'],'color':o['color'],'bold':o['bold'],'italic':o['italic'],'align':[o['align'],'middle'],'lineHeight':1,'wrap':True})
    elif kind=='picture':e.update(elementType='image',src=o['path'],fit={'mode':'contain'})
    else:
        e.update(elementType='shape',shapeName={'roundrect':'roundRect'}.get(kind,kind))
        if kind=='roundrect':e['adjustments']=[8000]
        if o.get('fill'):e['fill']={'type':'solid','color':o['fill']}
        if o.get('stroke'):e['border']={'style':'dash' if o.get('dash') else 'solid','width':o['weight'],'color':o['stroke']}
    return e


def main():
    data=json.loads((HERE/'scene.json').read_text(encoding='utf-8'))
    out=HERE/'first_three_project';out.mkdir(exist_ok=True)
    for f in data['figures'][:3]:
        dest=out/f['stem'];(dest/'pages').mkdir(parents=True,exist_ok=True);(dest/'media').mkdir(exist_ok=True)
        pptx=HERE/(f['stem']+'.pptx');root_fade(pptx)
        manifest={'version':'v2','title':f['title'],'size':[f['width'],f['height']],'pages':['pages/figure.page']}
        page={'pageType':'research_figure','background':{'type':'solid','color':'#FFFFFF'},'notes':f['notes'],'elements':[element(o) for o in f['objects']]}
        # JSON is a strict YAML 1.2 subset and avoids an extra packaging dependency.
        (dest/'figure.pptd').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        (dest/'pages/figure.page').write_text(json.dumps(page,ensure_ascii=False,indent=2),encoding='utf-8')
        for o in f['objects']:
            if o['kind']=='picture':shutil.copy2(HERE/o['path'],dest/o['path'])
        shutil.copy2(pptx,dest/'figure.pptx')
        assert len(page['elements'])==len({e['elementId'] for e in page['elements']})
        for e in page['elements']:
            if e['elementType']=='image':assert (dest/e['src']).is_file()
        print(f"Fig {f['number']}: {len(page['elements'])} editable elements; PPTD/PPTX/assets packaged")
    (out/'README.md').write_text('''# 前三张论文图 · 2026-10-09

每个子目录含 `figure.pptd`、`pages/figure.page`、`media/` 和 `figure.pptx`，可独立复制。
PPTX 由本项目 PowerPoint COM 工作流生成，含原生文本框、形状、连线和独立照片；已嵌入字体并设置淡入切换。
PPTD 与对应 scene.json 对象逐一映射，供跨工具编辑；主交付以在 PowerPoint 中检查过的 PPTX 为准。

- [图一项目](fig01_study_pipeline/figure.pptd)
- [图二项目](fig02_image_edit_workflow/figure.pptd)
- [图三项目](fig03_lora_t2i_workflow/figure.pptd)

绘图源：上级目录 `revise_first_three.py`、`scene.json`、`build_figures.ps1`。
重新运行 COM 绘图后，运行上级目录 `package_first_three.py` 更新此项目。
''',encoding='utf-8')

if __name__=='__main__':main()
