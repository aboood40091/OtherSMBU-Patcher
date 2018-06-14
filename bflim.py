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

import struct

import addrlib
import dds

formats = {
    0x00000000: 'GX2_SURFACE_FORMAT_INVALID',
    0x0000001a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM',
    0x0000041a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB',
    0x00000019: 'GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM',
    0x00000008: 'GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM',
    0x0000000a: 'GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM',
    0x0000000b: 'GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM',
    0x00000001: 'GX2_SURFACE_FORMAT_TC_R8_UNORM',
    0x00000007: 'GX2_SURFACE_FORMAT_TC_R8_G8_UNORM',
    0x00000002: 'GX2_SURFACE_FORMAT_TC_R4_G4_UNORM',
    0x00000031: 'GX2_SURFACE_FORMAT_T_BC1_UNORM',
    0x00000431: 'GX2_SURFACE_FORMAT_T_BC1_SRGB',
    0x00000032: 'GX2_SURFACE_FORMAT_T_BC2_UNORM',
    0x00000432: 'GX2_SURFACE_FORMAT_T_BC2_SRGB',
    0x00000033: 'GX2_SURFACE_FORMAT_T_BC3_UNORM',
    0x00000433: 'GX2_SURFACE_FORMAT_T_BC3_SRGB',
    0x00000034: 'GX2_SURFACE_FORMAT_T_BC4_UNORM',
    0x00000035: 'GX2_SURFACE_FORMAT_T_BC5_UNORM',
}


class FLIMHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s2H2IH2x')


class imagHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4sI3H2BI')


def computeSwizzleTileMode(z):
    z = ''.join([bin(z[0])[2:].zfill(3), bin(z[1])[2:].zfill(5)])
    return int(z, 2)


def warn_color(f):
    print("\nWarning: in file \"%s\", colors might mess up!!" % f)


def writeFLIM(f, tileMode, swizzle_, SRGB):
    # Read the DDS file
    width, height, format__, fourcc, dataSize, compSel, numMips, data = dds.readDDS(f, SRGB)

    # Check if it was read correctly
    if 0 in [width, dataSize] and data == []:
        return b''

    # Check if the texture format is supported
    if format__ not in formats:
        return b''

    # Remove the mipmap data if it exists
    data = data[:dataSize]

    # GTX format -> BFLIM format

    # GTX format: 1
    # if alpha: BFLIM format: 0
    # else: BFLIM format: 1
    if format__ == 1:
        if compSel[3] == 0:
            format_ = 1

        else:
            format_ = 0

    # GTX format: 0x1a
    # if one value is 0: BFLIM format: 6 (BAD CHOICE)
    # else: BFLIM format: 9
    elif format__ == 0x1a:
        if 5 in compSel:
            format_ = 6

        else:
            format_ = 9

    # GTX format: 0x31
    # if ETC1: BFLIM format: 0xa
    # else: BFLIM format: 0xc
    elif format__ == 0x31:
        if fourcc == b'ETC1':
            format_ = 0xa

        else:
            format_ = 0xc

    # GTX format: (key) -> BFLIM format: (value)
    else:
        fmt = {
            7: 3,
            8: 5,
            0xa: 7,
            0xb: 8,
            0x32: 0xd,
            0x33: 0xe,
            0x34: 0x10,
            0x35: 0x11,
            0x41a: 0x14,
            0x431: 0x15,
            0x432: 0x16,
            0x433: 0x17,
            0x19: 0x18,
        }

        format_ = fmt[format__]

    # Check if colors are messed up or if R and B are swapped
    if format_ == 0:
        if compSel not in [[0, 0, 0, 5], [0, 5, 5, 5]]:
            warn_color(f)

    elif format_ == 1:
        if compSel != [5, 5, 5, 0]:
            warn_color(f)

    elif format_ in [2, 3]:
        if compSel not in [[0, 0, 0, 1], [0, 5, 5, 1]]:
            warn_color(f)

    elif format_ == 5:
        if compSel != [2, 1, 0, 5]:
            if compSel == [0, 1, 2, 5]:
                # Swap R and B
                data = dds.form_conv.swapRB_16bpp(data, 'rgb565')

            else:
                warn_color(f)

    elif format_ == 6:
        if compSel != [0, 1, 2, 5]:
            if compSel == [2, 1, 0, 5]:
                # Swap R and B
                data = dds.form_conv.swapRB_32bpp(data, 'rgba8')

            else:
                warn_color(f)

    elif format_ == 7:
        if compSel != [0, 1, 2, 3]:
            if compSel == [2, 1, 0, 3]:
                # Swap R and B
                data = dds.form_conv.swapRB_16bpp(data, 'rgb5a1')

            else:
                warn_color(f)

    elif format_ == 8:
        if compSel != [2, 1, 0, 3]:
            if compSel == [0, 1, 2, 3]:
                # Swap R and B
                data = dds.form_conv.swapRB_16bpp(data, 'argb4')

            else:
                warn_color(f)

    elif format_ in [9, 0x14, 0x18]:
        if compSel != [0, 1, 2, 3]:
            if compSel == [2, 1, 0, 3]:
                if format_ == 0x18:
                    # Swap R and B
                    data = dds.form_conv.swapRB_32bpp(data, 'bgr10a2')

                else:
                    # Swap R and B
                    data = dds.form_conv.swapRB_32bpp(data, 'rgba8')

            else:
                warn_color(f)

    # Get the Surface Info
    surfOut = addrlib.getSurfaceInfo(format__, width, height, 1, 1, tileMode, 0, 0)

    # Depths other than 1 are not supported
    if surfOut.depth != 1:
        return b''

    # Pad the data
    padSize = surfOut.surfSize - len(data)
    data += padSize * b"\x00"

    # Pack the swizzle value and tileMode
    z = (swizzle_, tileMode)
    swizzle_tileMode = computeSwizzleTileMode(z)

    # Get the swizzle value used for (de)swizzling
    if tileMode in [1, 2, 3, 16]:
        s = swizzle_ << 8

    else:
        s = 0xd0000 | (swizzle_ << 8)

    # Swizzle the data
    swizzled_data = addrlib.swizzle(width, height, surfOut.height, format__, surfOut.tileMode, s,
                                    surfOut.pitch, surfOut.bpp, data)

    # Get the alignment value
    alignment = 512 * (surfOut.bpp >> 3)

    # Pack the file header
    head_struct = FLIMHeader()
    head = head_struct.pack(b"FLIM", 0xFEFF, 0x14, 0x2020000, len(swizzled_data) + 0x28, 1)

    # Pack the `imag` header
    img_head_struct = imagHeader()
    imag_head = img_head_struct.pack(b"imag", 16, width, height, alignment, format_, swizzle_tileMode,
                                     len(swizzled_data))

    # Build the file
    output = b"".join([swizzled_data, head, imag_head])

    return output
