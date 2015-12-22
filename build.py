#!/usr/bin/env python2.7
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
import fnmatch
import glob
import multiprocessing
import os
import os.path
import shutil
import sys

import sdk

#
# Paths
#

HERE = os.path.abspath(os.path.dirname(__file__))
HOME = os.path.expanduser('~')
PYQT_LICENSE_FILE = os.path.join(HERE, 'pyqt-commercial.sip')
QT_LICENSE_FILE = os.path.join(HERE, 'qt-license.txt')
SUPPORT_DIR = os.path.join(HERE, 'support')
EXECUTABLE_EXT = ".exe" if sys.platform == 'win32' else ""


def check_bash():
    try:
        sdk.sh("bash", "--version")
    except:
        sdk.die("ERROR: unable to run 'bash', check your PATH")


def main():
    args = parse_command_line()

    # Prepare the build plan
    # plan :: (component_name, build_function, abs_source_directory_path)
    plan = []

    def add_to_plan(plan, component_name, build_f, source_directory):
        plan.append((component_name, build_f, source_directory))

    add_to_plan(plan, 'icu', build_icu, args.with_icu_sources)
    add_to_plan(plan, 'qt', build_qt, args.with_qt_sources)
    add_to_plan(plan, 'sip', build_sip, args.with_sip_sources)
    add_to_plan(plan, 'pyqt', build_pyqt, args.with_pyqt_sources)

    # If user specified some packages on the command line, build only those
    if args.packages != 'all':
        plan = [entry for entry in plan if entry[0] in args.packages]

    # Get this installation's layout
    layout = sdk.get_layout(sdk.platform_root(args.install_root))

    # Setup build environment
    prep(layout)

    # --only-merge stops the build here.
    if args.only_merge:
        merge(layout)
        return

    # --shell stops the build here.
    if args.shell:
        sdk.start_subshell()
        return

    # --only-scripts stops the build here.
    if args.only_scripts:
        install_scripts(args.install_root)
        return

    # Build
    build(plan, layout, args.debug, args.profile)
    merge(layout)
    install_scripts(args.install_root)


def parse_command_line():
    args_parser = argparse.ArgumentParser()

    def check_source_dir(glob_pattern):
        sdk.print_box("Sources discovery for %r..." % glob_pattern)
        sources_pattern = os.path.join(HERE, 'sources', glob_pattern)
        sources_pattern_platform = os.path.join(sdk.platform_root('sources'), glob_pattern)
        globs = glob.glob(sources_pattern) + glob.glob(sources_pattern_platform)
        candidates = [d for d in globs if os.path.isdir(d)]

        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            argparse.ArgumentTypeError(
                "Too many candidates for %s: %s" % (glob_pattern, ", ".join(candidates)))
        else:
            argparse.ArgumentTypeError("%r not found, provide an existing folder" % glob_pattern)

    args_parser.add_argument('-d', '--debug', action='store_true')
    args_parser.add_argument(
        '-k', '--shell', action='store_true', help="starts a shell just before starting the build")
    args_parser.add_argument(
        '-m', '--only-merge', action='store_true', help="Merge user provided files from ./merge")
    args_parser.add_argument('-n', '--only-scripts', action='store_true',
                             help='Skip build step, update install scripts only')
    args_parser.add_argument(
        '-p', '--profile', type=sdk.maybe(sdk.ajson, {}), help="json config file for Qt build")
    args_parser.add_argument('-r', '--install-root', help="default: %(default)s", type=sdk.mkdir,
                             default=os.path.join(HERE, '_out'))
    args_parser.add_argument('-c', '--with-icu-sources',  type=sdk.adir)
    args_parser.add_argument('-t', '--with-pyqt-sources', type=sdk.adir)
    args_parser.add_argument('-q', '--with-qt-sources',   type=sdk.adir)
    args_parser.add_argument('-s', '--with-sip-sources',  type=sdk.adir)
    args_parser.add_argument('packages', metavar='PACKAGES', nargs='*', choices=['sip', 'qt', 'pyqt', 'icu', 'all'],
                             default='all', help="Build only selected packages from {%(choices)s}, default: %(default)s")

    args = args_parser.parse_args()

    def has_package(pkg):
        return (pkg in args.packages or "all" in args.packages)

    if args.with_icu_sources is None:
        args.with_icu_sources = check_source_dir('icu*')
    if args.with_pyqt_sources is None:
        args.with_pyqt_sources = check_source_dir('PyQt-*')
    if args.with_qt_sources is None:
        args.with_qt_sources = check_source_dir('qt-everywhere-*')
    if args.with_sip_sources is None:
        args.with_sip_sources = check_source_dir('sip-*')

    if has_package("icu"):
        if sys.platform == 'win32':
            check_bash()

    # to rebuild Qt.
    if has_package("qt"):
        if not args.profile:
            sdk.die('I need a profile in to rebuild Qt!')

    return args


