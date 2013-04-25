#!/usr/bin/env python

"""
Module docstring.
"""

import os
import unittest
import matlabdoc_parser
import matlabdoc_parser2

import logging
logging.basicConfig


class MatlabdocParser2Tests(unittest.TestCase):
    """Tests for parsimonious matlab doc grammar.

    Try to cover most of the syntax possibilities.

    """

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger(__name__ + '.ParserTests')
        self.logger.setLevel(logging.DEBUG)

        self.parser = matlabdoc_parser2.MatlabDocParser()

    # def parse(self, expr_name, test_str):
    #     p = self.grammar[expr_name].parse(test_str)
    #     return self.node_viewer.visit(p)

    def setUp(self):
        pass

    def test_mfile(self):
        s = ("classdef A < R\n"
             "function a = asd(in1, in2)\n"
             "% asdlhas \n % dddd\n asdasd \n"
             "    function f2()\n"
             "   funccall(a, fcall2(a, b))\n"
             "    last line funccall(3)asddaa\n")
        actual = self.parser.parse(s, 'mfile')
        expected = {
            'main':
            {
                'key_type': 'class',
                'doc': '',
                'name': 'A',
                'superclasses': ('R',),
                'calls': ()
            },
            'sub':
            [{
                'inargs': ('in1', 'in2'),
                'doc': ' asdlhas \n dddd\n',
                'outargs': ('a',),
                'name': 'asd',
                'key_type': 'function',
                'calls': ()
            },
             {
                 'inargs': (),
                 'doc': '',
                 'outargs': (),
                 'name': 'f2',
                 'key_type': 'function',
                 'calls': ('fcall2', 'funccall')
             }]}

        self.assertDictEqual(actual, expected)

    def test_definition_line_class(self):
        actual = self.parser.parse('   classdef A  \n', 'definition_line')
        expected = dict(key_type='class', name='A', superclasses=())
        self.assertDictEqual(actual, expected)

    def test_definition_line_function(self):
        actual = self.parser.parse('   function a  \n', 'definition_line')
        expected = dict(key_type='function', name='a', outargs=(), inargs=())
        self.assertDictEqual(actual, expected)

    def test_classdef(self):
        actual = self.parser.parse('classdef A', 'classdef')
        expected = dict(key_type='class', name='A', superclasses=())
        self.assertDictEqual(actual, expected)

    def test_inherit(self):
        actual = self.parser.parse('< S1 & ...\n  S2', 'inherit')
        expected = ('S1', 'S2')
        self.assertTupleEqual(actual, expected)

    def test_functiondef(self):
        actual = self.parser.parse('function a()', 'functiondef')
        expected = dict(key_type='function', name='a', outargs=(), inargs=())
        self.assertDictEqual(actual, expected)

    def test_outargs_single(self):
        actual = self.parser.parse('asd =', 'outargs')
        expected = ('asd',)
        self.assertTupleEqual(actual, expected)

    def test_outargs_multiple(self):
        actual = self.parser.parse('[ ...\na, f,... \n    b]=', 'outargs')
        expected = ('a', 'f', 'b')
        self.assertTupleEqual(actual, expected)

    def test_inargs_none(self):
        actual = self.parser.parse('()', 'inargs')
        expected = ()
        self.assertTupleEqual(actual, expected)

    def test_inargs_single(self):
        actual = self.parser.parse('(...\n asd)', 'inargs')
        expected = ('asd',)
        self.assertTupleEqual(actual, expected)

    def test_inargs_multiple(self):
        actual = self.parser.parse('( ...\n a, f, b)', 'inargs')
        expected = ('a', 'f', 'b')
        self.assertTupleEqual(actual, expected)

    def test_commentblock(self):
        actual = self.parser.parse(
            '% line nr.1 \n  % line2 test % comment in comment\n%3rd\n',
            'commentblock')
        expected = ' line nr.1 \n line2 test % comment in comment\n3rd\n'
        self.assertEqual(actual, expected)

    def test_comment(self):
        actual = self.parser.parse('% asdllljasd\n', 'comment')
        expected = ' asdllljasd\n'
        self.assertEqual(actual, expected)

    def test_codeline(self):
        # return
        actual = self.parser.parse('asd aasd funcname1  ( func2() )\n', 'codeline')
        expected = ['funcname1', 'func2']
        self.assertEqual(actual, expected)

    def test_call(self):
        actual = self.parser.parse('funcname1  (', 'call')
        expected = 'funcname1'
        self.assertEqual(actual, expected)


class MatlabdocParser2SmokeTests(unittest.TestCase):

    def test_matlabdocparser_on_large_file(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'matlab_test_dir/realfiledir/SuperelementBuilder.m')
        parser = matlabdoc_parser2.MatlabDocParser()
        p = parser.parse(open(path).read())
        self.assertEqual(p['main']['key_type'], 'class')
        self.assertEqual(p['main']['name'], 'SuperelementBuilder')
        self.assertEqual(len(p['sub']), 10)

if __name__ == '__main__':
    unittest.main()
    # unittest.main('matlabdoc_parser2', 'MatlabdocParser2SmokeTests', exit=True, catchbreak=True)
