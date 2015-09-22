# Qt + PyQt SDK Builder

This repository contains tools needed to quickly and painlessly build Qt and PyQt on multiple
platforms with different build profiles.

It contains a lot of hard-won lessons building and compiling Qt and PyQt on Linux, OS X and
Windows.

For example, debug builds on Windows are linked to the release MSVCRT but still add debug .pdb
files so that you don't have to recompile the whole world when debugging a PyQt application.


## Platform Support Matrix

### Python

* Python 2.7.8


### Build Types

We usually build and test against the latest version of Qt 4, Qt 5, SIP and PyQt.

| Qt, SIP, PyQt versions            | OS X 10.10 | Ubuntu 12.04 | Windows 7 |
|-----------------------------------|------------|--------------|-----------|
| Qt 4.8.6, SIP 4.16.7, PyQt 4.11.1 | 64-bit     | 64-bit       | 32-bit    |
| Qt 5.4.1, SIP 4.16.7, PyQt 5.4.1  | 64-bit     | 64-bit       | 32-bit    |


### Compilers

|          | GCC | Clang | Visual Studio | MinGW |
|----------|-----|-------|---------------|-------|
| Linux    | Yes | No    | -             | -     |
| OS X     | No  | Yes   | -             | -     |
| Windows  | -   | -     | Yes (2008)\*    | No    |

\* Supported Versions are : Visual C++ and Visual C++ 2008 Express Editions. Visual Studio
C++ for Python is currently incompatible.


## Installing Dependencies

To setup your machine, run the appropriate setup script from the `script` directory. It will try to
install all dependencies needed to rebuild Qt on your platform.

### OS X

Make sure your user can install dependencies through [Homebrew](http://brew.sh), then:

    ./script/setup-osx.sh


### Ubuntu

    sudo ./script/setup-ubuntu.sh


### Windows

Launch `./script/setup-windows.cmd` as Administrator.


## Overview

This toolkit is composed of several moving parts:

* `build.py`: This script will re-compile ICU, Qt, SIP and PyQt to generate a redistributable SDK.
  By default this scripts creates a directory but a command line switch enables the creation of a
  gzipped tarball.
* `configure.py`: This script is distributed alongside the SDK. Users of the SDK will launch this
  script to relocate the SDK and setup all the necessary environment variables to use it.
* `sdk.py`: This file contains code in common between `build.py` and `configure.py`. It is therefore
  needed during the build process and is included alongside `configure.py` in the resulting SDK.


## Basic Usage

*This section presumes you have already launched `build.py --help` at least once.*

In order to build a complete SDK you have to tell `build.py`:

1. Where all the needed source code (ICU, Qt, SIP, PyQt) is located on disk. To accomplish this you
   can either specify the paths on the command line (see `build.py --help`) or create a `sources`
   directory and unpack the source tarballs there.
2. How to build Qt: what we call a *profile*. We have a couple of pre-made profiles in the
   `profiles` directory.

Then grab a cup of coffee and wait until `build.py` is done. If you are lucky, you will find
everything in the `_out` directory (you can control the output directory with a command line switch,
see `build.py --help` for more information).


## Limitations

Only dynamically linked versions of Qt and PyQt are currently supported.