def prep(layout):
    make_install_root_skel(layout)

    sdk_configure = __import__('configure')
    sdk_configure.setup_environment(layout)


def make_install_root_skel(layout):
    for path in layout.values():
        if not os.path.isdir(path):
            os.makedirs(path)


def build(recipes, layout, debug, profile):
    for pkg, build_f, src_dir in recipes:
        sdk.print_box('Building %s' % pkg, src_dir)

        with sdk.chdir(src_dir):
            build_f(layout, debug, profile)


def merge(layout):
    merge_dir = os.path.join(HERE, 'merge')

    if os.path.isdir(merge_dir):
        sdk.print_box('Merging %s' % merge_dir, 'into', layout['root'])

        sdk.copy_tree(merge_dir, layout['root'])
    else:
        print('No files to merge.')


def install_scripts(install_root):
    sdk.print_box('Installing configure.py and sdk.py to:', install_root)

    shutil.copyfile(
        os.path.join(HERE, 'configure.py'), os.path.join(install_root, 'configure.py'))
    shutil.copyfile(os.path.join(HERE, 'sdk.py'), os.path.join(install_root, 'sdk.py'))

#
# Build recipes
# Function prototype: def f(layout, debug, profile) :: dict -> bool -> dict
#

def build_icu(layout, debug, profile):
    # NOTE: We always build ICU in release mode since we don't usually need to debug it.
    os.chdir('source')

    if sys.platform == 'darwin':
        sdk.sh('chmod', '+x', 'configure', 'runConfigureICU')
        sdk.sh('bash', 'runConfigureICU', 'MacOSX', '--prefix=%s' %
               layout['root'], '--disable-debug', '--enable-release')
        sdk.sh('make')
        sdk.sh('make', 'install')
    elif sys.platform == 'linux2':
        sdk.sh('chmod', '+x', 'configure', 'runConfigureICU')
        sdk.sh('bash', 'runConfigureICU', 'Linux', '--prefix=%s' %
               layout['root'], '--disable-debug', '--enable-release')
        sdk.sh('make')
        sdk.sh('make', 'install')
    elif sys.platform == 'win32':
        # Convert native install_root path to one accepted by Cygwin (e.g.: /cygdrive/c/foo/bar)
        cy_install_root = layout['root'].replace('\\', '/')
        cy_install_root = cy_install_root.replace('C:/', '/cygdrive/c/')

        sdk.sh('bash', 'runConfigureICU', 'Cygwin/MSVC', '--prefix=%s' %
               cy_install_root, '--disable-debug', '--enable-release')
        sdk.sh('bash', '-c', 'make')  # We have to use GNU make here, so no make() wrapper...
        sdk.sh('bash', '-c', 'make install')
    else:
        sdk.die('You have to rebuild ICU only on OS X or Windows')


