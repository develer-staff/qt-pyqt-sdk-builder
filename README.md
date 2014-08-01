# Qt + PyQt SDK Builder

This repository contains tools needed to quickly and painlessly build Qt and PyQt on multiple
platforms with different build profiles.

It contains a lot of hard-won lessons building and compiling Qt and PyQt on Linux, OS X and
Windows.

For example, debug builds on Windows are linked to the release MSVCRT but still add debug .pdb
files so that you don't have to recompile the whole world when debugging a PyQt application.




## Platform Support

Operating Systems:

- OS X 10.9 and later.
- Ubuntu 12.04 and later.
- Windows 7 and later.

Qt:

- Qt 4.8.6
- Qt 5.3.0

Python:

- Python 2.7

SIP/PyQt:

- PyQt 4.11.1
- PyQt 5.3.1
- sip 4.16.1

Compilers:

- On Linux: GCC 4.4
- On OS X: Clang Apple LLVM 5.1
- On Windows: Visual C++ 2008 Express





## Usage

WIP.




## Limitations

Only dynamically linked versions of Qt and PyQt are currently supported.
