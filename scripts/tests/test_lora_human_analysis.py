import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import analyze_lora_reviews as a


class TestHumanAnalysis(unittest.TestCase):
    def test_binary_confusion_and_kappa(self):
        metric=a.agreement([0,0,1,1],[0,1,0,1],[0,1])
        self.assertEqual(metric['exact_agreement'],.5)
        self.assertEqual(metric['kappa'],0)
        self.assertEqual(metric['confusion'],{'0':{'0':1,'1':1},'1':{'0':1,'1':1}})

    def test_constant_kappa_is_unavailable(self):
        self.assertIsNone(a.agreement([1,1],[1,1],[0,1])['kappa'])

    def test_ordinal_weighting_treats_adjacent_difference_as_smaller(self):
        categories=['low','middle','high']
        near=a.agreement(['low','high'],['middle','high'],categories,True)
        far=a.agreement(['low','high'],['high','low'],categories,True)
        self.assertGreater(near['kappa'],far['kappa'])

    def test_realism_not_used_as_usability_gate(self):
        r={'i':dict(usability=['pass','pass'],requirements=['pass','fail','pass','pass'],realism='not_realistic',usability_reasons=[[],[]])}
        result=a.describe(r,['i'])
        self.assertEqual(result['usable'],1)
        self.assertEqual(result['prompt_pass'],0)
        self.assertEqual(sum(result['realism'].values()),1)
        r['i']['usability'][0]='uncertain'
        self.assertEqual(a.describe(r,['i'])['usable'],0)


if __name__=='__main__':unittest.main()