def build_qt(layout, debug, profile):

    def qtmake(*args):
        try:
            sdk.sh('jom', '/VERSION')
        except:
            make(*args)
        else:
            sdk.sh('jom', '-j%s' % str(multiprocessing.cpu_count() + 1), *args)

    if os.path.isfile(QT_LICENSE_FILE):
        qt_license = '-commercial'

        shutil.copy(QT_LICENSE_FILE, os.path.join(HOME, ".qt-license"))
    else:
        qt_license = '-opensource'

    # Bootstrap configure.exe on Windows so that we can re-use the UNIX source
    # tarball which doesn't have configure.exe pre-built like the Win32
    # version. To do this, we 'touch' qtbase\.gitignore.
    if is_qt5():
        with open(os.path.join('qtbase', '.gitignore'), 'w'):
            pass

    # Configure
    qt_configure_args = [
        '-confirm-license',
        '-prefix', layout['root'],
        '-shared',
        qt_license
    ]

    # Load build profile
    qt_configure_args.extend(profile['qt']['common'])

    if sys.platform in profile['qt']:
        qt_configure_args.extend(profile['qt'][sys.platform])

    # Enable proper release + debug .pdb files on Windows
    if debug:
        if sys.platform == 'win32':
            mkspec_file_name = 'qt%s-msvc2008-release-with-debuginfo.conf' % profile[
                'qt']['version']

            shutil.copyfile(os.path.join(SUPPORT_DIR, mkspec_file_name), os.path.join(
                'mkspecs', 'win32-msvc2008', 'qmake.conf'))
            qt_configure_args.append('-release')
        else:
            qt_configure_args.append('-debug')
    else:
        qt_configure_args.append('-release')

    # Have the compiler find our local copy of ICU
    if sys.platform == 'darwin' or sys.platform == 'win32':
        qt_configure_args.extend(['-I', os.path.join(layout['root'], 'include')])
        qt_configure_args.extend(['-L', os.path.join(layout['root'], 'lib')])

    if sys.platform == 'win32':
        # VC++ doesn't have stdint.h (required by WebKit)
        shutil.copy(os.path.join(SUPPORT_DIR, 'stdint-msvc.h'),
                    os.path.join(layout['include'], 'stdint.h'))

        # Add gnuwin32 to the PATH (required by WebKit)
        qt_source_dir = os.path.abspath(os.getcwd())
        os.environ['PATH'] = os.pathsep.join([
            os.path.join(qt_source_dir, 'gnuwin32', 'bin'),
            os.environ['PATH']
        ])

        # Enable parallel build
        qt_configure_args.append('-mp')

    # Build Qt 4 with clang on OS X
    has_clang = sys.platform == 'darwin' \
        and os.path.isfile('/usr/bin/clang') \
        and os.path.isfile('/usr/bin/clang++')
    if has_clang and not is_qt5():
        qt_configure_args.extend(['-platform', 'unsupported/macx-clang'])

    # Build
    configure_qt(*qt_configure_args)
    qtmake()
    qtmake('install')

    # Delete all libtool's .la files
    for root, _, filenames in os.walk(layout['root']):
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
        shutil.copyfile(PYQT_LICENSE_FILE, os.path.join('sip', 'pyqt-commercial.sip'))

    # Configure-ng
    configure_ng_args = [
        '--assume-shared',
        '--bindir', layout['bin'],
        '--concatenate',
        '--concatenate-split=4',
        '--confirm-license',
        '--destdir', layout['python'],
        '--no-designer-plugin',
        '--no-docstrings',
        '--no-sip-files',
        '--sip', os.path.join(layout['bin'], 'sip'+EXECUTABLE_EXT),
        '--sipdir', layout['sip'],
        '--verbose',
    ]
    if 'pyqt' in profile and 'common' in profile['pyqt']:
        configure_ng_args += profile['pyqt']['common']

    set_pyqt_debug_flags(debug, configure_ng_args)

    # Build
    configure_ng(*configure_ng_args)
    make()
    make('install')

#
# Utility methods
#


def is_qt5():
    return os.path.isdir('qtbase')


def configure(*args):
    sdk.sh(sys.executable, 'configure.py', *args)


def configure_ng(*args):
    sdk.sh(sys.executable, 'configure-ng.py', *args)


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
