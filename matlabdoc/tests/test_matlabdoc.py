#!/usr/bin/env python

"""
Module docstring.
"""

import os
import unittest
import matlabdoc
import pprint


class TestMatlabdoc(unittest.TestCase):
    """Testing matlabdoc
    """
    def setUp(self):
        self.M = matlabdoc.M2Html()
        self.cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))
        
    def tearDown(self):
        os.chdir(self.cwd)
        
    def test_m2html(self):
        M = matlabdoc.M2Html('--recursive on'.split())
        self.assertEqual(M.opts.recursive, True)
        
    def test_get_mfiles_from_dir(self):
        """Testing Matlabdoc
        """
        self.M.opts.recursive = False
        filepaths = self.M.get_mfiles_from_dir('matlab_test_dir')
        e_filepaths = [
            os.path.join('matlab_test_dir', 'functest.m'),
            os.path.join('matlab_test_dir', 'test.m')
        ]
        
        try:
            self.assertItemsEqual(filepaths, e_filepaths)
        except AssertionError:
            print('filepaths:')
            pprint.pprint(filepaths)
            raise
            
        self.M.opts.recursive = True
        e_filepaths.append(os.path.join('matlab_test_dir',
                                        'subdir', 'subdirfunc.m'))
        filepaths = self.M.get_mfiles_from_dir('matlab_test_dir')
        
        try:
            self.assertItemsEqual(filepaths, e_filepaths)
        except AssertionError:
            print('filepaths:')
            pprint.pprint(filepaths)
            raise
            
    def test_get_filemap(self):
        paths = [
            os.path.join('a', 'b', 'c.m'),
            os.path.join('a', 'b', 'r.m'),
            os.path.join('a', 'c', 't.m'),
            os.path.join('d', 'd', 'y.m')]
        file_dict = self.M.get_filemap(paths)
        e_file_dict = {}
        e_file_dict[os.path.join('a', 'b')] = ['c.m', 'r.m']
        e_file_dict[os.path.join('a', 'c')] = ['t.m']
        e_file_dict[os.path.join('d', 'd')] = ['y.m']
        self.assertDictEqual(file_dict, e_file_dict)
        
    def test_create_doc_dir(self):
        self.M.opts.htmlDir = 'doc'
        self.M.create_doc_dir()
        self.assertTrue(os.path.isdir(self.M.opts.htmlDir))
        os.rmdir(self.M.opts.htmlDir)
        
        self.M.opts.htmlDir = 'matlab_test_dir'
        self.M.create_doc_dir()
        
        # try to write directory onto a filepath
        self.M.opts.htmlDir = 'test_matlabdoc.py'
        with self.assertRaises(matlabdoc.NoDirectoryAtDocdirError):
            self.M.create_doc_dir()
            
    def test_get_mfiles(self):
        self.M.opts.mFiles = [os.path.join('matlab_test_dir', 'test.m')]
        filepaths = self.M.get_mfiles()
        e_filepaths = tuple(self.M.opts.mFiles)
        self.assertEqual(filepaths, e_filepaths)
        
        self.M.opts.mFiles = ['matlab_test_dir']
        
        # create mock output for _get_files_from_dir
        def mock_get_mfiles_from_dir(arg):
            return ['file1', 'file1', os.path.join('matlab_test_dir', 'test.m')]
        self.M.get_mfiles_from_dir = mock_get_mfiles_from_dir
        # evaluate test function
        filepaths = self.M.get_mfiles()
        # create expected output
        e_filepaths = tuple(['file1', os.path.join('matlab_test_dir', 'test.m')])
        self.assertTupleEqual(filepaths, e_filepaths)
        
if __name__ == "__main__":
    unittest.main()
    
