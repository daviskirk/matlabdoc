#!/usr/bin/env python

"""
m2html python port.
"""

import os
import sys
import argparse
import logging
import parsley

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class M2Html(object):
    """Port for m2html
    """
    def __init__(self, args=[]):
        """Run M2Html
        """
        self.logger = logging.getLogger(type(self).__name__)
        self.matlab_parser = self._get_matlab_parser()
        self.argparser = argparse.ArgumentParser()

        def getonoffargs(isOn=False):
            return dict(choices=['on', 'off'],
                        default=isOn,
                        action=OnOffAction)

        add_arg = self.argparser.add_argument
        add_arg('--mFiles', default=os.path.curdir)
        add_arg('--htmlDir', default='doc')
        add_arg('--recursive', **getonoffargs())
        add_arg('--source', **getonoffargs(True))
        add_arg('--download', **getonoffargs())
        add_arg('--syntaxHighlighting', **getonoffargs())
        add_arg('--tabs')
        add_arg('--globalHypertextLinks', **getonoffargs())
        add_arg('--graph', **getonoffargs())
        add_arg('--todo', **getonoffargs())
        add_arg('--load')
        add_arg('--save')
        add_arg('--search', **getonoffargs())
        add_arg('--helptocxml', **getonoffargs())
        add_arg('--indexFile', default='index')
        add_arg('--extension', default='html')
        add_arg('--template', default='default')
        add_arg('--rootdir', default=os.path.abspath(os.path.curdir))
        add_arg('--ignoreDir', default=['.svn', 'cvs', '.git'])
        add_arg('--language', choices=['english'], default='english')
        add_arg('--debug', action='store_true')

        self.opts = self.argparser.parse_args(args)
        if self.opts.debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug("Parsed options:% s", self.opts)

    def join_paths_rel(self, *paths):
        """Join paths and return the joined path relative to current directory.

        """
        path = os.path.join(*paths)
        path = os.path.relpath(path)
        return path

    def get_mfiles(self):
        filepaths = []
        for path in self.opts.mFiles:
            if os.path.isfile(path):
                filepaths.append(path)
            elif os.path.isdir(path):
                filepaths += self.get_mfiles_from_dir(path)
            else:
                raise ValueError('Path %s is neither a file nor a directory!',
                                 path)
        # make this a sorted tuple
        filepaths = tuple(list(set(filepaths)).sort())
        return filepaths

    def create_doc_dir(self):
        """Create doc dir if it does not exist
        """
        try:
            os.mkdirs(self.opts.htmlDir)
            self.logger.info('creating doc directory: %s', self.opts.htmlDir)
        except OSError:
            if os.path.isdir(self.opts.htmlDir):
                self.logger.info('directory %s exists... OK',
                                 self.opts.htmlDir)
            else:
                self.logger.debug('failed to create directory %s... error:',
                                  self.opts.htmlDir)
                raise

    def _get_matlab_parser(self):
        matlab_grammer_str = textwrap.dedent(r"""
        # whitespace in line
        sp = (' ' | '\t')*

        # line continuing
        linecont = sp '...' nl
        spa = sp linecont*
        nl = sp <('\r' '\n' | '\r' | '\n')> sp
        wsa = ws '...'? ws

        # comments
        comment = ('%' <(~nl anything)*>:commentcontent) -> commentcontent
        commentblock = ((sp comment:comment nl) -> comment)+:comments -> "\n".join(comments)

        # vars and vectors
        varvec = <'[' wsa (varname:varname wsa (',' | ';')? wsa)* ']'>
        varname = <letter (letterOrDigit | '_')*>

        parenexp = '(' (~')' anything)* ')'

        # function definitions
        fdef = (( <'function' sp (outargs spa '=' spa)? varname:fname spa inargs:inargs>):sig nl) -> [('type', 'function'), ('name', fname), ('signature', sig)]
        cdef = (( <'classdef' sp varname:cname (inherit |sp -> []):superclasses> ):sig nl)-> [('type','class'), ('name',cname), ('signature',sig), ('superclasses', superclasses)]
        inherit = (spa '<' spa varname:v1 spa ((('&' spa varname:vother spa)->vother)+|->[]):vothers) -> [v1]+vothers

        f_or_c_def = (fdef | cdef)
        argvarlist = <'(' wsa (varname wsa ','? wsa)* ')'>:str -> str.translate(None,".()\r\n").split(',')
        inargs = argvarlist | -> ['']
        outargs = ((varname:arg -> [arg])| varvec)
        # outargs in function context
        foutargs = ((outargs:outargs spa '=' spa) ->outargs) | -> []

        # keys
        methodkey = 'methods'
        propertykey = 'properties'

        # code
        code = (comment? (~f_or_c_def anything))*

        # docstring and cocumentation parsers
        docobj = f_or_c_def:fcdef ws (commentblock?:docstr -> docstr)-> dict([('doc', docstr)] + fcdef)
        doclist = code ((docobj:d code) -> d)+:ds -> ds
        """)
        matlab_parser = parsley.makeGrammar(matlab_grammer_str)
        return matlab_parser

    def parse_m_file(self, m_file):
        """Parse .m file using the matlab parser and return a parsed list

        """
        return self.matlab_parser(m_file).doclist()

    def get_filemap(self, paths):
        """Map files to unique directories.

        Constructs a dict where the keys are the directorypaths relative to the
        documentation root. The dict values are the filenames of the files that
        are located in the key directory.

        :arg paths: iterable of paths

        """
        file_dict = dict()
        dirs_and_files = [os.path.split(ipath) for ipath in paths]
        # map files to unique dirnames
        for dirname, filename in dirs_and_files:
            file_dict[dirname] = filename

    def write_doc_file(self, doc_dict, doc_file_path):
        """

        :arg doc_dict:
        :arg doc_file_path:
        """
        pass

    def get_mfiles_from_dir(self, topdir):
        """Search for correct .m files in a directory
        """
        filepaths = []
        for dirname, dirnames, filenames in os.walk(topdir):
            # add new files
            filepaths += [self.join_paths_rel(dirname, filename)
                          for filename in filenames
                          if os.path.splitext(filename)[1] == '.m']

            # Editing the 'dirnames' list will stop os.walk()
            # from recursing into there.
            if self.opts.recursive:
                ignored_dirs = [idir for idir in self.opts.ignoreDir
                                if idir in dirnames]
                for dirname in ignored_dirs:
                    dirnames.remove(dirname)
            else: # if not recursive do not continue with any directories
                dirnames = []
        return filepaths

        # self.logger.debug(filepaths)


class OnOffAction(argparse.Action):
    """Action to handle different strings as boolean values
    """

    TRUE_STRINGS = ['on', "On", "True", "true", "1", "yes", "YES"]
    FALSE_STRINGS = ['off', "Off", "False", "false", "1", "no", "No"]

    def __call__(self, parser, namespace, values, option_string=None):
        logger.debug(values)
        if values in OnOffAction.TRUE_STRINGS:
            isOn = True
        elif values in OnOffAction.FALSE_STRINGS:
            isOn = False
        else:
            raise ValueError('only on or off can be switched')
        setattr(namespace, self.dest, isOn)


if __name__ == '__main__':
    print(sys.argv)
    M = M2Html(sys.argv[1:])
