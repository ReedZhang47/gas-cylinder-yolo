import copy
import itertools
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import eval_lora_compare as ev


class TestEvaluation(unittest.TestCase):
    def test_matrix_missing_and_duplicate(self):
        rows=[dict(config=c,prompt_id=p,seed=s) for c,p,s in itertools.product(ev.CONFIGS,ev.PROMPTS,ev.SEEDS)]
        ev.check_matrix(rows)
        with self.assertRaises(ValueError):ev.check_matrix(rows[:-1])
        with self.assertRaises(ValueError):ev.check_matrix(rows+[rows[0]])

    def test_baseline_effective_graph(self):
        # Disconnected LoRA is ignored; a connected one makes the baseline invalid.
        graph={
            '1':dict(class_type='UNETLoader',inputs=dict(unet_name='base')),
            '2':dict(class_type='LoraLoaderModelOnly',inputs=dict(model=['1',0],lora_name='step-1860.safetensors',strength_model=.8)),
            '3':dict(class_type='CLIPLoader',inputs=dict(clip_name='encoder')),
            '4':dict(class_type='VAELoader',inputs=dict(vae_name='vae')),
            '5':dict(class_type='ResolutionSelector',inputs=dict(aspect_ratio='4:3',megapixels=1)),
            '6':dict(class_type='TextEncodeQwenImage21',inputs=dict(prompt='test',negative_prompt='',resolution=1024,clip=['3',0])),
            '7':dict(class_type='KSampler',inputs=dict(model=['1',0],positive=['6',0],negative=['6',1],latent_image=['10',0],seed=99999,steps=25,cfg=1.,sampler_name='euler',scheduler='simple',denoise=1.)),
            '8':dict(class_type='VAEDecode',inputs=dict(samples=['7',0],vae=['4',0])),
            '9':dict(class_type='SaveImage',inputs=dict(images=['8',0])),
            '10':dict(class_type='EmptyLatentImage',inputs=dict(width=['5',0],height=['5',1],batch_size=1)),
        }
        self.assertFalse(ev.trace_graph(graph,'no-lora',99999,(1184,896))['active_loras'])
        graph['7']['inputs']['model']=['2',0]
        with self.assertRaises(ValueError):ev.trace_graph(graph,'no-lora',99999,(1184,896))
        self.assertEqual(len(ev.trace_graph(graph,'1860-0.8',99999,(1184,896))['active_loras']),1)
        graph['7']['inputs']['positive']=['6',1]
        with self.assertRaises(ValueError):ev.trace_graph(graph,'1860-0.8',99999,(1184,896))

    def test_tokenizer_never_silently_truncates(self):
        class FakeClip:
            def tokenize(self,texts,context_length,truncate):
                self.context,self.truncate=context_length,truncate
                if any(len(t)>77 for t in texts):raise RuntimeError('too long')
        clip=FakeClip()
        with self.assertRaises(RuntimeError):ev.token_counts(clip,{'p':'x'*78})
        self.assertEqual(clip.context,77)
        self.assertFalse(clip.truncate)

    def test_rank_ties_unrounded(self):
        self.assertEqual(ev.rank_range({'a':30.,'b':30.+5e-7,'c':30.1},'a'),(2,3))
        self.assertEqual(ev.rank_range({'a':30.,'b':30.004},'a'),(2,2))

    def test_missing_and_uncertain_are_distinct(self):
        self.assertIsNone(ev.all_pass(['pass','','pass']))
        self.assertIsNone(ev.all_pass([]))
        self.assertEqual(ev.all_pass(['pass','uncertain']),0)
        self.assertEqual(ev.all_pass(['pass','pass']),1)

    def test_review_unknown_duplicate_rejected(self):
        mapping={'LC001':dict(prompt_id='new150_010')}
        row=dict(blind_id='LC001',usability=['pass']*2,realism='somewhat_realistic',requirements=['pass']*4,usability_reasons=[[],[]],usability_other=['',''],revealed_at='2026-10-10T00:00:00Z')
        payload=dict(rule=ev.REVIEW_RULE,protocol='digest',rater='R1',records=[row])
        self.assertEqual(ev.validate_review(payload,mapping,'digest'),{'LC001'})
        payload['records']=[row,row]
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')
        payload['records']=[dict(row,blind_id='LC999')]
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')
        payload['records']=[dict(row,requirements=['uncertain']*4)]
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')

    def test_v2_failure_needs_only_selected_reason(self):
        row=dict(blind_id='LC001',usability=['fail','pass'],realism='not_realistic',requirements=['fail']*4,
                 usability_reasons=[['no_target'],[]],usability_other=['',''],revealed_at='2026-10-10T00:00:00Z')
        payload=dict(rule=ev.REVIEW_RULE,protocol='digest',rater='R1',records=[row])
        mapping={'LC001':dict(prompt_id='new150_010')}
        ev.validate_review(payload,mapping,'digest')
        self.assertTrue(ev.review_complete(row))
        self.assertEqual(ev.all_pass(row['requirements']),0)
        row['usability_reasons'][0]=['other']
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')
        row['usability_other'][0]='Synthetic test reason'
        ev.validate_review(payload,mapping,'digest')
        row['usability_reasons'][0]=['poor_quality']
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')

    def test_v2_missing_binary_answer_and_legacy_export(self):
        row=dict(blind_id='LC001',usability=['pass']*2,realism='somewhat_realistic',requirements=['pass']*3+[''],
                 usability_reasons=[[],[]],usability_other=['',''],revealed_at='2026-10-10T00:00:00Z')
        mapping={'LC001':dict(prompt_id='new24_001')}
        payload=dict(rule=ev.REVIEW_RULE,protocol='digest',rater='R1',records=[row])
        ev.validate_review(payload,mapping,'digest')
        self.assertFalse(ev.review_complete(row))
        self.assertIsNone(ev.all_pass(row['requirements']))
        with self.assertRaises(ValueError):ev.validate_review(dict(payload,rule='LC-review-v1'),mapping,'digest')
        row['visible_count']=12
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')

    def test_realism_required_and_independent_from_usability(self):
        row=dict(blind_id='LC001',usability=['pass']*2,realism='',requirements=['pass']*4,
                 usability_reasons=[[],[]],usability_other=['',''],revealed_at=None)
        payload=dict(rule=ev.REVIEW_RULE,protocol='digest',rater='R1',records=[row])
        mapping={'LC001':dict(prompt_id='new24_001')}
        self.assertFalse(ev.review_complete(row))
        row['revealed_at']='2026-10-11T00:00:00Z'
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')
        for option in ev.REALISM_OPTIONS:
            row['realism']=option['code']
            ev.validate_review(payload,mapping,'digest')
            self.assertTrue(ev.review_complete(row))
            self.assertEqual(ev.all_pass(row['usability']),1)
        row['realism']='pass'
        with self.assertRaises(ValueError):ev.validate_review(payload,mapping,'digest')
        row['realism']='very_realistic'
        with self.assertRaises(ValueError):ev.validate_review(dict(payload,rule='LC-review-v2'),mapping,'digest')

    def test_v2_exactly_four_non_count_questions(self):
        for items in ev.PROMPT_CHECKS.values():
            self.assertEqual(len(items),4)
            self.assertTrue(all('是否' in question for question in items))
            self.assertFalse(any(word in question for question in items for word in ['恰好','十二','八个','数量','几个']))

    def test_review_revision_does_not_mutate_clip_provenance(self):
        with tempfile.TemporaryDirectory(dir=ev.ROOT/'.tmp') as temp,patch.object(ev,'OUT',Path(temp)):
            out=Path(temp)
            source=out/'versions/v1';source.mkdir(parents=True)
            (source/'original.py').write_text('original scoring code',encoding='utf-8')
            base=dict(code_hashes={'original.py':ev.sha(source/'original.py')})
            ev.write(out/'protocol.json',base)
            ev.write(out/'clip_scores.csv',{'unchanged':True})
            ev.write(out/'clip_cache.json',{'unchanged':True})
            revision=dict(rule=ev.REVIEW_RULE,automatic_protocol_sha256=ev.sha(out/'protocol.json'),clip_scores_sha256=ev.sha(out/'clip_scores.csv'),clip_cache_sha256=ev.sha(out/'clip_cache.json'),code_hashes=ev.code_hashes())
            ev.write(out/'review_protocol.json',revision)
            (out/'review_protocol.sha256').write_text(ev.sha(out/'review_protocol.json'))
            self.assertEqual(ev.review_protocol(),revision)
            (source/'original.py').write_text('changed',encoding='utf-8')
            with self.assertRaises(ValueError):ev.review_protocol()

    def test_filename_seed_is_not_counter(self):
        self.assertEqual(ev.parse_name('1860-0.8_new150_010_seed99999_00002_.png'),('1860-0.8','new150_010',99999))

    def test_matched_difference_direction(self):
        with tempfile.TemporaryDirectory(dir=ev.ROOT/'.tmp') as temp:
            out=Path(temp)
            with patch.object(ev,'OUT',out),patch.object(ev,'frozen',return_value=({},[])):
                ev.write(out/'protocol.json',{'code_hashes':ev.code_hashes()})
                ev.csvwrite(out/'manifest.csv',[dict(image_id='placeholder')])
                data=[dict(image_id=f'{c}_{p}_{s}',config=c,prompt_id=p,seed=s,clip_t=29. if c==ev.REFERENCE else 30.)
                      for c,p,s in itertools.product(ev.CONFIGS,ev.PROMPTS,ev.SEEDS)]
                ev.csvwrite(out/'clip_scores.csv',data)
                ev.write(out/'clip_cache.json',dict(scores_sha256=ev.sha(out/'clip_scores.csv'),
                    provenance=dict(protocol_sha256=ev.sha(out/'protocol.json'),manifest_sha256=ev.sha(out/'manifest.csv'),code_hashes=ev.code_hashes())))
                ev.aggregate()
                comparisons=ev.csvread(out/'reference_comparison.csv')
                self.assertEqual(float(next(r for r in comparisons if r['candidate']=='no-lora')['clip_mean_difference']),-1.)
                self.assertEqual(float(next(r for r in comparisons if r['candidate']==ev.REFERENCE)['clip_mean_difference']),0.)
                self.assertTrue(all(r['prompt_pass_n']=='pending' and r['usable_n']=='pending' for r in ev.csvread(out/'summary.csv')))

    def test_review_source_privacy(self):
        template=ev.TEMPLATE.read_text(encoding='utf-8').lower()
        for forbidden in ['step-','safetensors','clip_t','strength','no-lora','blind_mapping','config']:
            self.assertNotIn(forbidden,template)


if __name__=='__main__':unittest.main()
