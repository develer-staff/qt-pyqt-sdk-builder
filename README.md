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

| Qt, SIP, PyQt versions            | OS X 10.9 | Ubuntu 12.04 | Windows 7 |
|-----------------------------------|-----------|--------------|-----------|
| Qt 4.8.6, SIP 4.16.2, PyQt 4.11.1 | 64-bit    | 64-bit       | 32-bit    |
| Qt 5.3.1, SIP 4.16.2, PyQt 5.3.1  | 64-bit    | 64-bit       | 32-bit    |


### Compilers

|          | GCC | Clang | Visual Studio | MinGW |
|----------|-----|-------|---------------|-------|
| Linux    | Yes | No    | -             | -     |
| OS X     | No  | Yes   | -             | -     |
| Windows  | -   | -     | Yes (2008)    | No    |


## Usage

WIP.


## Limitations

Only dynamically linked versions of Qt and PyQt are currently supported.
