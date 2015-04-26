#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2014  Develer S.r.L.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# #############################################################################
# NOTE: if not in github.com/develersrl/qt-pyqt-sdk-builder sources           #
# this file is overwritten every build.py run and copied in the generated SDK #
# #############################################################################

"""Support methods used in both build.py and configure.py"""

from __future__ import print_function

import argparse
import contextlib
import distutils.dir_util
import json
import os
import os.path
import platform
import subprocess
import sys
import tarfile
import zipfile


# Utility functions to be used as type=afunc in argparse arguments

def adir(apath):
    if os.path.isdir(apath):
        return apath
    else:
        raise argparse.ArgumentTypeError("%r not found, provide an existing dir" % apath)


def mkdir(apath):
    if os.path.exists(apath):
        return apath
    try:
        os.makedirs(apath)
        return apath
    except:
        raise argparse.ArgumentTypeError("Unable to create %r dir" % apath)


def afile(apath):
    if os.path.exists(apath) and not os.path.isdir(apath):
        return apath
    else:
        raise argparse.ArgumentTypeError("%r not found, provide an existing file" % apath)


def ajson(apath):
    return json.load(open(afile(apath)))


def maybe(afunc, default=None, verbose=False):
    def _maybe(value):
        try:
            return afunc(value)
        except Exception as err:
            if verbose:
                print(err)
            return default
    return _maybe


@contextlib.contextmanager
def chdir(path):
    """Changes current working directory for the life of the context manager."""
    cwd = os.path.abspath(os.getcwd())

    try:
        os.chdir(path)

        print("+ cd", os.path.abspath(path))

        yield
    finally:
        os.chdir(cwd)

        print("+ cd", cwd)


def platform_root(install_root, build_type='dynamic'):
    """
    Given the root directory of an SDK installation, returns the platform specific installation
    root.

    """
    if build_type not in ('static', 'dynamic'):
        raise ValueError('build_type must be either "static" or "dynamic"')

    platform_name = str(platform.system() + "-" + platform.architecture()[0]).lower()

    return os.path.join(install_root, build_type, platform_name)


def get_layout(install_root):
    """Returns a dictionary representing the layout of an SDK installation.

    For example, the 'bin' key points to the directory which contains the executables under the
    given installation root.

    Additionally, the installation root is checked to make sure all required files and directories
    are there. Since this is an expensive operation, the result of calling get_layout() should be
    cached and passed around instead of invoking this function each time.

    """
    rootdir = os.path.abspath(install_root)
    pydir = 'python%s.%s' % sys.version_info[:2]

    layout = {
        'root': rootdir,                               # Installation root
        'bin': os.path.join(rootdir, 'bin'),           # Executables
        'include': os.path.join(rootdir, 'include'),   # Includes
        'lib': os.path.join(rootdir, 'lib'),           # Libraries
        'plugins': os.path.join(rootdir, 'plugins'),   # Qt Plugins
        'python': os.path.join(rootdir, pydir),        # Python libraries
        'sip': os.path.join(rootdir, 'share', 'sip'),  # SIP files
    }

    # Sanity check
    for path in layout.values():
        if not os.path.isdir(path):
            print('WARNING: Missing required directory %s' % path)

    sipconfig = os.path.join(layout['python'], 'sipconfig.py')

    if not os.path.isfile(sipconfig):
        print('WARNING: Missing required file %s' % sipconfig)

    return layout


def start_subshell():
    print_box('Starting a subshell with the environment properly set-up for you.')

    if sys.platform == 'win32':
        sh(os.environ['COMSPEC'], '/K')
    else:
        sh(os.environ['SHELL'])

    print_box('Goodbye.')


def print_box(*args):
    print('')
    print('=' * 78)

    for message in args:
        print('{:^78}'.format(message))

    print('=' * 78)
    print('')


copy_tree = distutils.dir_util.copy_tree


def sh(*args, **kwargs):
    print('+', ' '.join(args))
    env = os.environ.copy() if kwargs.get("copy_env", True) else None
    return subprocess.check_call(args, stderr=sys.stderr, stdout=sys.stdout, env=env)


def expand(source, dest=None):
    if source.endswith(".zip"):
        zipfile.ZipFile(source).extractall(dest)
    else:
        tarfile.open(source).extractall(dest)


def die(*args):
    print('')

    for message in args:
        print(message)

    print('Aborting.')

    sys.exit(1)
