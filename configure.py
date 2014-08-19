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


"""Configuration script that end-users can use to properly setup their environment when using a Qt +
PyQt SDK generated using build.py

"""

from __future__ import print_function

import argparse
import fileinput
import fnmatch
import os
import os.path
import re
import subprocess
import sys

import util


HERE = os.path.abspath(os.path.dirname(__file__))


def main():
    if is_setup_done():
        util.die('SDK setup already done.')

    args = parse_args()
    layout = util.get_layout(args.install_root)

    if not args.no_relocate:
        relocate_qt(layout)
        relocate_sip(layout)

    setup_environment(layout)

    if args.command:
        sys.exit(subprocess.call(args.command))
    elif not args.no_subshell:
        util.start_subshell()


def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-q', '--no-relocate', action='store_true')
    arg_parser.add_argument('-r', '--install-root', type=str, default=HERE, help='alternate install root')
    arg_parser.add_argument('-s', '--no-subshell', action='store_true')
    arg_parser.add_argument('command', nargs='*', metavar='command', help='command (with arguments) to run within the SDK environment')

    return arg_parser.parse_args()


def relocate_qt(layout):
    # We must tell qmake where Qt is installed, otherwise it will use the value hardwired at
    # compile time.
    with open(os.path.join(layout['bin'], 'qt.conf'), 'w') as qt_conf:
        qt_conf.write('[Paths]\n')
        qt_conf.write('Prefix = %s\n' % layout['root'].replace("\\", "/"))

    # .prl files have the library search path hardcoded at install time. We have to rewrite the
    # library search path so that it points to the current location of the SDK on disk.
    linker_path = re.compile(r'\s-L[/\w._]+\s')

    for root, _, filenames in os.walk(layout['root']):
        for filename in fnmatch.filter(filenames, '*.prl'):
            with open(os.path.join(root, filename), 'r+') as prl_file:
                contents = prl_file.read()

                prl_file.seek(0)
                prl_file.write(linker_path.sub(' -L%s ' % layout['lib'], contents))


def relocate_sip(layout):
    # sipconfig.py contains hardcoded paths specific to the system which made the build.
    data = {}
    sipconfig = os.path.join(layout['python'], 'sipconfig.py')
    execfile(sipconfig, data)

    wrong_path = data["_pkg_config"]["sip_mod_dir"].encode("string-escape")

    for L in fileinput.FileInput(sipconfig, inplace=True):
        L = L.replace(wrong_path, layout['root'].encode("string-escape"))
        sys.stdout.write(L)


def is_setup_done():
    return 'QT_PYQT_SDK_SETUP_DONE' in os.environ


def setup_environment(layout):
    os.environ['PATH'] = os.pathsep.join([os.path.join(layout['bin']), os.environ['PATH']])
    os.environ['PYTHONPATH'] = os.path.join(layout['python'])
    os.environ['QTDIR'] = os.path.join(layout['root'])
    os.environ['QT_PLUGIN_PATH'] = os.path.join(layout['plugins'])
    os.environ['QT_PYQT_SDK_SETUP_DONE'] = '1'

    if sys.platform == 'linux2':
        os.environ['LD_LIBRARY_PATH'] = layout['lib']
    elif sys.platform == 'darwin':
        os.environ['DYLD_FRAMEWORK_PATH'] = layout['lib']
        os.environ['DYLD_LIBRARY_PATH'] = layout['lib']
    elif sys.platform == 'win32':
        # Setup Visual C++ 2008 environment variables.
        from distutils.msvccompiler import MSVCCompiler
        msvc = MSVCCompiler()
        msvc.initialize()

        os.environ['INCLUDE'] = os.pathsep.join([layout['include'], os.environ['INCLUDE']])
        os.environ['LIB'] = os.pathsep.join([layout['lib'], os.environ['LIB']])
        os.environ['QMAKESPEC'] = 'win32-msvc2008'

        os.environ['PATH'] = os.pathsep.join([
            os.environ['PATH'],
            # These paths must be __AFTER__ MSVC paths otherwise we pick up
            # link.exe from cygwin instead of MSVC's linker.
            layout['lib'],
            os.path.expandvars(r'%SYSTEMDRIVE%\cygwin64\bin'),
            os.path.expandvars(r'%SYSTEMDRIVE%\Perl64\bin'),
            os.path.expandvars(r'%SYSTEMDRIVE%\Python27'),
            os.path.expandvars(r'%SYSTEMDRIVE%\Ruby193\bin'),
        ])


if __name__ == '__main__':
    main()
