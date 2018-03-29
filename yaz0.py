#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# OtherSMBU Patcher
# Version 0.1
# Copyright © 2018 AboodXD

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

################################################################
################################################################

import os
import platform
import subprocess

import globals
from libyaz0 import decompress, compress


def compressWSZST(inf, outf):
    """
    Compress the file using WSZST
    """
    if os.path.isfile(outf):
        os.remove(outf)

    if platform.system() == 'Windows':
        os.chdir(globals.curr_path + '/Tools')
        subprocess.call('wszst.exe COMPRESS "' + inf + '" --dest "' + outf + '"', creationflags=0x8)

    elif platform.system() == 'Linux':
        os.chdir(globals.curr_path + '/linuxTools')
        os.system('chmod +x ./wszst_linux.elf')
        os.system('./wszst_linux.elf COMPRESS "' + inf + '" --dest "' + outf + '"')

    else:
        os.chdir(globals.curr_path + '/macTools')
        os.system('"' + globals.curr_path + '/macTools/wszst_mac" COMPRESS "' + inf + '" --dest "' + outf + '"')

    os.chdir(globals.curr_path)

    if not os.path.isfile(outf):
        return False

    return True


def decompressWSZST(inb):
    """
    Deompress the data using WSZST
    """
    inf = os.path.join(globals.curr_path, 'tmp.tmp')
    outf = os.path.join(globals.curr_path, 'tmp2.tmp')

    with open(inf, "wb+") as out:
        out.write(inb)

    if os.path.isfile(outf):
        os.remove(outf)

    if platform.system() == 'Windows':
        os.chdir(globals.curr_path + '/Tools')
        subprocess.call('wszst.exe COMPRESS "' + inf + '" --dest "' + outf + '"', creationflags=0x8)

    elif platform.system() == 'Linux':
        os.chdir(globals.curr_path + '/linuxTools')
        os.system('chmod +x ./wszst_linux.elf')
        os.system('./wszst_linux.elf COMPRESS "' + inf + '" --dest "' + outf + '"')

    else:
        os.chdir(globals.curr_path + '/macTools')
        os.system('"' + globals.curr_path + '/macTools/wszst_mac" COMPRESS "' + inf + '" --dest "' + outf + '"')

    os.remove(inf)
    os.chdir(globals.curr_path)

    if not os.path.isfile(outf):
        return b''

    with open(outf, "rb") as inf_:
        data = inf_.read()

    os.remove(outf)

    return data


def compressLIBYAZ0(inf, outf, level=1):
    """
    Compress the file using libyaz0
    """
    with open(inf, "rb") as inf_:
        inb = inf_.read()

    try:
        data = compress(inb, 0, level)

        with open(outf, "wb+") as out:
            out.write(data)

    except:
        return False

    else:
        return True


def decompressLIBYAZ0(inb):
    """
    Decompress the file using libyaz0
    """
    try:
        data = decompress(inb)

    except:
        return False

    else:
        return data
