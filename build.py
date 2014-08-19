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

from __future__ import print_function

import argparse
import collections
import fnmatch
import glob
import json
import multiprocessing
import os
import os.path
import platform
import re
import shutil
import subprocess
import sys
import tarfile

import sdk

#
# Paths
#

HERE = os.path.abspath(os.path.dirname(__file__))
HOME = os.path.expanduser('~')
PYQT_LICENSE_FILE = os.path.join(HERE, 'pyqt-commercial.sip')
QT_LICENSE_FILE = os.path.join(HERE, 'qt-license.txt')


def main():
    args = parse_command_line()

    # Load build profile
    with open(args.profile, 'r') as f:
        profile = json.load(f)

    # Autodiscover source directories, if possible.
    args.with_icu_sources = args.with_icu_sources or find_source_dir('icu*')
    args.with_qt_sources = args.with_qt_sources or find_source_dir('qt-everywhere-*')
    args.with_sip_sources = args.with_sip_sources or find_source_dir('sip-*')
    args.with_pyqt_sources = args.with_pyqt_sources or find_source_dir('PyQt-*')

    # Prepare the build plan
    plan = []

    if sys.platform == 'darwin' or sys.platform == 'win32':
        # We need to build ICU from sources only on OS X and Windows. On Ubuntu we can usually
        # rely on ICU being installed system wide.
        add_to_plan(plan, 'icu', build_icu, args.with_icu_sources)

    add_to_plan(plan, 'qt', build_qt, args.with_qt_sources)
    add_to_plan(plan, 'sip', build_sip, args.with_sip_sources)
    add_to_plan(plan, 'pyqt', build_pyqt, args.with_pyqt_sources)

    # If user specified some packages on the command line, build only those
    if args.packages:
        plan = filter(lambda x: x[0] in args.packages, plan)

    # Determine install root
    if args.install_root:
        install_root = args.install_root
    else:
        qt_version = extract_version(args.with_qt_sources)
        sip_version = extract_version(args.with_sip_sources)
        pyqt_version = extract_version(args.with_pyqt_sources)
        plat = sys.platform
        arch = platform.architecture()[0]
        build_type = 'debug' if args.debug else 'release'
        install_root = os.path.join(HERE, '_out', 'qt-%s-sip-%s-pyqt-%s-%s-%s-%s' % (qt_version, sip_version, pyqt_version, plat, arch, build_type))

    # Get this installation's layout
    layout = sdk.get_layout(install_root)

    # Build
    prep(layout)
    build(plan, layout, args.debug, profile)
    install_scripts(install_root)
    package(install_root, '%s.tar.gz' % (os.path.basename(install_root)))


def parse_command_line():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--debug', action='store_true')
    args_parser.add_argument('--install-root', type=str)
    args_parser.add_argument('--profile', type=str, required=True)
    args_parser.add_argument('--with-icu-sources', type=str)
    args_parser.add_argument('--with-pyqt-sources', type=str)
    args_parser.add_argument('--with-qt-sources', type=str)
    args_parser.add_argument('--with-sip-sources', type=str)
    args_parser.add_argument('packages', metavar='packages', nargs='*')

    return args_parser.parse_args()


def find_source_dir(glob_pattern):
    candidates = [d for d in glob.glob(os.path.join(HERE, '_source', glob_pattern)) if os.path.isdir(d)]

    if candidates:
        return candidates[0]
    else:
        return None


def add_to_plan(plan, component_name, build_f, source_directory):
    if not source_directory:
        print('%s: need a source directory.' % component_name)
        sys.exit(1)

    if not os.path.isdir(source_directory):
        print('%s: No such directory: %s' % (compenent_name, source_directory))
        sys.exit(1)

    plan.append((component_name, build_f, source_directory))


def extract_version(path):
    assert os.path.isdir(path)
    found = re.findall(r'\d+\.\d+\.\d+', path)
    assert len(found) == 1
    return found[0]


def prep(layout):
    make_install_root_skel(layout)

    import configure
    configure.setup_environment(layout)


def make_install_root_skel(layout):
    for d in layout.values():
        if not os.path.isdir(d):
            os.makedirs(d)


def build(recipes, layout, debug, profile):
    for pkg, build_f, src_dir in recipes:
        sdk.print_box('Building %s' % pkg, src_dir)

        with sdk.chdir(src_dir):
            build_f(layout, debug, profile)


def install_scripts(install_root):
    shsdk.copyfile(os.path.join(HERE, 'configure.py'), os.path.join(install_root, 'configure.py'))
    shsdk.copyfile(os.path.join(HERE, 'sdk.py'), os.path.join(install_root, 'sdk.py'))


def package(install_root, archive_name):
    parent, root_dir = os.path.split(install_root)

    try:
        t = tarfile.open(archive_name, 'w:gz')

        with sdk.chdir(parent):
            t.add(root_dir)
    finally:
        t.close()

#
# Build recipes
# Function prototype: def f(layout, debug, profile) :: dict -> bool -> dict
#

