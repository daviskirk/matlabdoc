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
    doc_obj_list = []  # list of dicts where information is held
    doc_obj_dict = {}  # dict where info about the function or class is held
    last_line = ''

    file_obj = open(filename)
    for line in file_obj:
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
        # check line continuation
        rstrip_line = line.rstrip()
        if rstrip_line.endswith('...'):
            last_line = rstrip_line[:-3]  # delete ...
            continue  # next line if line continues
        else:
            # set last line to nothing for no continuation
            last_line = ''

        # look for start of doc object
        doc_obj_dict = _find_doc_obj_start(doc_obj_dict, line)
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


def _find_doc_obj_start(doc_obj_dict, line):
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
    inherit_re_str =  inherit_re_str.format(varname=varname_re_str)
    class_re_str = "(?P<sig>(?P<id>classdef) {varname} ({inherit})?)"
    class_re_str = class_re_str.format(
        inherit=inherit_re_str, varname=varname_re_str)
    class_re_str = class_re_str.replace(' ', space_maybe_re_str)

    doc_obj_re = dict()
    doc_obj_re['function'] = re.compile(function_re_str)
    doc_obj_re['class'] = re.compile(class_re_str)
    return doc_obj_re


# module variables
_doc_obj_re = _get_doc_obj_re()

# setup module logger
logging.basicConfig()
_logger = logging.getLogger(__name__)
# _logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    M = parse_file('tests/test.m')
