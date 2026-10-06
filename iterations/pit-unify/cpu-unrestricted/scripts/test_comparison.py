import unittest
from compare_abc import compare_groups
class CorrespondenceTests(unittest.TestCase):
    def test_different_operators_do_not_pair(self):
        r={'status':'KILLED','normalizedKillingTests':['t']}
        d=compare_groups({('C','m','Negate'):[r]},{('C','m','Remove'):[r]})
        self.assertEqual(d['counts'],{'MISSING_FROM_RIGHT':1,'FRESH_ONLY':1})
    def test_multiplicity_is_not_collapsed(self):
        r={'status':'KILLED','normalizedKillingTests':['t']}
        d=compare_groups({('C','m'):[r,r]},{('C','m'):[r]})
        self.assertEqual(d['leftRecords'],2)
        self.assertEqual(d['counts'],{'AMBIGUOUS_MULTIPLICITY':1})
    def test_normalized_killing_sets_checked(self):
        d=compare_groups({('C','m'):[{'status':'KILLED','normalizedKillingTests':['a']}]},{('C','m'):[{'status':'KILLED','normalizedKillingTests':['b']}]})
        self.assertTrue(d['records'][0]['normalizedKillingSetChanged'])
        self.assertFalse(d['records'][0]['statusChanged'])
if __name__=='__main__':unittest.main()
