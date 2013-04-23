#!/usr/bin/env python

"""
Matlab documentation parser using parsley.
"""

import sys
from parsley import makeGrammar, term, termMaker as t
import unittest
from pprint import pprint
import logging
logging.basicConfig()


class MatlabdocParser3Tests(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger(__name__ + '.ParserTests')
        self.logger.setLevel(logging.DEBUG)

    def setUp(self):
        grammar_str = open('matlabdoc_parser3.grammar').read()
        self.grammar = makeGrammar(grammar_str, {})

    def test_definition_line_class(self):
        actual = self.grammar('   classdef A  \n').definition_line()
        expected = dict(type='class', name='A', superclasses=())
        self.assertDictEqual(actual, expected)

    def test_definition_line_function(self):
        actual = self.grammar('   function a  \n').definition_line()
        expected = dict(type='function', name='a', outargs=(), inargs=())
        self.assertDictEqual(actual, expected)

    def test_functiondef(self):
        actual = self.grammar('function a()').functiondef()
        expected = dict(type='function', name='a', outargs=(), inargs=())
        self.assertDictEqual(actual, expected)

    def test_classdef(self):
        actual = self.grammar('classdef A').classdef()
        expected = dict(type='class', name='A', superclasses=())
        self.assertDictEqual(actual, expected)

    def test_inherit(self):
        actual = self.grammar('< S1 & ...\n  S2').inherit()
        expected = ('S1', 'S2')
        self.assertTupleEqual(actual, expected)

    def test_commentblock(self):
        actual = self.grammar(
            '% line nr.1 \n  % line2 test % comment in comment\n%3rd\n'''
        ).commentblock()
        expected = ' line nr.1 \n line2 test % comment in comment\n3rd\n'
        self.assertEqual(actual, expected)

    def test_comment(self):
        actual = self.grammar('% asdllljasd\n').comment()
        expected = ' asdllljasd\n'
        self.assertEqual(actual, expected)

    def test_outargs_single(self):
        actual = self.grammar('asd =').outargs()
        expected = ('asd',)
        self.assertTupleEqual(actual, expected)

    def test_outargs_multiple(self):
        actual = self.grammar('[ ...\na, f,... \n    b]=').outargs()
        expected = ('a', 'f', 'b')
        self.assertTupleEqual(actual, expected)

    def test_inargs_none(self):
        actual = self.grammar('()').inargs()
        expected = ()
        self.assertTupleEqual(actual, expected)

    def test_inargs_single(self):
        actual = self.grammar('(...\n asd)').inargs()
        expected = ('asd',)
        self.assertTupleEqual(actual, expected)

    def test_inargs_multiple(self):
        actual = self.grammar('( ...\n a, f, b)').inargs()
        expected = ('a', 'f', 'b')
        self.assertTupleEqual(actual, expected)

if __name__ == '__main__':

    grammar_str = open('matlabdoc_parser3.grammar').read()
    matlab_doc_grammar = makeGrammar(grammar_str, {}, name='matlabdoc')

    f = "/home/dek/Documents/Code/matlabdoc/matlabdoc/tests/matlab_test_dir/realfiledir/m2html.m"
    s = open(f).read()
    # a = matlab_doc_grammar(s).mfile()
    # pprint(a)
    unittest.main()
    sys.exit()