def build_icu(layout, debug, profile):
    # NOTE: We always build ICU in release mode since we don't usually need to debug it.
    os.chdir('source')

    if sys.platform == 'darwin':
        sdk.sh('chmod', '+x', 'configure', 'runConfigureICU')
        sdk.sh('bash', 'runConfigureICU', 'MacOSX', '--prefix=%s' % layout['root'], '--disable-debug', '--enable-release')
        sdk.sh('make')
        sdk.sh('make', 'install')
    elif sys.platform == 'win32':
        # Convert native install_root path to one accepted by Cygwin (e.g.: /cygdrive/c/foo/bar)
        cy_install_root = layout['root'].replace('\\', '/')
        cy_install_root = cy_install_root.replace('C:/', '/cygdrive/c/')

        sdk.sh('bash', 'runConfigureICU', 'Cygwin/MSVC', '--prefix=%s' % cy_install_root, '--disable-debug', '--enable-release')
        sdk.sh('bash', '-c', 'make')  # We have to use GNU make here, so no make() wrapper...
        sdk.sh('bash', '-c', 'make install')
    else:
        sdk.die('You have to rebuild ICU only on OS X or Windows')


def build_qt(layout, debug, profile):
    if os.path.isfile(QT_LICENSE_FILE):
        license = '-commercial'

        shsdk.copy(QT_LICENSE_FILE, os.path.join(HOME, ".qt-license"))
    else:
        license = '-opensource'

    # Bootstrap configure.exe on Windows so that we can re-use the UNIX source
    # tarball which doesn't have configure.exe pre-built like the Win32
    # version. To do this, we 'touch' qtbase\.gitignore.
    if is_qt5():
        with open(os.path.join('qtbase', '.gitignore'), 'w') as f:
            pass

    # Configure
    qt_configure_args = [
        '-confirm-license',
        '-prefix', layout['root'],
        '-shared',
        license
    ]

    # Configure: load profile
    qt_configure_args.extend(profile['qt']['common'])

    if sys.platform in profile['qt']:
        qt_configure_args.extend(profile['qt'][sys.platform])

    # Configure: debug build?
    if debug and sys.platform == 'win32':
        shsdk.copyfile(os.path.join(HERE, 'mkspecs', 'qt4-win32-msvc2008-relwithdebinfo.conf'), os.path.join('mkspecs', 'win32-msvc2008', 'qmake.conf'))

        qt_configure_args.append('-release')
    elif debug:
        qt_configure_args.append('-debug')
    else:
        qt_configure_args.append('-release')

    # Configure: have the compiler find our local copy of ICU
    if sys.platform == 'darwin' or sys.platform == 'win32':
        qt_configure_args.extend(['-I', os.path.join(layout['root'], 'include')])
        qt_configure_args.extend(['-L', os.path.join(layout['root'], 'lib')])

    # Configure: build Qt 4 with clang on OS X
    if sys.platform == 'darwin' and os.path.isfile('/usr/bin/clang') and not is_qt5():
        qt_configure_args.extend(['-platform', 'unsupported/macx-clang'])

    # Configure: enable parallel build on Windows
    if sys.platform == 'win32':
        qt_configure_args.append('-mp')

    # Build
    configure_qt(*qt_configure_args)
    make()
    make('install')

    # Delete all libtool's .la files
    for root, dirnames, filenames in os.walk(layout['root']):
        for filename in fnmatch.filter(filenames, '*.la'):
            os.remove(os.path.join(root, filename))


def build_sip(layout, debug, profile):
    configure_args = [
        '--bindir', layout['bin'],
        '--destdir', layout['python'],
        '--incdir', layout['include'],
        '--sipdir', layout['sip'],
    ]

    set_pyqt_debug_flags(debug, configure_args)

    configure(*configure_args)
    make()
    make('install')


def build_pyqt(layout, debug, profile):
    if os.path.isfile(PYQT_LICENSE_FILE):
        shsdk.copyfile(PYQT_LICENSE_FILE, os.path.join('sip', 'pyqt-commercial.sip'))

    # Configure
    configure_args = [
        '--assume-shared',
        '--bindir', layout['bin'],
        '--concatenate',
        '--concatenate-split=4',
        '--confirm-license',
        '--destdir', layout['python'],
        '--no-designer-plugin',
        '--no-docstrings',
        '--no-sip-files',
        '--sip=%s' % os.path.join(layout['bin'], 'sip.exe' if sys.platform == 'win32' else 'sip'),
        '--verbose',
    ]

    set_pyqt_debug_flags(debug, configure_args)

    # Build
    configure(*configure_args)
    make()
    make('install')

#
# Utility methods
#

def is_qt5():
    return os.path.isdir('qtbase')


def configure(*args):
    sdk.sh(sys.executable, 'configure.py', *args)


def configure_qt(*args):
    if sys.platform == 'win32':
        configure_exe = 'configure.bat' if is_qt5() else 'configure.exe'
    else:
        configure_exe = './configure'

    sdk.sh(configure_exe, *args)


def make(*args):
    if sys.platform == 'win32':
        sdk.sh('nmake', *args)
    else:
        sdk.sh('make', '-j%s' % str(multiprocessing.cpu_count() + 1), *args)


def set_pyqt_debug_flags(debug, configure_args):
    if debug:
        if sys.platform == 'win32':
            configure_args.append('CFLAGS=/O2 /Zi')
            configure_args.append('CXXFLAGS=/O2 /Zi')
            configure_args.append('LFLAGS=/DEBUG /INCREMENTAL:NO /OPT:REF')
        else:
            configure_args.append('--debug')

#
# Entry point
#

if __name__ == '__main__':
    main()
