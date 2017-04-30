from django.test import TestCase
import utils
from datetime import datetime
# Create your tests here.

class StartOfTest(TestCase):
    def test_trivial(self):
        expected = datetime(1989, 8, 6, 0, 0)
        case = datetime(1989, 8, 6, 0, 0)
        self.assertEqual(utils.start_of(case), expected)

    def test_simple(self):
        expected = datetime(1989, 8, 6, 0, 0)
        case = datetime(1989, 8, 6, 1)
        self.assertEqual(utils.start_of(case), expected)

    def test_wicked_hard(self):
        expected = datetime(1989, 8, 6, 0 ,0 )
        case = datetime(1989, 8, 6, 1, 2, 3)
        self.assertEqual(utils.start_of(case), expected)

    def test_not_yesterday(self):
        expected = datetime(1989, 8, 6, 0, 0)
        case = datetime(1989, 8, 5)
        self.assertNotEqual(utils.start_of(case), expected)


class EndOfTest(TestCase):
    def test_trivial(self):
        expected = datetime(1989, 8, 6, 23, 59)
        case = datetime(1989, 8, 6, 23, 59)
        self.assertEqual(utils.end_of(case), expected)

    def test_trivial(self):
        expected =  datetime(1989, 8, 6, 23, 59)
        case = datetime(1989, 8, 6)
        self.assertEqual(utils.end_of(case), expected)

    def test_simple(self):
        expected =  datetime(1989, 8, 6, 23, 59)
        case = datetime(1989, 8, 6, 1)
        self.assertEqual(utils.end_of(case), expected)

    def test_wicked_hard(self):
        expected = datetime(1989, 8, 6, 23, 59)
        case = datetime(1989, 8, 6, 1, 2, 3)
        self.assertEqual(utils.end_of(case), expected)

    def test_not_yesterday(self):
        expected = datetime(1989, 8, 6, 23, 59)
        case = datetime(1989, 8, 5)
        self.assertNotEqual(utils.end_of(case), expected)
