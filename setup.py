#!/usr/bin/env python

"""

"""

from distutils.core import setup

setup(
    name='MatlabDoc',
    packages=['matlabdoc', ],
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=["Parsley==1.1"],
    url='http://github.com/dk440241/matlabdoc/',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Documentation',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)
