#!/usr/bin/python

import unittest
import sys
from lib.layout import *

class LayoutTest(unittest.TestCase):

    def testTableLayout(self):
        res = table_layout( [ '1', '2', '3', '4' ] )
        self.assertEqual('1\n2\n3\n4\n', res)

    def testCounterLength(self):
        res = counter_length( 123 )
        self.assertEqual(3, res)
        res = counter_length( 1 )
        self.assertEqual(1, res)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(LayoutTest)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() and 1 or 0)

