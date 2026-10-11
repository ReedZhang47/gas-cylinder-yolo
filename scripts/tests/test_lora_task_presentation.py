from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from present_lora_task_evaluation import pareto_front


class TestParetoPresentation(unittest.TestCase):
    def test_tradeoff_preserves_all_frontier_candidates(self):
        points={'current':(30.41,6,6),'clip_leader':(30.76,4,4),'usable_leader':(29.58,7,3),'baseline':(28.99,6,1)}
        self.assertEqual(set(pareto_front(points)),{'current','clip_leader','usable_leader'})

    def test_tied_points_are_not_dominated(self):
        self.assertEqual(set(pareto_front({'a':(2,2,2),'b':(2,2,2),'c':(2,1,2)})),{'a','b'})


if __name__=='__main__':unittest.main()
