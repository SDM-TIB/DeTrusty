from DeTrusty.Operators.AnapsidOperators.Xvalues import Xvalues
from DeTrusty.Sparql.Parser.services import Argument, Values
import time, unittest

class filterByValues(unittest.TestCase):

    def setUp(self):
        self.vars1 = Values([Argument('?disease_name')], [[Argument("\"Attention-deficit_hyperactivity_disorder\"", True)]])
        self.vars2 = Values([Argument('?disease_name')], [[None, True]])
        self.value1 = Xvalues(self.vars1)
        self.value2 = Xvalues(self.vars2)

    def test_isValid(self):
        tuple = {'disease_name': 'Attention-deficit_hyperactivity_disorder'}
        self.assertEqual(self.value1.filterByValues(tuple), True)

    def test_UNDEF(self):
        tuple = {'disease_name': 'Rheumatoid_arthritis'}
        self.assertEqual(self.value2.filterByValues(tuple), True)
    
    def test_NotValid(self):
        tuple = {'disease_name': 'Rheumatoid_arthritis'}
        self.assertEqual(self.value1.filterByValues(tuple), False)
    
    def tearDown(self):
        self.vars1 = None
        self.vars2 = None
        self.value1 = None
        self.value2 = None

class TestEfficiency(unittest.TestCase):

    def setUp(self):
        self.vars1 = Values([Argument("?disease_name")], [[Argument("\"Attention-deficit_hyperactivity_disorder\"", True)]])
        self._filterByValues = Xvalues(self.vars1)
        self._efficiency_data = dict()

    def test_filterByValues_single_var(self):
        starting_time = time.time()

        tuple = {'disease_name': 'Rheumatoid_arthritis'}
        self._filterByValues.filterByValues(tuple)

        ending_time = time.time()

        self._efficiency_data["filterByValues1"] = ending_time - starting_time

    def test_filterByValues_mult_var(self):
        starting_time = time.time()

        tuple = {'drug_gn': 'Heroin', 'drug': 'http://www4.wiwiss.fu-berlin.de/drugbank/resource/drugs/DB01452', 'disease_name': 'Response to morphine-6-glucuronide', 'disease': 'http://www4.wiwiss.fu-berlin.de/diseasome/resource/diseases/3733', 'disease_class': 'http://www4.wiwiss.fu-berlin.de/diseasome/resource/diseaseClass/Neurological'}
        self._filterByValues.filterByValues(tuple)

        ending_time = time.time()

        self._efficiency_data["filterByValues2"] = ending_time - starting_time
    
    def tearDown(self):
        print(self._efficiency_data)
        self.vars1 = None
        self._filterByValues = None

if __name__ == "__main__":
    unittest.main()
