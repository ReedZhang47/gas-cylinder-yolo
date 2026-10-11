"""Reproducible 153-image LoRA evaluation; human labels are never inferred.

Use the project Python. Official CLIP and its small isolated dependencies live
under .tmp/lora-eval. The source images are read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/lora_compare'
INPUT = Path('D:/gas_cylinders/lora-compare')
RUNTIME = ROOT / '.tmp/lora-eval'
FIGURES = ROOT / 'paper/figures/lora_compare'
PROMPTS = ['new150_010', 'new24_001', 'new24_010']
SEEDS = [99999, 88888, 77777]
STEPS = [500, 1000, 1500, 1860]
STRENGTHS = [0.2, 0.5, 0.8, 1.0]
CONFIGS = ['no-lora'] + [f'{s}-{v:.1f}' for s in STEPS for v in STRENGTHS]
REFERENCE = '1860-0.8'
SHORT_TEXT = {
    'new150_010': 'A realistic construction-site photograph of exactly one complete blue industrial gas cylinder lying horizontally on a roof deck beside insulated ductwork, with a clear gap, an unobstructed body, and no other cylinders.',
    'new24_001': 'A realistic construction-site photograph of twelve tall blue industrial gas cylinders standing upright in two rows inside an open-top rectangular blue steel storage cage, on wet concrete in rainy weather.',
    'new24_010': 'A realistic construction-site photograph of eight tall silver-gray industrial gas cylinders standing in a compact irregular cluster beside a concrete column in a partially covered storage area, with no enclosing cage or shared securing frame.',
}
PROMPT_CHECKS = {
    'new150_010': ['恰好一个气瓶且无其它气瓶', '蓝色、横卧', '瓶身完整在画内、轮廓可辨、无物体横穿遮挡', '屋面施工场景，邻近保温风管，气瓶与其它材料有可见间隙'],
    'new24_001': ['可确认恰好十二个气瓶', '蓝色且竖直', '呈两排排列', '整组位于蓝色矩形钢制储存笼架内，开放顶、立柱与横杆可辨', '湿混凝土地面及阴雨环境外观'],
    'new24_010': ['可确认恰好八个气瓶', '银灰色且竖直', '紧凑不规则聚集', '整组无围合储瓶笼架、无共同固定框架', '混凝土柱附近、部分遮盖的施工储存场景'],
}
USABLE_CHECKS = [
    '至少一个可识别工业气瓶；可见瓶体、瓶肩或阀门无破坏身份的明显畸形或不可能融合。',
    '达到标注可见性要求的气瓶，实例与边界足够清楚，可一致标注。合理透视、遮挡、边缘截断不单独否决。',
    '可作为真实施工场景照片；无妨碍标注的严重拼贴、浮空、重复结构、伪文字覆盖或画质缺陷。',
]
REASONS = ['no_target', 'malformed_target', 'fused_instances', 'ambiguous_annotation', 'severe_scene_artifact', 'other']
NAME_RE = re.compile(r'^(no-lora|(?:500|1000|1500|1860)-(?:0\.2|0\.5|0\.8|1\.0))_(new150_010|new24_001|new24_010)_seed(99999|88888|77777)_\d+_\.png$')
TEMPLATE = Path(__file__).with_name('lora_review.html')


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def objsha(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def csvwrite(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def csvread(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def code_hashes():
    return {p.name: sha(p) for p in [Path(__file__), TEMPLATE]}


def official_clip():
    sys.path.insert(0, str(RUNTIME / 'python'))
    sys.path.insert(0, str(RUNTIME / 'CLIP'))
    import clip
    require(Path(clip.__file__).resolve().is_relative_to(RUNTIME / 'CLIP'), 'Not the isolated official CLIP checkout')
    return clip


def clip_source():
    return subprocess.check_output(['git', '-C', str(RUNTIME / 'CLIP'), 'rev-parse', 'HEAD'], text=True).strip()


def token_counts(clip, texts):
    # Official tokenize defaults to truncate=False. Count includes SOT/EOT.
    tokens = clip.tokenize(list(texts.values()), context_length=77, truncate=False)
    return {p: int((row != 0).sum()) for p, row in zip(texts, tokens)}


def parse_name(name):
    match = NAME_RE.fullmatch(name)
    require(match, f'Unexpected input filename: {name}')
    c, p, seed = match.groups()
    return c, p, int(seed)


def check_matrix(rows):
    found = Counter((r['config'], r['prompt_id'], int(r['seed'])) for r in rows)
    expected = set(itertools.product(CONFIGS, PROMPTS, SEEDS))
    require(set(found) == expected and all(v == 1 for v in found.values()),
            f'Matrix mismatch: missing={sorted(expected-set(found))}, duplicate={[k for k,v in found.items() if v>1]}, unexpected={sorted(set(found)-expected)}')


def connected(graph, node, slot, expected=None, output=None):
    link = graph[node]['inputs'][slot]
    require(isinstance(link, list) and len(link) == 2 and str(link[0]) in graph, f'Invalid {node}.{slot} connection')
    target = str(link[0])
    if expected:
        require(graph[target]['class_type'] == expected, f'Unexpected class at {node}.{slot}: {graph[target]["class_type"]}')
    if output is not None:
        require(link[1] == output, f'Unexpected output slot at {node}.{slot}')
    return target


def trace_graph(graph, config, seed, size):
    saves = [n for n, d in graph.items() if d['class_type'] == 'SaveImage']
    require(len(saves) == 1, 'Require exactly one active SaveImage')
    decode = connected(graph, saves[0], 'images', 'VAEDecode', 0)
    sampler = connected(graph, decode, 'samples', 'KSampler', 0)
    vae = connected(graph, decode, 'vae', 'VAELoader', 0)
    model = connected(graph, sampler, 'model', output=0)
    active_loras = []
    visited = set()
    while graph[model]['class_type'] == 'LoraLoaderModelOnly':
        require(model not in visited, 'Cyclic model chain')
        visited.add(model)
        active_loras.append(dict(graph[model]['inputs']))
        model = connected(graph, model, 'model', output=0)
    require(graph[model]['class_type'] == 'UNETLoader', 'Unknown effective base model chain')
    if config == 'no-lora':
        require(not active_loras, 'Baseline has an effective LoRA')
    else:
        step, strength = config.split('-')
        require(len(active_loras) == 1, 'Require exactly one effective LoRA')
        require(active_loras[0]['lora_name'] == f'step-{step}.safetensors' and active_loras[0]['strength_model'] == float(strength), 'Filename/active LoRA mismatch')
    pos = connected(graph, sampler, 'positive', 'TextEncodeQwenImage21', 0)
    neg = connected(graph, sampler, 'negative', 'TextEncodeQwenImage21', 1)
    require(pos == neg, 'Positive and negative must share the documented encoder')
    encoder = connected(graph, pos, 'clip', 'CLIPLoader', 0)
    latent = connected(graph, sampler, 'latent_image', 'EmptyLatentImage', 0)
    resolution = connected(graph, latent, 'width', 'ResolutionSelector', 0)
    require(connected(graph, latent, 'height', 'ResolutionSelector', 1) == resolution, 'Latent width/height mismatch')
    sampling = {k: graph[sampler]['inputs'][k] for k in ['seed', 'steps', 'cfg', 'sampler_name', 'scheduler', 'denoise']}
    require(sampling == dict(seed=seed, steps=25, cfg=1.0, sampler_name='euler', scheduler='simple', denoise=1.0), 'Unexplained sampling difference')
    text = graph[pos]['inputs']['prompt']
    require(graph[pos]['inputs']['negative_prompt'] == '' and graph[latent]['inputs']['batch_size'] == 1 and size == (1184, 896), 'Unexpected negative prompt, batch size, or dimensions')
    common = {'base_model': graph[model]['inputs'], 'text_encoder': graph[encoder]['inputs'],
              'vae': graph[vae]['inputs'], 'resolution': graph[resolution]['inputs'],
              'text_resolution': graph[pos]['inputs']['resolution'], 'sampling_without_seed': {k:v for k,v in sampling.items() if k != 'seed'},
              'negative_prompt': '', 'dimensions': list(size), 'batch_size': 1}
    return {'common': common, 'sampling': sampling, 'active_loras': active_loras,
            'active_nodes': {'save': saves[0], 'decode': decode, 'sampler': sampler, 'base': model, 'encoder': encoder, 'text': pos, 'latent': latent, 'resolution': resolution, 'vae': vae}, 'positive_prompt': text}


def prepare():
    from PIL import Image
    rows, metadata, prompts, errors = [], {}, {}, []
    for path in sorted(INPUT.glob('*.png')):
        try:
            config, pid, seed = parse_name(path.name)
            with Image.open(path) as im:
                im.load()
                graph = json.loads(im.info['prompt'])
                trace = trace_graph(graph, config, seed, im.size)
                pixel_sha = hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
                width, height = im.size
            require(pid not in prompts or prompts[pid] == trace['positive_prompt'], f'Inconsistent prompt {pid}')
            prompts[pid] = trace['positive_prompt']
            image_id = f'{config}_{pid}_{seed}'
            step, strength = ('', '') if config == 'no-lora' else config.split('-')
            rows.append(dict(image_id=image_id, filename=path.name, sha256=sha(path), prompt_id=pid, seed=seed,
                             step=step, strength=strength, is_baseline=int(config=='no-lora'), config=config,
                             width=width, height=height, prompt_sha256=objsha(trace['positive_prompt']), workflow_sha256=objsha(graph), pixel_sha256=pixel_sha))
            metadata[image_id] = dict(trace=trace, workflow=graph)
        except Exception as exc:
            errors.append(dict(filename=path.name, error=str(exc)))
    try:
        check_matrix(rows)
        require(len({canonical(v['trace']['common']) for v in metadata.values()}) == 1, 'Unexplained common generation parameter differences')
    except Exception as exc:
        errors.append(dict(error=str(exc)))
    hash_groups = defaultdict(list)
    pixel_groups = defaultdict(list)
    for row in rows:
        hash_groups[row['sha256']].append(row['image_id'])
        pixel_groups[row['pixel_sha256']].append(row['image_id'])
    audit = dict(checked_at=now(), input_count=len(rows), errors=errors,
                 duplicate_file_hashes=[v for v in hash_groups.values() if len(v)>1],
                 duplicate_pixel_hashes=[v for v in pixel_groups.values() if len(v)>1])
    write(OUT / 'input_audit.json', audit)
    require(not errors, 'Input anomalies; inspect input_audit.json before continuing')
    require(not audit['duplicate_file_hashes'] and not audit['duplicate_pixel_hashes'], 'Duplicate images flagged for inspection; no automatic removal')
    clip = official_clip()
    counts = token_counts(clip, SHORT_TEXT)
    candidate = dict(version='lora_compare_v1', prepared_at=now(), input_path=str(INPUT), n=153,
        configs=CONFIGS, prompts=PROMPTS, seeds=SEEDS, full_prompts=prompts, clip_texts=SHORT_TEXT, token_counts=counts,
        clip=dict(model='ViT-L/14', resolution=224, formula='100*cosine(L2(image),L2(text))', dtype='float32',
                  source_commit=clip_source(), preprocess='official resize shortest edge, center crop 224, RGB, normalize', truncate=False),
        prompt_checks=PROMPT_CHECKS, usable_checks=USABLE_CHECKS, reason_codes=REASONS,
        human=dict(anonymous_seed=20261010, order_seeds={'R1':20261011,'R2':20261012}, positive='all criteria pass', uncertain='0 with uncertain status retained', pending='NA, never zero', count='integer or uncertain'),
        ranking=dict(tolerance=1e-6, order='descending unrounded mean', ties='rank interval; numerical tolerance is not equivalence'),
        figure=dict(name='lora_parameter_sensitivity', seed=99999, prompts=PROMPTS[:2], panel_a=dict(strength=0.8,steps=STEPS), panel_b=dict(step=1860,strengths=['no-lora']+STRENGTHS), heatmap='all 9 matched images/config; baseline outside grid', supplementary='3 prompts x 3 seeds; all 153 images'),
        input_digest=objsha(rows), code_hashes=code_hashes(), plan_sha256=sha(ROOT/'docs/LORA_COMPARE_EVALUATION_PLAN.md'),
        base_alias='Author confirmed qwen_image_2.1.safetensors is renamed qwen_image_2.1_int8_convrot.safetensors; not independently dual-file hash verified',
        role='supplementary analysis specified before scores; some images previously seen; not generation preregistration')
    if (OUT/'protocol.json').exists():
        previous = read(OUT/'protocol.json')
        require({k:v for k,v in candidate.items() if k!='prepared_at'} == {k:v for k,v in previous.items() if k!='prepared_at'}, 'Frozen protocol differs; refusing overwrite')
        candidate = previous
    csvwrite(OUT/'manifest.csv', rows)
    write(OUT/'metadata.json', metadata)
    write(OUT/'prompts.json', {p:dict(full=prompts[p],evaluation=SHORT_TEXT[p],token_count=counts[p]) for p in PROMPTS})
    write(OUT/'protocol.json', candidate)
    (OUT/'protocol.sha256').write_text(sha(OUT/'protocol.json')+'\n', encoding='ascii')
    state('prepared', input_count=len(rows), token_counts=counts)
    print('Prepared: 153 images; effective graphs valid; tokens:', counts, flush=True)


def frozen():
    protocol = read(OUT/'protocol.json')
    require(sha(OUT/'protocol.json') == (OUT/'protocol.sha256').read_text().strip(), 'Protocol SHA256 mismatch')
    require(protocol['code_hashes'] == code_hashes(), 'Frozen source/template changed; refusing cache reuse')
    rows = csvread(OUT/'manifest.csv')
    typed_rows = [{k:(int(v) if k in ('seed','is_baseline','width','height') else v) for k,v in r.items()} for r in rows]
    require(objsha(typed_rows) == protocol['input_digest'], 'Frozen manifest contents changed')
    check_matrix(rows)
    require({p.name for p in INPUT.glob('*.png')} == {r['filename'] for r in rows}, 'Input filename set changed')
    for r in rows:
        require(sha(INPUT/r['filename']) == r['sha256'], f'Input changed: {r["filename"]}')
    return protocol, rows


def state(stage, **values):
    record = read(OUT/'execution.json') if (OUT/'execution.json').exists() else {'started_at': now()}
    record.update(status=stage, updated_at=now(), **values)
    write(OUT/'execution.json', record)


def download_model():
    official_clip()
    from clip.clip import _MODELS, _download
    path = _download(_MODELS['ViT-L/14'], str(RUNTIME/'models'))
    print('Official model downloaded and checksum verified:', path, flush=True)


def run_clip():
    protocol, rows = frozen()
    import torch
    import torchvision
    import PIL
    clip = official_clip()
    require(clip_source() == protocol['clip']['source_commit'], 'CLIP source changed')
    from clip.clip import _MODELS
    model_path = RUNTIME/'models'/Path(_MODELS['ViT-L/14']).name
    require(model_path.exists(), 'Missing model: run download-model first')
    weight_sha = sha(model_path)
    require(weight_sha == _MODELS['ViT-L/14'].split('/')[-2], 'Official model checksum mismatch')
    provenance = dict(protocol_sha256=sha(OUT/'protocol.json'), manifest_sha256=sha(OUT/'manifest.csv'),
                      model_sha256=weight_sha, source_commit=clip_source(), code_hashes=code_hashes())
    if (OUT/'clip_cache.json').exists():
        cached = read(OUT/'clip_cache.json')
        require(cached['provenance'] == provenance and cached['scores_sha256'] == sha(OUT/'clip_scores.csv'), 'CLIP cache provenance mismatch')
        require(len(csvread(OUT/'clip_scores.csv')) == 153, 'Incomplete CLIP cache')
        print('Reusing verified 153-image CLIP cache')
        return
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    model, preprocess = clip.load(str(model_path), device='cpu', jit=False)
    model = model.float().to(device).eval()
    texts = clip.tokenize([protocol['clip_texts'][p] for p in PROMPTS], truncate=False).to(device)
    scores = []
    with torch.inference_mode():
        text_features = model.encode_text(texts).float()
        text_features /= text_features.norm(dim=-1, keepdim=True)
        from PIL import Image
        # One finite smoke pass is reused as the first row of the full evaluation.
        for idx, row in enumerate(rows):
            with Image.open(INPUT/row['filename']) as im:
                tensor = preprocess(im).unsqueeze(0).to(device, dtype=torch.float32)
            feature = model.encode_image(tensor).float()
            feature /= feature.norm(dim=-1, keepdim=True)
            value = float(100 * (feature[0] @ text_features[PROMPTS.index(row['prompt_id'])]).item())
            require(math.isfinite(value) and -100.0001 <= value <= 100.0001, 'Non-finite/out-of-range CLIP score')
            scores.append(dict(image_id=row['image_id'], config=row['config'], prompt_id=row['prompt_id'], seed=int(row['seed']), clip_t=value,
                               text_sha256=objsha(protocol['clip_texts'][row['prompt_id']]), model_sha256=weight_sha,
                               protocol_sha256=provenance['protocol_sha256'], image_sha256=row['sha256']))
            if idx == 0 or (idx+1)%18 == 0 or idx == 152:
                print(f'CLIP {idx+1}/153 finite; device={device}', flush=True)
    csvwrite(OUT/'clip_scores.csv', scores)
    env = dict(recorded_at=now(), executable=sys.executable, python=sys.version, torch=torch.__version__, torchvision=torchvision.__version__, Pillow=PIL.__version__,
               clip_commit=clip_source(), clip_package_version='1.0 (official source checkout)', model_file=str(model_path), model_sha256=weight_sha,
               device=device, gpu=torch.cuda.get_device_name(0) if device=='cuda' else None, dtype='float32', tf32=False,
               preprocessing=repr(preprocess), isolated_dependencies={n:importlib.metadata.version(n) for n in ['ftfy','regex','tqdm','wcwidth']})
    write(OUT/'environment.json', env)
    write(OUT/'clip_cache.json', dict(provenance=provenance, scores_sha256=sha(OUT/'clip_scores.csv'), completed_at=now(), smoke='first full-data row finite and reused'))
    state('clip_completed', clip_count=153)


def review_pack():
    from PIL import Image
    protocol, rows = frozen()
    ordered = sorted(rows, key=lambda r:r['image_id'])
    random.Random(protocol['human']['anonymous_seed']).shuffle(ordered)
    mapping = [dict(blind_id=f'LC{i+1:03}', image_id=r['image_id'], filename=r['filename'], prompt_id=r['prompt_id'], config=r['config'], seed=r['seed']) for i,r in enumerate(ordered)]
    csvwrite(OUT/'restricted/blind_mapping.csv', mapping)
    sources = {r['image_id']:r for r in rows}
    order_record = {}
    for rater, seed in protocol['human']['order_seeds'].items():
        directory = OUT/'review'/rater
        (directory/'images').mkdir(parents=True, exist_ok=True)
        display = list(mapping)
        random.Random(seed).shuffle(display)
        order_record[rater] = [m['blind_id'] for m in display]
        items = []
        for m in display:
            target = directory/'images'/f'{m["blind_id"]}.png'
            with Image.open(INPUT/sources[m['image_id']]['filename']) as im:
                clean = Image.frombytes('RGB', im.size, im.convert('RGB').tobytes())
                clean.save(target, compress_level=6)
            items.append(dict(id=m['blind_id'], image=f'images/{m["blind_id"]}.png', prompt=protocol['full_prompts'][m['prompt_id']], checks=protocol['prompt_checks'][m['prompt_id']]))
        payload = dict(rater=rater, rule='LC-review-v1', protocol=sha(OUT/'protocol.json'), items=items,
                       usability=protocol['usable_checks'], reasons=REASONS)
        encoded = json.dumps(payload, ensure_ascii=False).replace('<','\\u003c')
        (directory/'index.html').write_text(TEMPLATE.read_text(encoding='utf-8').replace('__REVIEW_DATA__',encoded), encoding='utf-8')
        (directory/'README.txt').write_text('打开 index.html 开始评价（Chrome 或 Edge）。每人 153 张。先判断训练可用性，再显示提示词评价符合性。\n'
            '浏览器自动保存只用于方便恢复；每次结束请下载评分 JSON 备份。换浏览器/电脑时用“导入备份”恢复。\n'
            '不确定选 uncertain，不猜隐藏气瓶数。非通过项填写原因/备注。点击图片可放大，完整原图不裁剪。\n'
            '保存 JSON 显示已完成数与缺项；全部完成后将 JSON 交给作者。请各自独立评分。\n'
            '只能将当前整个文件夹交给评分者；不要提供上层目录、映射、自动分数或带配置的图表。\n', encoding='utf-8')
    write(OUT/'restricted/display_orders.json', order_record)
    state('review_ready', human_status='pending', raters=['R1','R2'], images_per_rater=153)
    print('Anonymous R1/R2 packages ready; no human labels generated', flush=True)


def rank_range(values, key, tol=1e-6):
    target = values[key]
    higher = sum(v > target+tol for v in values.values())
    tied = sum(abs(v-target) <= tol for v in values.values())
    return higher+1, higher+tied


def all_pass(values):
    if not values or any(v is None or v == '' for v in values):
        return None
    require(all(v in ('pass','fail','uncertain') for v in values), 'Invalid rating value')
    return int(all(v == 'pass' for v in values))


def validate_review(payload, mapping, protocol_sha):
    require(payload.get('rule') == 'LC-review-v1' and payload.get('protocol') == protocol_sha, 'Review rule/protocol mismatch')
    require(payload.get('rater') in ('R1','R2','ADJ'), 'Unknown rater ID')
    require(isinstance(payload.get('records'), list), 'Review records must be a list')
    seen = set()
    for item in payload['records']:
        bid = item.get('blind_id')
        require(bid in mapping and bid not in seen, f'Unknown or duplicate anonymous ID: {bid}')
        seen.add(bid)
        pid = mapping[bid]['prompt_id']
        for key, n in [('usability',3),('requirements',len(PROMPT_CHECKS[pid]))]:
            values = item.get(key, [])
            require(len(values)==n and all(v in ('pass','fail','uncertain',None,'') for v in values), f'Invalid {bid} {key}')
        count = item.get('visible_count','')
        require(count in ('','uncertain',None) or (isinstance(count,int) and not isinstance(count,bool) and count>=0), f'Invalid visible count {bid}')
        require(isinstance(item.get('note',''), str), f'Invalid note {bid}')
        require(all(r in REASONS for r in item.get('reasons',[])), f'Invalid reasons {bid}')
        complete = all_pass(item['usability']) is not None and all_pass(item['requirements']) is not None and count not in ('',None)
        if complete:
            require(item.get('revealed_at'), f'Missing phase record {bid}')
            if all_pass(item['usability']) == 0:
                require(item.get('reasons') and item.get('usability_note','').strip(), f'Missing usability reason {bid}')
            if all_pass(item['requirements']) == 0:
                require(item.get('note','').strip(), f'Missing requirement reason {bid}')
    return seen


def import_review(path):
    frozen()
    payload = read(path)
    mapping = {r['blind_id']:r for r in csvread(OUT/'restricted/blind_mapping.csv')}
    validate_review(payload, mapping, sha(OUT/'protocol.json'))
    target = OUT/'restricted/raw'/f'{payload["rater"]}_{sha(path)[:12]}.json'
    write(target, payload)
    # The current pointer is explicit; every original import remains retained.
    write(OUT/'restricted'/f'{payload["rater"]}_current.json', payload)
    print('Imported immutable human review:', target)


def human_results():
    mapping = {r['blind_id']:r for r in csvread(OUT/'restricted/blind_mapping.csv')} if (OUT/'restricted/blind_mapping.csv').exists() else {}
    raters = {}
    for rater in ['R1','R2']:
        path = OUT/'restricted'/f'{rater}_current.json'
        if path.exists():
            data = read(path)
            validate_review(data, mapping, sha(OUT/'protocol.json'))
            records = {r['blind_id']:r for r in data['records']}
            require(set(records)==set(mapping), f'{rater} must complete all 153 images')
            require(all(all_pass(r['usability']) is not None and all_pass(r['requirements']) is not None and r.get('visible_count') not in ('',None) for r in records.values()), f'{rater} has missing labels')
            raters[rater] = records
    if not raters:
        return {}, 'pending'
    agreement = {}
    disagreements = []
    if len(raters)==2:
        for field in ['usability','requirements']:
            a = [all_pass(raters['R1'][b][field]) for b in mapping]
            b = [all_pass(raters['R2'][b][field]) for b in mapping]
            observed = sum(x==y for x,y in zip(a,b))/153
            pa,pb = sum(a)/153,sum(b)/153
            expected=pa*pb+(1-pa)*(1-pb)
            kappa=None if len(set(a))==1 or len(set(b))==1 or expected==1 else (observed-expected)/(1-expected)
            agreement[field] = dict(n=153, raw_agreement=observed, cohens_kappa=kappa)
        for bid in mapping:
            a,b = raters['R1'][bid],raters['R2'][bid]
            if any(a.get(k)!=b.get(k) for k in ['usability','requirements','visible_count']):
                disagreements.append(dict(blind_id=bid, R1=a, R2=b))
    write(OUT/'restricted/agreement.json', agreement)
    write(OUT/'restricted/disagreements.json', disagreements)
    adjudication = {}
    adjpath = OUT/'restricted/ADJ_current.json'
    if adjpath.exists():
        data = read(adjpath)
        validate_review(data,mapping,sha(OUT/'protocol.json'))
        adjudication = {r['blind_id']:r for r in data['records']}
    needed = {r['blind_id'] for r in disagreements}
    if not needed.issubset(adjudication):
        return {}, 'adjudication_pending'
    result = {}
    for bid,m in mapping.items():
        item = adjudication[bid] if bid in needed else next(iter(raters.values()))[bid]
        require(all_pass(item['usability']) is not None and all_pass(item['requirements']) is not None, 'Incomplete adjudication')
        result[m['image_id']] = dict(usable=all_pass(item['usability']), prompt_pass=all_pass(item['requirements']),
                                    usability=item['usability'], requirements=item['requirements'], visible_count=item['visible_count'])
    write(OUT/'restricted/final_labels.json', result)
    return result, 'single_rater' if len(raters)==1 else 'two_raters_adjudicated'


def aggregate():
    frozen()
    data = csvread(OUT/'clip_scores.csv')
    require(len(data)==153, 'CLIP scores incomplete')
    check_matrix(data)
    cache = read(OUT/'clip_cache.json')
    require(cache['scores_sha256']==sha(OUT/'clip_scores.csv'), 'Scores changed after CLIP')
    require(cache['provenance']['protocol_sha256']==sha(OUT/'protocol.json') and cache['provenance']['manifest_sha256']==sha(OUT/'manifest.csv') and cache['provenance']['code_hashes']==code_hashes(), 'CLIP cache provenance mismatch')
    labels,human_status=human_results()
    summary,per_prompt,per_seed=[],[],[]
    for config in CONFIGS:
        selected=[r for r in data if r['config']==config]
        values=[float(r['clip_t']) for r in selected]
        step,strength=('', '') if config=='no-lora' else config.split('-')
        counts={k:sum(labels[r['image_id']][k] for r in selected) if labels else 'pending' for k in ['prompt_pass','usable']}
        summary.append(dict(config=config,step=step,strength=strength,n=9,clip_t_mean=statistics.mean(values),clip_t_sd=statistics.stdev(values),
                            prompt_pass_n=counts['prompt_pass'],usable_n=counts['usable'],human_status=human_status))
        for pid in PROMPTS:
            v=[float(r['clip_t']) for r in selected if r['prompt_id']==pid]
            per_prompt.append(dict(config=config,prompt_id=pid,n=3,clip_t_mean=statistics.mean(v),clip_t_sd=statistics.stdev(v)))
        for seed in SEEDS:
            v=[float(r['clip_t']) for r in selected if int(r['seed'])==seed]
            per_seed.append(dict(config=config,seed=seed,n=3,clip_t_mean=statistics.mean(v),clip_t_sd=statistics.stdev(v)))
    csvwrite(OUT/'summary.csv',summary)
    csvwrite(OUT/'per_prompt.csv',per_prompt)
    csvwrite(OUT/'per_seed.csv',per_seed)
    matched={(r['config'],r['prompt_id'],int(r['seed'])):r for r in data}
    overall={r['config']:r['clip_t_mean'] for r in summary if r['config']!='no-lora'}
    comparisons,pair_rows=[],[]
    for candidate in CONFIGS:
        diffs=[]
        table=Counter()
        for pid,seed in itertools.product(PROMPTS,SEEDS):
            a,b=matched[REFERENCE,pid,seed],matched[candidate,pid,seed]
            delta=float(a['clip_t'])-float(b['clip_t'])
            diffs.append(delta)
            pair_rows.append(dict(reference=REFERENCE,candidate=candidate,prompt_id=pid,seed=seed,clip_reference=float(a['clip_t']),clip_candidate=float(b['clip_t']),difference_reference_minus_candidate=delta))
            if labels:
                for field in ['prompt_pass','usable']:
                    table[field,labels[a['image_id']][field],labels[b['image_id']][field]]+=1
        low,high=rank_range(overall,REFERENCE)
        row=dict(reference=REFERENCE,candidate=candidate,n_pairs=9,clip_mean_difference=statistics.mean(diffs),reference_clip_rank_min=low,reference_clip_rank_max=high)
        for pid in PROMPTS:
            row[f'difference_{pid}']=statistics.mean(float(matched[REFERENCE,pid,s]['clip_t'])-float(matched[candidate,pid,s]['clip_t']) for s in SEEDS)
        for field in ['prompt_pass','usable']:
            for x,y in itertools.product([0,1],repeat=2):
                row[f'{field}_reference{x}_candidate{y}']=table[field,x,y] if labels else 'pending'
            if labels:
                v={r['config']:int(r[field+'_n']) for r in summary if r['config']!='no-lora'}
                row[field+'_rank_min'],row[field+'_rank_max']=rank_range(v,REFERENCE,tol=0)
            else:
                row[field+'_rank_min']=row[field+'_rank_max']='pending'
        comparisons.append(row)
    csvwrite(OUT/'reference_comparison.csv',comparisons)
    csvwrite(OUT/'matched_differences.csv',pair_rows)
    ranks=[]
    subsets=[('overall',lambda r:True)]+[(f'prompt:{p}',lambda r,p=p:r['prompt_id']==p) for p in PROMPTS]+[(f'seed:{s}',lambda r,s=s:int(r['seed'])==s) for s in SEEDS]+[(f'leave_out:{p}',lambda r,p=p:r['prompt_id']!=p) for p in PROMPTS]
    for name,condition in subsets:
        values={c:statistics.mean(float(r['clip_t']) for r in data if r['config']==c and condition(r)) for c in CONFIGS[1:]}
        low,high=rank_range(values,REFERENCE)
        ranks.append(dict(subset=name,reference=REFERENCE,clip_t_mean=values[REFERENCE],rank_min=low,rank_max=high,n=sum(r['config']==REFERENCE and condition(r) for r in data)))
    csvwrite(OUT/'reference_rank_sensitivity.csv',ranks)
    state('awaiting_human_scores' if not labels else human_status,human_status=human_status)
    print('Summary: 17 configurations; human status:',human_status,flush=True)


def manuscript_tables(summary):
    maximum=max(float(r['clip_t_mean']) for r in summary)
    md=['| Step | Strength | CLIP-T mean ± SD | All requirements met | Training usable |','|---|---|---|---|---|']
    tex=[r'\begin{tabular}{llccc}',r'\hline',r'Step & Strength & CLIP-T mean $\pm$ SD & Requirements & Usable \\',r'\hline']
    for r in summary:
        value=f'{float(r["clip_t_mean"]):.2f} ± {float(r["clip_t_sd"]):.2f}'
        tx=f'{float(r["clip_t_mean"]):.2f} $\\pm$ {float(r["clip_t_sd"]):.2f}'
        if abs(float(r['clip_t_mean'])-maximum)<=1e-6:
            value=f'**{value}**'
            tx=r'\textbf{'+tx+'}'
        def human_cell(field,latex=False):
            if r[field]=='pending':return 'pending'
            value=f'{r[field]}/9'
            best=max(int(q[field]) for q in summary)
            if int(r[field])==best:
                return (r'\textbf{'+value+'}') if latex else f'**{value}**'
            return value
        md.append(f'| {r["step"] or "No LoRA"} | {r["strength"] or "--"} | {value} | {human_cell("prompt_pass_n")} | {human_cell("usable_n")} |')
        tex.append(f'{r["step"] or "No LoRA"} & {r["strength"] or "--"} & {tx} & {human_cell("prompt_pass_n",True)} & {human_cell("usable_n",True)} '+r'\\')
    tex += [r'\hline',r'\end{tabular}', '% n=9 per configuration; sample SD (ddof=1); human fields pending until real reviews.']
    (OUT/'summary.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    table=ROOT/'paper/tables/lora_parameter_sensitivity.tex'
    table.parent.mkdir(parents=True,exist_ok=True)
    table.write_text('\n'.join(tex)+'\n',encoding='utf-8')
    return '\n'.join(md)


def make_figures(summary, rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Rectangle
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    FIGURES.mkdir(parents=True,exist_ok=True)
    by_config={r['config']:float(r['clip_t_mean']) for r in summary}
    index={(r['config'],r['prompt_id'],int(r['seed'])):r for r in rows}
    def show(ax,config,pid,seed):
        with Image.open(INPUT/index[config,pid,seed]['filename']) as im:
            ax.imshow(im.convert('RGB'))
        ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values():spine.set_visible(False)
        if config==REFERENCE:
            ax.add_patch(Rectangle((0,0),1,1,transform=ax.transAxes,fill=False,edgecolor='#888888',linewidth=0.9,clip_on=False))
    fig=plt.figure(figsize=(180/25.4,218/25.4),layout='constrained')
    outer=fig.add_gridspec(3,1,height_ratios=[2.7,2.5,2.9],hspace=.10)
    for section,configs,title in [(0,[f'{s}-0.8' for s in STEPS],'(a) Checkpoint sensitivity | strength 0.8 | seed 99999'),
                                  (1,['no-lora']+[f'1860-{s:.1f}' for s in STRENGTHS],'(b) Strength sensitivity | step 1860 | seed 99999')]:
        sub=outer[section].subgridspec(3,len(configs),height_ratios=[.22,1,1],hspace=.03,wspace=.03)
        heading=fig.add_subplot(sub[0,:]);heading.axis('off');heading.text(0,.65,title,fontsize=7.4,weight='bold')
        for i,pid in enumerate(PROMPTS[:2]):
            for j,c in enumerate(configs):
                ax=fig.add_subplot(sub[i+1,j]);show(ax,c,pid,99999)
                if i==0:ax.set_title(('step '+c.split('-')[0]) if section==0 else ('No LoRA' if c=='no-lora' else c.split('-')[1]),fontsize=7,pad=3)
                if j==0:ax.set_ylabel('Single cylinder' if i==0 else 'Storage cage',fontsize=7)
    bottom=outer[2].subgridspec(1,2,width_ratios=[1.5,1],wspace=.2)
    ax=fig.add_subplot(bottom[0,0])
    values=np.array([[by_config[f'{s}-{v:.1f}'] for v in STRENGTHS] for s in STEPS])
    norm=plt.Normalize(values.min(),values.max())
    cmap=plt.get_cmap('cividis')
    im=ax.imshow(values,cmap=cmap,norm=norm)
    ax.set_title('(c) Mean CLIP-T | all 9 images per cell',loc='left',fontsize=7.4,weight='bold',pad=8)
    ax.set_xticks(range(4),[str(s) for s in STRENGTHS]);ax.set_yticks(range(4),[str(s) for s in STEPS])
    ax.set_xlabel('LoRA strength');ax.set_ylabel('Training step')
    for i,j in itertools.product(range(4),repeat=2):
        r,g,b,_=cmap(norm(values[i,j])); luminance=.2126*r+.7152*g+.0722*b
        ax.text(j,i,f'{values[i,j]:.2f}',ha='center',va='center',color='black' if luminance>.5 else 'white',fontsize=7)
    ax.add_patch(Rectangle((1.5,2.5),1,1,fill=False,edgecolor='#888888',linewidth=1.2))
    fig.colorbar(im,ax=ax,fraction=.045,pad=.04).set_label('CLIP-T similarity')
    note=fig.add_subplot(bottom[0,1]);note.axis('off')
    note.text(0,.98,'Supplementary parameter analysis\n\nFull images; fixed display scenes.\nPanels (a, b): seed 99999.\nHeatmap: 3 prompts x 3 seeds.\nEach setting: n = 9.\n\nGray frame: current setting\n(step 1860, strength 0.8).\nFrame does not indicate a winner.\n\nNo-LoRA baseline mean:\n'+f'{by_config["no-lora"]:.2f}'+'\n\nHuman assessment pending:\nrequirements and training usability.',va='top',fontsize=7,linespacing=1.4)
    for ext in ['pdf','svg','png']:
        fig.savefig(FIGURES/f'lora_parameter_sensitivity.{ext}',dpi=300)
    plt.close(fig)
    with PdfPages(FIGURES/'lora_parameter_sensitivity_supplement.pdf') as pdf:
        for pid,seed in itertools.product(PROMPTS,SEEDS):
            fig,axes=plt.subplots(5,4,figsize=(10,10.7),layout='constrained')
            fig.suptitle(f'Complete parameter grid | {pid} | seed {seed}',fontsize=12)
            for ax in axes.flat:ax.axis('off')
            for j,c in enumerate(CONFIGS[1:]):
                show(axes.flat[j],c,pid,seed);axes.flat[j].set_title(f'step {c.split("-")[0]} | strength {c.split("-")[1]}',fontsize=8)
            show(axes.flat[16],'no-lora',pid,seed);axes.flat[16].set_title('No LoRA baseline',fontsize=8)
            axes.flat[17].text(0,.8,'All 17 settings shown.\nFull images; no selected seed.\nGray frame: current setting.\nHuman assessment pending.',fontsize=9,va='top')
            pdf.savefig(fig,dpi=180);plt.close(fig)


def report():
    protocol,rows=frozen()
    summary=csvread(OUT/'summary.csv')
    table=manuscript_tables(summary)
    make_figures(summary,rows)
    ranks=csvread(OUT/'reference_rank_sensitivity.csv')
    reference=next(r for r in summary if r['config']==REFERENCE)
    baseline=summary[0]
    env=read(OUT/'environment.json')
    rank_text=f'{ranks[0]["rank_min"]}-{ranks[0]["rank_max"]}'
    report_text=f'''# LoRA parameter evaluation: automatic stage complete

Prepared and evaluated {now()} (UTC+8). CLIP is complete for all 153 images. Human requirements and training-usability assessments are {reference['human_status']}. No human score was inferred.

17 configurations, each n=9 (three prompts x three matched seeds). Current setting step 1860 / strength 0.8: CLIP-T {float(reference['clip_t_mean']):.4f} +/- {float(reference['clip_t_sd']):.4f} (sample SD), descriptive rank {rank_text} among 16 LoRA settings. No-LoRA baseline {float(baseline['clip_t_mean']):.4f} +/- {float(baseline['clip_t_sd']):.4f}, reported separately.

This report and configured figures must not be distributed to human raters before scoring. Give each rater only review/R1 or review/R2, respectively.

## Human handoff

Open review/R1/index.html and review/R2/index.html in Chrome or Edge. Each rater independently reviews 153 images. Complete training-usability judgments before revealing the prompt, then requirements and visible-cylinder count. Non-pass/uncertain judgments require reasons. Click the image to enlarge. Download JSON at the end of each session; local browser saving is only a convenience. Import the JSON to resume elsewhere. The export reports completed images and missing fields. Submit the completed JSON files to the author. One actual rater is allowed with explicit single-rater reporting; never manufacture a second rater.

Continue with: `.venv/Scripts/python.exe scripts/eval_lora_compare.py import-review PATH_TO_JSON`, then `aggregate`. Original imports are retained. If disagreements exist, only the disputed IDs wait for human adjudication. `report` can then rebuild the final table and figures.

## Automatic table (human cells pending)

{table}

## Rank sensitivity

'''
    report_text += '\n'.join(f'- {r["subset"]}: rank {r["rank_min"]}-{r["rank_max"]}, mean {float(r["clip_t_mean"]):.4f}, n={r["n"]}.' for r in ranks)
    report_text+='''

## Interpretation limits

Only these three prompts and nine images/configuration support this descriptive comparison. CLIP uses a center crop while raters see full images. The SD is not an SE or confidence interval. Ranking ties within 1e-6 are numerical ties, not evidence of equivalence. The prompts are shared across configurations. Seed and leave-one-prompt-out summaries reuse the same observations. These data do not support a strong noninferiority claim or independently select the best setting for detector training. This is a supplementary sensitivity analysis planned before computing scores, with some images already seen; it is not a generation preregistration. The base-model alias is author-confirmed, not dual-file hash verification. Detector results remain those for the existing D configuration.

For independent confirmation, choose a candidate after reporting all three dimensions, collect new prompts and matched seeds, and specify a task-grounded margin, primary endpoint and sample-size calculation before scoring. No generation or detector retraining was started here.

## Reproduction and sources

'''
    report_text+=f'Official OpenAI CLIP ViT-L/14 (224), commit `{env["clip_commit"]}`, model SHA256 `{env["model_sha256"]}`. Float32 on {env["device"]}; formula 100 times cosine of L2-normalized features; no softmax or logit scale.\n\n'
    report_text+='[OpenAI CLIP implementation](https://github.com/openai/CLIP/blob/'+env['clip_commit']+'/clip/clip.py). Input, protocol, source, model and result hashes are recorded. All input file hashes are rechecked after evaluation.\n'
    (OUT/'report.md').write_text(report_text,encoding='utf-8')
    caption='Supplementary sensitivity analysis of LoRA checkpoint and strength. (a) Strength 0.8 at four training steps. (b) Step 1860 at four strengths, with the no-LoRA baseline. Both display panels use two fixed prompts and seed 99999, selected in the analysis plan after some images had been seen; full uncropped images are shown. (c) Mean CLIP-T similarity across three prompts and three seeds (n=9 per configuration); the baseline is reported once outside the heatmap. Gray outlines identify the configuration used for the D detector experiment, not a winning setting. CLIP-T = 100 times cosine similarity; SD in the table is sample SD (ddof=1). Human requirements and training-usability evaluation remain pending.'
    methods=f'''# Methods and preliminary automatic results

We evaluated 153 existing images covering 16 LoRA settings (steps 500, 1000, 1500, 1860; strengths 0.2, 0.5, 0.8, 1.0) and one no-LoRA baseline. Every setting comprised three prompts and three matched seeds (n=9). PNG metadata were traced from the saved image to the active sampler, effective LoRA, text encoder, latent and VAE; sampling settings and prompt consistency were checked before scoring. The protocol and original images were hashed before evaluation. The alias of the base-model filename was confirmed by the author.

OpenAI CLIP ViT-L/14 (224) was evaluated in float32 with official image preprocessing. Evaluation texts were fixed short descriptions common to every setting; tokenizer lengths (including special tokens) were {protocol['token_counts']}, with no truncation. Image and text embeddings were L2 normalized, and CLIP-T was computed as 100 times their cosine similarity. Means and sample SDs were computed over nine images per setting. Two independently ordered packages conceal configuration labels; actual human ratings and adjudication have not yet been collected. These two dimensions are pending, not zero.

The current step-1860/strength-0.8 setting had mean CLIP-T {float(reference['clip_t_mean']):.4f} (SD {float(reference['clip_t_sd']):.4f}), rank {rank_text} among the 16 LoRA settings. The baseline mean was {float(baseline['clip_t_mean']):.4f}. Rank sensitivity by prompt, seed and prompt omission is reported separately. This result is limited to the three prompts, is descriptive, and neither establishes equivalence nor invalidates the existing D detector experiment. Human assessment is required before any combined interpretation of parameter suitability.

## Figure caption

{caption}

## Table caption

CLIP-T mean and sample SD over n=9 images per configuration. Human columns await actual reviewers. Bold identifies the best observed value within each completed dimension, including ties; it does not establish superiority. No-LoRA baseline is represented once.
'''
    (OUT/'methods_results.md').write_text(methods,encoding='utf-8')
    state('awaiting_human_scores' if reference['human_status'] in ('pending','adjudication_pending') else reference['human_status'],human_status=reference['human_status'],automatic_report_completed_at=now())
    print('Automatic tables, main PDF/SVG/PNG and nine-page supplement written',flush=True)


def accept():
    from PIL import Image
    _,rows=frozen()
    scores=csvread(OUT/'clip_scores.csv'); summary=csvread(OUT/'summary.csv')
    require(len(scores)==153 and len(summary)==17,'Result counts mismatch')
    independently_recomputed={}
    for r in summary:
        values=[float(s['clip_t']) for s in scores if s['config']==r['config']]
        mean=sum(values)/len(values)
        sd=math.sqrt(sum((v-mean)**2 for v in values)/(len(values)-1))
        require(abs(mean-float(r['clip_t_mean']))<1e-10 and abs(sd-float(r['clip_t_sd']))<1e-10,'Summary numerical mismatch')
        independently_recomputed[r['config']]=dict(mean=mean,sd=sd,n=len(values))
    mapping={r['blind_id']:r for r in csvread(OUT/'restricted/blind_mapping.csv')}
    require(len(mapping)==153,'Anonymous IDs incomplete')
    source_by_id={r['image_id']:r for r in rows}
    package_checks={}
    for rater in ['R1','R2']:
        directory=OUT/'review'/rater
        html=(directory/'index.html').read_text(encoding='utf-8')
        for row in rows:
            require(row['filename'] not in html and row['image_id'] not in html,'Source/configuration leak in review HTML')
        for forbidden in ['step-','safetensors','clip_t','strength','no-lora','blind_mapping','config']:
            require(forbidden not in html.lower(),f'Review HTML information leak: {forbidden}')
        images=list((directory/'images').glob('*.png'))
        require(len(images)==153,'Anonymous image count mismatch')
        for path in images:
            require(re.fullmatch(r'LC\d{3}\.png',path.name),'Anonymous filename mismatch')
            with Image.open(path) as im:
                require(not im.info,'PNG metadata leaked')
                pixel=hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
            require(pixel==source_by_id[mapping[path.stem]['image_id']]['pixel_sha256'],'Anonymous pixels differ from original')
        package_checks[rater]=dict(images=153,html_config_leaks=0,png_metadata_leaks=0,source_pixel_matches=153)
    acceptance=dict(checked_at=now(),status='automatic_complete_human_pending',inputs_unchanged=153,
        clip_rows=153,summary_rows=17,independent_summary=independently_recomputed,packages=package_checks,
        protocol_sha256=sha(OUT/'protocol.json'),source_hashes=code_hashes(),environment_sha256=sha(OUT/'environment.json'),
        outputs={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'clip_scores.csv',OUT/'summary.csv',FIGURES/'lora_parameter_sensitivity.pdf',FIGURES/'lora_parameter_sensitivity.svg',FIGURES/'lora_parameter_sensitivity.png',FIGURES/'lora_parameter_sensitivity_supplement.pdf']},
        human_labels='not generated; pending',visual_qa='must record after rendering',browser_qa='must record after actual browser checks')
    write(OUT/'acceptance.json',acceptance)
    print('Automatic completeness, independent summary, input hashes and package privacy passed',flush=True)


def serve_review(rater,port):
    from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
    from functools import partial
    directory=OUT/'review'/rater
    require((directory/'index.html').exists(),'Missing review package')
    print(f'Review {rater}: http://127.0.0.1:{port}/index.html (only this anonymous package is served)',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),partial(SimpleHTTPRequestHandler,directory=str(directory))).serve_forever()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for command in ['prepare','download-model','clip','review-pack','aggregate','report','accept']:
        sub.add_parser(command)
    imp=sub.add_parser('import-review',help='Validate and retain a real human JSON export')
    imp.add_argument('path',type=Path)
    serve=sub.add_parser('serve-review',help='Optional localhost view serving only one anonymous package')
    serve.add_argument('--rater',choices=['R1','R2'],required=True)
    serve.add_argument('--port',type=int,default=8087)
    args=parser.parse_args()
    if args.command=='import-review':import_review(args.path)
    elif args.command=='serve-review':serve_review(args.rater,args.port)
    else:{'prepare':prepare,'download-model':download_model,'clip':run_clip,'review-pack':review_pack,'aggregate':aggregate,'report':report,'accept':accept}[args.command]()


if __name__=='__main__':
    main()
