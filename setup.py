#!/usr/bin/env python

"""Setup script for the package."""

import os
import sys

import setuptools


PACKAGE_NAME = 'taskjuggler_python'
MINIMUM_PYTHON_VERSION = '2.7'


def check_python_version():
    """Exit when the Python version is too low."""
    if sys.version < MINIMUM_PYTHON_VERSION:
        sys.exit("Python {0}+ is required.".format(MINIMUM_PYTHON_VERSION))


def read_package_variable(key, filename='__init__.py'):
    """Read the value of a variable from the package without importing."""
    module_path = os.path.join(PACKAGE_NAME, filename)
    with open(module_path) as module:
        for line in module:
            parts = line.strip().split(' ', 2)
            if parts[:-1] == [key, '=']:
                return parts[-1].strip("'")
    sys.exit("'{0}' not found in '{1}'".format(key, module_path))


def build_description():
    """Build a description for the project from documentation files."""
    try:
        readme = open("README.rst").read()
        changelog = open("CHANGELOG.rst").read()
    except IOError:
        return "<placeholder>"
    else:
        return readme + '\n' + changelog


check_python_version()

setuptools.setup(
    name=read_package_variable('__project__'),
    version=read_package_variable('__version__'),

    description="Python interfaces to TaskJuggler 3 planner",
    url='https://github.com/grandrew/taskjuggler-python',
    author='Andrew Gryaznov',
    author_email='realgrandrew@gmail.com',

    packages=setuptools.find_packages(),

    entry_points={'console_scripts': [
        'tjp-client = taskjuggler_python.tjpy_client:main',
        # 'taskjuggler_python-gui = taskjuggler_python.gui:main',
    ]},

    long_description=build_description(),
    license='MIT',
    classifiers=[
        # TODO: update this list to match your application: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    install_requires=[
        # TODO: Add your library's requirements here
        # "testpackage ~= 2.26",
        "icalendar>=3.11",
        "airtable-python-wrapper>=0.8",
        "python-dateutil>=2.6"
    ]
)
