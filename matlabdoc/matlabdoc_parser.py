#!/usr/bin/env python

"""Documentation parser for matlab code to generate documentation for
MATLAB code
"""

import re
import logging
import pprint


def parse_file(filename):
    """Parses a file for documentation objects and returns a list of dicts,
    each of which contain documentation and information about the MATLAB
    classes and functions in the file.

    :arg filename: path to file that will be parsed
    """

    # Create doc_obj_dict as a dict where info about the function or class is
    # held Initiate with root doc obj. the root doc object stores information
    # about the file when no functions or classes have been stored yet. In a
    # script file for example, this would be the only object added to the
    # doc_obj_list. As soon as a new function or class definition is found, it
    # is used to store information about it.
    #
    # Additionally, the doc_obj_dict also stores information about the
    # functions that were called since the last definition. If the type is
    # 'root', meaning that no definitions have been found yet, it stores the
    # calls since the beginning of the script file
    doc_obj_dict = dict(type='root', doc='', calls=[])
    # List of dicts where information is held. Each time a function or class
    # definition and its documentation is found it is added to the list.
    doc_obj_list = [doc_obj_dict]
    last_line = ''

    file_obj = open(filename)
    for iLine, line in enumerate(file_obj):
        if doc_obj_dict:
            # look for docstring
            line = line.lstrip()
            if line.startswith('%'):
                # add to docstring
                doc_obj_dict['doc'] += line
            elif line:
                # stop looking for docstring
                # add doc_obj to list
                doc_obj_list.append(doc_obj_dict)
                # reset doc_obj_dict
                doc_obj_dict = {}
        # Check if still looking for docstring: There is no need to parse
        # the rest if we are only looking for docstrings
        if doc_obj_dict:
            continue

        # strip comments
        line = line.partition('%')[0]
        # only one space
        line = " ".join(line.split())

        # connect continued line
        if last_line:
            line = last_line + line
            iLine = iLine - 1
        # check line continuation
        rstrip_line = line.rstrip()
        if rstrip_line.endswith('...'):
            last_line = rstrip_line[:-3]  # delete ...
            continue  # next line if line continues
        else:
            # set last line to nothing for no continuation
            last_line = ''

        # look for start of doc object
        doc_obj_dict = _find_doc_obj_start(doc_obj_dict, line, iLine)

        # look for function identifiers (function calls)
        # add all the found calls to
        for match in _call_re.finditer(line):
            try:
                doc_obj_list[-1]['calls'].add(match.group('name'))
            except AttributeError, KeyError:
                doc_obj_list[-1]['calls'] = set(match.group('name'))

    _logger.debug(pprint.pformat(doc_obj_list))
    return tuple(doc_obj_list)


def _add_to_docstring(doc_obj_dict, line):
    """Add another line to the documentation of the passed documentation
    object if it exists and the line is indeed a continuation of the
    documentation string.

    :arg doc_obj_dict: Dictionary with information about the current
    documentation object. Should be an empty dictionary if no current object is
    being analysed
    :arg line: line that is being searched for a docstring

    """

    return doc_obj_dict


def _find_doc_obj_start(doc_obj_dict, line, iLine):
    """Find start of a doc object (classdef or function) in passed string.
    If no match is found, return an empty dict
    """
    # find function or class
    for key in _doc_obj_re:
        doc_obj_match = _doc_obj_re[key].match(line)
        if doc_obj_match:
            # found doc obj_dict
            doc_obj_dict = doc_obj_match.groupdict()

            # reassign superclasses when dealing with classes
            try:
                doc_obj_dict['supers'] = \
                    doc_obj_dict['supers'].replace(' ', '').split('&')
            except AttributeError:
                doc_obj_dict['supers'] = []
            except KeyError:
                pass  # this is probably a function

            # initiate docstring
            doc_obj_dict['doc'] = ''
            # initiate calls
            doc_obj_dict['calls'] = set()
            # store line this was found in
            try:
                doc_obj_dict['line'] = iLine
            except NameError:
                _logger.debug('no iLine passes,  setting to None')
                doc_obj_dict['line'] = None
            break  # out of: for key in _doc_obj_re
    return doc_obj_dict


def _get_doc_obj_re():
    space_maybe_re_str = '\s?'
    varname_re_str = '[a-zA-Z]\w*'

    outargs_re_str = '((([ {varname}( , {varname})* ])|({varname})) = )?'
    outargs_re_str = outargs_re_str.format(varname=varname_re_str)

    inargs_re_str = '(\( {varname}?( , {varname})* \))?'
    inargs_re_str = inargs_re_str.format(varname=varname_re_str)

    function_re_str = "(?P<sig>(?P<id>function) {O} (?P<name>{fname}) {I})"
    function_re_str = function_re_str.format(
        O=outargs_re_str,
        I=inargs_re_str,
        fname=varname_re_str)
    function_re_str = function_re_str.replace(' ', space_maybe_re_str)

    inherit_re_str = '< (?P<supers>{varname}( & {varname})*)'
    inherit_re_str = inherit_re_str.format(varname=varname_re_str)
    class_re_str = "(?P<sig>(?P<id>classdef) {varname} ({inherit})?)"
    class_re_str = class_re_str.format(
        inherit=inherit_re_str, varname=varname_re_str)
    class_re_str = class_re_str.replace(' ', space_maybe_re_str)

    doc_obj_re = dict()
    doc_obj_re['function'] = re.compile(function_re_str)
    doc_obj_re['class'] = re.compile(class_re_str)
    return doc_obj_re


def _get_call_re():
    """Get regular expression for function call.
    """
    varname_re_str = '[a-zA-Z]\w*'

    call_re = '(?P<namespace>({varname}\.)*)(?P<name>{varname})\s?\('
    call_re = call_re.format(varname=varname_re_str)
    call_re = re.compile(call_re)
    return call_re

# module variables
_doc_obj_re = _get_doc_obj_re()
_call_re = _get_call_re()

# setup module logger
logging.basicConfig()
_logger = logging.getLogger(__name__)
# _logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    M = parse_file('tests/test.m')
