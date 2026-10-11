"""Read-only audit of frozen inputs, real ratings and final LoRA deliverables."""
import itertools
import math
import statistics

import eval_lora_compare as e
import finalize_lora_evaluation as f
import present_lora_task_evaluation as p


def main():
    summary, final, mapping, _, raw = f.verify_final()
    scores = e.csvread(e.OUT / 'clip_scores.csv')
    source = {(r['config'], r['prompt_id'], int(r['seed'])): r for r in scores}
    for row in summary:
        values = [float(r['clip_t']) for r in scores if r['config'] == row['config']]
        assert math.isclose(float(row['clip_t_mean']), statistics.mean(values), abs_tol=1e-10)
        assert math.isclose(float(row['clip_t_sd']), statistics.stdev(values), abs_tol=1e-10)
    for row in e.csvread(e.OUT / 'reference_comparison.csv'):
        delta = []
        counts = {field: {(i, j): 0 for i, j in itertools.product([0, 1], repeat=2)}
                  for field in ['usable', 'prompt_pass']}
        for prompt, seed in itertools.product(e.PROMPTS, e.SEEDS):
            a, b = source[e.REFERENCE, prompt, seed], source[row['candidate'], prompt, seed]
            delta.append(float(a['clip_t']) - float(b['clip_t']))
            for field in counts:
                counts[field][final[a['image_id']][field], final[b['image_id']][field]] += 1
        assert math.isclose(statistics.mean(delta), float(row['clip_mean_difference']), abs_tol=1e-10)
        for field in counts:
            for (i, j), count in counts[field].items():
                assert count == int(row[f'{field}_reference{i}_candidate{j}'])
    data = e.read(e.OUT / 'human_analysis/final_results.json')
    assert data['totals'] == {'usable': 80, 'prompt_pass': 84}
    assert data['realism_totals'] == {'not_realistic': 30, 'somewhat_realistic': 70, 'very_realistic': 53}
    for rater, imported in raw.items():
        name = 'anonymous_adjudication_v3.json' if rater == 'ADJ' else f'anonymous_review_v3_{rater}.json'
        assert e.read(e.OUT / 'review' / name) == imported
    amendment = e.read(e.OUT / 'human_analysis/presentation_amendment.json')
    for name, digest in amendment['preserved_data_sha256'].items():
        assert e.sha(e.ROOT / name) == digest, f'Preserved data changed: {name}'
    values = p.vectors(summary, final, mapping)
    assert set(p.pareto_front(values)) == {'1500-0.8', '1860-0.2', '1860-0.8'}
    assert math.isclose(values[e.REFERENCE][0], 30.407935712072586, abs_tol=1e-10)
    assert values[e.REFERENCE][1:] == (6, 6)
    assert max(x[2] for x in values.values()) == 6
    assert sum(x[2] == 6 for x in values.values()) == 1
    cage = [final[m['image_id']] for m in mapping.values() if m['prompt_id'] == 'new24_001']
    assert len(cage) == 51 and sum(x['requirements'][1] == 'pass' for x in cage) == 0
    assert sum(x['usable'] for x in cage) == 30
    acceptance = e.read(e.OUT / 'acceptance.json')
    assert acceptance['status'] == 'complete' and acceptance['remaining_adjudication_count'] == 0
    for name, digest in acceptance['outputs'].items():
        assert e.sha(e.ROOT / name) == digest, f'Final output changed: {name}'
    for name, digest in acceptance['finalization_source_hashes'].items():
        assert e.sha(e.ROOT / 'scripts' / name) == digest, f'Finalization source changed: {name}'
    assert e.sha(e.ROOT / 'scripts/present_lora_task_evaluation.py') == acceptance['presentation_amendment']['source_sha256']
    print(f'PASS: 153 frozen images; 306 real ratings; 110 adjudications; '
          f'17 summaries; {len(acceptance["outputs"])} final output hashes; three-metric presentation.')


if __name__ == '__main__':
    main()
