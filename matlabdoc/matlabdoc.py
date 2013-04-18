#!/usr/bin/env python

"""
m2html python port.
"""

import os
import sys
import argparse
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class M2Html(object):
    """Port for m2html
    """
    def __init__(self, args=[]):
        """Run M2Html
        """
        self.logger = logging.getLogger(type(self).__name__)

        self.parser = argparse.ArgumentParser()

        def getonoffargs(isOn=False):
            return dict(choices=['on', 'off'],
                        default=isOn,
                        action=OnOffAction)

        add_arg = self.parser.add_argument
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

        self.opts = self.parser.parse_args(args)
        if self.opts.debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug("Parsed options:% s", self.opts)

    def get_mfiles(self, topdir):
        """Search for correct .m files
        """
        filepaths = []
        dirpaths = []
        for dirname, dirnames, filenames in os.walk(topdir):
            # get new dirs
            new_dirpaths = [os.path.join(dirname, subdirname)
                            for subdirname in dirnames]
            dirpaths += new_dirpaths

            # get new files
            new_filepaths = [os.path.join(dirname, filename)
                             for filename in filenames
                             if os.path.splitext(filename)[1] == '.m']
            filepaths += new_filepaths

            # Editing the 'dirnames' list will stop os.walk()
            # from recursing into there.
            ignored_dirs = [idir for idir in self.opts.ignoreDir
                            if idir in dirnames]
            for dirname in ignored_dirs:
                dirnames.remove(dirname)
            if not self.opts.recursive:
                break
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
