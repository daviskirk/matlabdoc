#!/usr/bin/env python

"""
Matlab documentation parser using parsimonious
"""


import unittest
import collections
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from pprint import pprint

import logging
logging.basicConfig


class MatlabNodeVisitor(NodeVisitor):

    visit_trailing_s = visit_leading_s = visit_scs = lambda s, n, c: None

    @staticmethod
    def flatten(*n):
        """Flattens iterables

        :arg *n:
        """
        return (e for a in n for e in (MatlabNodeVisitor.flatten(*a)
                                       if isinstance(a, (tuple, list))
                                       else (a,)))

    def visit_mfile(self, node, (s1, root_comment, sp2, docobj_or_code)):
        root_comment = root_comment[0] if root_comment else ''
        docobjects = []

        for i, (docobj, codelines) in enumerate(docobj_or_code):
            calls = list(set(MatlabNodeVisitor.flatten(codelines)))
            calls.sort()
            calls = tuple(calls)
            if i == 0 and not docobj:
                docobjects = [dict(key_type='script', calls=calls)]
                break
            docobj = docobj[0]
            docobj['calls'] = calls
            docobjects.append(docobj)
        # add root comment to doc object
        docobjects[0]['doc'] = root_comment + docobjects[0]['doc']
        # split into main and subfunctions
        return dict(main=docobjects[0], sub=docobjects[1:])

    def visit_doc_obj(self, node, (definition_line, commentblock)):
        commentblock = commentblock[0] if commentblock else ''
        doc_obj = {'doc':commentblock}
        doc_obj.update(definition_line)
        return doc_obj

    def visit_definition_line(self, node, (leading_s, definition, trailing)):
        return definition[0]

    def visit_classdef(self, node, (keyword, sc1, cname, sc3, inherit)):
        return dict(key_type='class',
                    name=cname,
                    superclasses=inherit[0] if inherit else ())

    def visit_inherit(self, node, (arrow, sc1, classname1, following)):
        return tuple(node.text.translate(None, ' .\n\r<').split('&'))

    def visit_functiondef(self, node, (keyword, sc1, outargs, sc2, fname, sc3, inargs)):
        return dict(key_type='function',
                    name=fname,
                    outargs=outargs[0] if outargs else (),
                    inargs=inargs[0] if inargs else ())

    def visit_outargs(self, node, ((outargs, ), s1, eq)):
        outargs = outargs[2] if isinstance(outargs, list) else tuple([outargs])
        return outargs

    def visit_inargs(self, node, (brace1, s1, inargs, s2, brace2)):
        inargs = inargs[0] if inargs else ()
        return inargs

    def visit_commma_separated_varlist(self, node, children):
        return tuple(node.text.translate(None, ' \t.\n\r').split(','))

    def visit_varname(self, node, args):
        return node.text

    def visit_commentblock(self, node, comments):
        return ''.join(commentnode[1] for commentnode in comments)

    def visit_comment(self, node, (comment_key, comment_text, newline)):
        return node.text.partition('%')[-1]

    def visit_codeline(self, node, (calls, nl)):
        calls = [call[0] for call in calls if call[0]]
        return calls

    def visit_call(self, node, (fname, s1, paren1)):
        return fname

    def generic_visit(self, node, visited_children):
        """Replace childbearing nodes with a list of their children; keep
        others untouched.

        For our case, if a node has children, only the children are important.
        Otherwise, keep the node around for (for example) the flags of the
        regex rule. Most of these kept-around nodes are subsequently thrown
        away by the other visitor methods.

        We can't simply hang the visited children off the original node; that
        would be disastrous if the node occurred in more than one place in the
        tree.

        """
        # print "{0}: {1}".format(node.expr_name, visited_children)
        return visited_children


class MatlabdocParser2Tests(unittest.TestCase):
    """Tests for parsimonious matlab doc grammar.

    Try to cover most of the syntax possibilities.

    """

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger(__name__ + '.ParserTests')
        self.logger.setLevel(logging.DEBUG)

        self.grammar = Grammar(open("matlabdoc_parser2.grammar").read())
        self.node_viewer = MatlabNodeVisitor()

    def parse(self, expr_name, test_str):
        p = self.grammar[expr_name].parse(test_str)
        return self.node_viewer.visit(p)

    def setUp(self):
        pass

    def test_mfile(self):
        s = ("classdef A < R\n"
             "function a = asd(in1, in2)\n"
             "% asdlhas \n % dddd\n asdasd \n"
             "    function f2()\n"
             "   funccall(a, fcall2(a, b))\n"
             "    last line funccall(3)asddaa\n")
        actual = self.parse('mfile', s)
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
        actual = self.parse('definition_line', '   classdef A  \n')
        expected = dict(key_type='class', name='A', superclasses=())
        self.assertDictEqual(actual, expected)

    def test_definition_line_function(self):
        actual = self.parse('definition_line', '   function a  \n')
        expected = dict(key_type='function', name='a', outargs=(), inargs=())
        self.assertDictEqual(actual, expected)

    def test_classdef(self):
        actual = self.parse('classdef', 'classdef A')
        expected = dict(key_type='class', name='A', superclasses=())
        self.assertDictEqual(actual, expected)

    def test_inherit(self):
        actual = self.parse('inherit', '< S1 & ...\n  S2')
        expected = ('S1', 'S2')
        self.assertTupleEqual(actual, expected)

    def test_functiondef(self):
        actual = self.parse('functiondef', 'function a()')
        expected = dict(key_type='function', name='a', outargs=(), inargs=())
        self.assertDictEqual(actual, expected)

    def test_outargs_single(self):
        actual = self.parse('outargs', 'asd =')
        expected = ('asd',)
        self.assertTupleEqual(actual, expected)

    def test_outargs_multiple(self):
        actual = self.parse('outargs', '[ ...\na, f,... \n    b]=')
        expected = ('a', 'f', 'b')
        self.assertTupleEqual(actual, expected)

    def test_inargs_none(self):
        actual = self.parse('inargs', '()')
        expected = ()
        self.assertTupleEqual(actual, expected)

    def test_inargs_single(self):
        actual = self.parse('inargs', '(...\n asd)')
        expected = ('asd',)
        self.assertTupleEqual(actual, expected)

    def test_inargs_multiple(self):
        actual = self.parse('inargs', '( ...\n a, f, b)')
        expected = ('a', 'f', 'b')
        self.assertTupleEqual(actual, expected)

    def test_commentblock(self):
        actual = self.parse(
            'commentblock',
            '% line nr.1 \n  % line2 test % comment in comment\n%3rd\n')
        expected = ' line nr.1 \n line2 test % comment in comment\n3rd\n'
        self.assertEqual(actual, expected)

    def test_comment(self):
        actual = self.parse('comment', '% asdllljasd\n')
        expected = ' asdllljasd\n'
        self.assertEqual(actual, expected)

    def test_codeline(self):
        # return
        actual = self.parse('codeline', 'asd aasd funcname1  ( func2() )\n')
        expected = ['funcname1', 'func2']
        self.assertEqual(actual, expected)

    def test_call(self):
        actual = self.parse('call', 'funcname1  (')
        expected = 'funcname1'
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    # f = "/home/dek/Documents/Code/matlabdoc/matlabdoc/tests/matlab_test_dir/realfiledir/SuperelementBuilder.m"
    # G = Grammar(open("matlab.grammar").read())
    # nv = MatlabNodeVisitor()

    unittest.main()
    # unittest.main('matlabdoc_parser2', 'MatlabdocParser2Tests.test_call', exit=True, catchbreak=True)
