#!/bin/sh
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

apt-get build-dep -y qt4-x11
apt-get install -y "libx11.*" "libxcb.*"
apt-get install -y bison \
    build-essential \
    flex \
    gperf \
    libasound2-dev \
    libbz2-dev \
    libcap-dev \
    libcups2-dev \
    libdbus-1-dev \
    libdrm-dev \
    libfontconfig1-dev \
    libgcrypt11-dev \
    libgl1-mesa-dev \
    libicu-dev \
    libnss3-dev \
    libnss3-dev \
    libpci-dev \
    libpulse-dev \
    libssl-dev \
    libudev-dev \
    libxcomposite-dev \
    libxcursor-dev \
    libxdamage-dev \
    libxi-dev \
    libxrandr-dev \
    libxtst-dev \
    python \
    python-dev \
    re2c \
    ruby

# Work-around a bug in PyQt5.
ln -sf /usr/include/python2.7 /usr/local/include/python2.7
