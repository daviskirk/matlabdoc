#!/usr/bin/env python

"""
Matlab documentation parser using parsimonious
"""

import os
import collections
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from pprint import pprint


class MatlabDocParser(NodeVisitor):
    """Object for parsing matlab code and extracting documentation from them.

    Uses :mod:`parsimonious` as a parsing backend and subclasses
    :class:`parsimonious.NodeVisitor` for post - processing. The parsimonious
    grammar is located in the file *matlabdoc_parser2.grammar*.

    For usage, see :func:`MatlabDocParser.parse`

    """

    _grammar = Grammar(open(os.path.join(os.path.dirname(__file__),
                                         "matlabdoc_parser2.grammar")).read())

    visit_trailing_s = visit_leading_s = visit_scs = lambda s, n, c: []

    def parse(self, mfile_string, expr_name='mfile'):
        """Parses a string of matlab code and returns a dictionary with information
        about the strings matlab documentation. The string is interpreted as a
        .m file.

        The field 'main' holds the information about the first documentation
        object in the string (function or class). If neither a function or
        class were found, it interprets the string as a matlab script.

        The field 'sub' is a list of dicts and holds all subfunctions (or
        methods) found in the string.

        Documentation objects have 3 different types:

        - class
        - function
        - script

        Each object is described by a dictionary with a key 'key_type'. The
        'key_type' field holds a string (either 'class', 'function' or
        'script'). All other fields can differ depending on the type of
        documentation object.

        Here are a list of fields sorted by documenation object type:

        +--------------------+-------------+----------------+--------------+
        | key_type           | ``'class'`` | ``'function'`` | ``'script'`` |
        +====================+=============+================+==============+
        | name               | **x**       | **x**          | -            |
        +--------------------+-------------+----------------+--------------+
        | superclasses       | **x**       | -              | -            |
        +--------------------+-------------+----------------+--------------+
        | calls              | **x**       | **x**          | **x**        |
        +--------------------+-------------+----------------+--------------+
        | doc                | **x**       | **x**          | **x**        |
        +--------------------+-------------+----------------+--------------+
        | signature **TODO** | **x**       | **x**          | -            |
        +--------------------+-------------+----------------+--------------+

        >>> from matlabdoc_parser2 import MatlabDocParser
        >>> parser = MatlabDocParser()
        >>> parsed = parser.parse("function out = dosomething(in)\n% Docstring\n")
        >>> parsed
        {'main':{'key_type':'function', 'doc':' Docstring\n'}, 'sub':[]}
        """

        p = self._grammar[expr_name].parse(mfile_string)
        return NodeVisitor.visit(self, p)

    def visit_mfile(self, node, (s1, root_comment, sp2, code_sections)):
        """Visits an mfile parsimonious node and extracts a dict from the node
        and its children.

        """
        root_comment = root_comment[0] if root_comment else ''
        docobjects = []

        # loop over
        is_maybe_script = True
        for docobj, codelines in code_sections:
            calls = MatlabDocParser.get_sorted_unique_tuple(
                MatlabDocParser.flatten(codelines))
            if is_maybe_script:
                # In case no function and no class were found at the beginning
                # of the file it means that we are dealing with a script file.
                # In either case, we know then know if this is a script or not
                is_script_maybe = False
                if not docobj:
                    docobjects = [dict(key_type='script', calls=calls, doc='')]
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

    @staticmethod
    def get_sorted_unique_tuple(list_like):
        """Return a sorted unique tuple from the list like input

        :arg list_like: iterable to be converted
        """
        list_like = list(set(list_like))
        list_like.sort()
        list_like = tuple(list_like)
        return list_like

    @staticmethod
    def flatten(*n):
        """Creates a generator that flattens iterables.

        :arg *n: comma sperated list of iterables that should be joined
        together into a flattened iterable

        """
        return (e for a in n for e in (MatlabDocParser.flatten(*a)
                                       if isinstance(a, (tuple, list)) else (a,)))


if __name__ == '__main__':
    print "Running tests for " + __file__
    import unittest
    import tests.test_matlabdoc_parser
    unittest.main(tests.test_matlabdoc_parser)
