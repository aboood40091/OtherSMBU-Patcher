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
import shutil
import struct
import sys

if platform.system() not in ['Windows', 'Linux', 'Darwin']:
    raise NotImplementedError("Unsupported platform!")

import globals

try:
    import pyximport
    pyximport.install()

    import cython_available

except:
    pass

else:
    del cython_available
    globals.cython_available = True

from bflim import writeFLIM
from level import Level
import SARC as SarcLib
from xmltodict import XmlToDict

if globals.cython_available:
    from yaz0 import compressLIBYAZ0 as CompYaz0
    from yaz0 import decompressLIBYAZ0 as DecompYaz0

else:
    from yaz0 import compressWSZST as CompYaz0
    from yaz0 import decompressWSZST as DecompYaz0


def createPatchFolder():
    """
    Create the Patch folder
    """
    try:
        os.mkdir(globals.patchpath)

    except FileExistsError:
        clear = input("\"Patch\" folder was found and has to be deleted, do you want to continue? (Y/N):\t").lower()
        if clear == 'y':
            shutil.rmtree(globals.patchpath)
            os.mkdir(globals.patchpath)

            print("\"Patch\" folder has successfully been removed and recreated!")

        else:
            sys.exit(1)

    else:
        print("\"Patch\" folder has successfully been created!")


def packLevels():
    """
    Pack all the levels in the Stage folder
    """
    if not os.path.isdir(os.path.join(globals.patchpath, 'content/Common/course_res_pack')):
        os.mkdir(os.path.join(globals.patchpath, 'content/Common/course_res_pack'))

    for f in os.listdir(os.path.join(globals.mod_path, 'Stage')):
        if os.path.isfile(os.path.join(globals.mod_path, 'Stage/' + f)):
            print('\nPacking: ' + f)

            level = Level(f)
            with open(os.path.join(globals.mod_path, 'Stage/' + f), "rb") as inf:
                level.load(inf.read())

            levelData = level.save()

            if not levelData:
                print('Something went wrong while packing %s!' % f)

            else:
                with open(os.path.join(globals.patchpath, 'content/Common/course_res_pack/' + f), "wb+") as out:
                    out.write(levelData)

            print('Compressing: ' + f)

            if not CompYaz0(
                    os.path.join(globals.patchpath, 'content/Common/course_res_pack/' + f),
                    os.path.join(globals.patchpath,
                                 'content/Common/course_res_pack/%s.szs' % ''.join(f.split('.sarc')[:-1])),
            ):
                print('Something went wrong while compressing %s!' % f)

            else:
                print('Packed: ' + f)

            os.remove(os.path.join(globals.patchpath, 'content/Common/course_res_pack/' + f))


def patchLayouts():
    """
    Patch all the layouts
    """
    if not os.path.isdir(os.path.join(globals.patchpath, 'content/Common/layout')):
        os.mkdir(os.path.join(globals.patchpath, 'content/Common/layout'))

    for layout in globals.Layouts:
        if os.path.isdir(os.path.join(globals.mod_path, 'Layouts/' + layout)):
            if not os.path.isfile(os.path.join(globals.mod_path, 'Layouts/%s/settings.xml' % layout)):
                continue

            sarcpadding = globals.Layouts[layout]
            settings = XmlToDict(os.path.join(globals.mod_path, 'Layouts/%s/settings.xml' % layout))

            if not settings:
                continue

            filesettings = []
            for setting in settings:
                if settings[setting]:
                    if setting == "SARCPadding":
                        sarcpadding = int(settings[setting], 0)

                    elif setting[:4] == "File":
                        filesettings.append(settings[setting])

            if not filesettings:
                continue

            files = {}
            for filesetting in filesettings:
                name = ""
                bflimname = ""
                tileMode = 4
                swizzle = 0
                SRGB = "False"

                for setting in filesetting:
                    if setting == "Name":
                        name = filesetting[setting]

                    elif setting == "BFLIMName":
                        bflimname = filesetting[setting]

                    elif filesetting[setting]:
                        if setting == "TileMode":
                            try:
                                tileMode = int(filesetting[setting], 0)

                            except ValueError:
                                tileMode = 4

                            else:
                                if tileMode > 16 or tileMode < 0:
                                    tileMode = 4

                        elif setting == "Swizzle":
                            try:
                                swizzle = int(filesetting[setting], 0)

                            except ValueError:
                                swizzle = 0

                            else:
                                if swizzle > 7 or swizzle < 0:
                                    swizzle = 0

                        elif setting == "SRGB":
                            SRGB = filesetting[setting]
                            if SRGB not in ["True", "False"]:
                                SRGB = "False"

                if not name:
                    continue

                elif not name.endswith(".dds"):
                    continue

                elif not os.path.isfile(os.path.join(globals.mod_path, 'Layouts/%s/%s' % (layout, name))):
                    continue

                if not bflimname:
                    bflimname = name[:-3] + "bflim"

                data = writeFLIM(
                    os.path.join(globals.mod_path, 'Layouts/%s/%s' % (layout, name)),
                    tileMode, swizzle,
                    SRGB == "True",
                )

                if not data:
                    print("Something went wrong while converting %s to BFLIM!" % name)
                    continue

                files[name] = {
                    "BFLIMName": bflimname,
                    "Data": data,
                }

            if not files:
                continue

            print("\nPatching: %s.szs\n" % layout)

            with open(os.path.join(globals.gamepath, 'Common/layout/%s.szs' % layout), 'rb') as inf:
                inb = inf.read()

            arc = SarcLib.SARC_Archive(DecompYaz0(inb))
            for name in files:
                bflimname = files[name]["BFLIMName"]
                data = files[name]["Data"]

                fileAdded = False
                for folder in arc.contents:
                    if isinstance(folder, SarcLib.Folder) and folder.name == "lyt_root":
                        for lytFolder in folder.contents:
                            if isinstance(lytFolder, SarcLib.Folder) and lytFolder.name == "timg":
                                for file in lytFolder.contents:
                                    if isinstance(file, SarcLib.File) and file.name == bflimname:
                                        lytFolder.removeFile(file)
                                        break

                                file = SarcLib.File()
                                file.name = bflimname
                                file.data = data

                                lytFolder.addFile(file)
                                fileAdded = True

                            if fileAdded:
                                break

                    if fileAdded:
                        break

                if fileAdded:
                    print("Added: %s" % bflimname)

                else:
                    print("Something went wrong while adding %s!" % bflimname)

            with open(os.path.join(globals.patchpath, 'content/Common/layout/%s.sarc' % layout), "wb+") as out:
                out.write(arc.save(sarcpadding))

            print('\nCompressing: %s.szs' % layout)

            if not CompYaz0(
                    os.path.join(globals.patchpath, 'content/Common/layout/%s.sarc' % layout),
                    os.path.join(globals.patchpath, 'content/Common/layout/%s.szs' % layout),
            ):
                print('Something went wrong while compressing %s.szs!' % f)

            else:
                print('Patched: %s.szs' % layout)

            os.remove(os.path.join(globals.patchpath, 'content/Common/layout/%s.sarc' % layout))


def patchBFSAR():
    """
    Patch the Sound Archive
    """
    if not os.path.isdir(os.path.join(globals.patchpath, 'content/CAFE/sound')):
        os.mkdir(os.path.join(globals.patchpath, 'content/CAFE/sound'))

    fsar = os.path.join(globals.gamepath, 'CAFE/sound/cafe_redpro_sound.bfsar')

    if not os.path.isfile(fsar):
        print("\n\"cafe_redpro_sound.bfsar\" not found!")
        print("Skipping patching the Sound Archive...")
        return

    tracks = {}
    for track in globals.Tracks:
        if not os.path.isfile(os.path.join(globals.mod_path, 'Sound/%s.bfwav' % track)):
            continue

        with open(os.path.join(globals.mod_path, 'Sound/%s.bfwav' % track), "rb") as inf:
            data = inf.read()

        if data[:4] != b'FWAV':
            continue

        pos, size = globals.Tracks[track]

        if data[4:6] == b'\xFE\xFF':
            endianness = ">"

        elif data[4:6] == b'\xFF\xFE':
            endianness = "<"

        else:
            print("Invalid endianness in \"%s.bfwav\"!" % track)
            continue

        size2 = len(data)
        size3 = struct.unpack(endianness + "I", data[12:16])[0]

        if size2 > size or size3 > size:
            print("Size of \"%s.bfwav\" exceeds the original!" % track)
            continue

        tracks[track] = (data, pos, size2)

    if tracks:
        with open(fsar, "rb") as inf:
            fsarData = inf.read()

        if fsarData[:4] != b'FSAR':
            print("Invalid Sound Archive!")
            print("Skipping patching the Sound Archive...")
            return

        for track in tracks:
            fwavData, pos, size = tracks[track]

            print("Injecting: " + track)

            if not isinstance(fsarData, bytearray):
                fsarData = bytearray(fsarData)

            fsarData[pos:pos + size] = fwavData

        with open(os.path.join(globals.patchpath, 'content/CAFE/sound/cafe_redpro_sound.bfsar'), "wb+") as outf:
            outf.write(fsarData)


def copytree(src, dst):
    # https://stackoverflow.com/a/13814557
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)

        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def getTree_(src, src2):
    dir2 = os.path.join(src, src2)
    for dir_ in os.listdir(dir2):
        dir = os.path.join(src2, dir_)
        dir2 = os.path.join(src, dir)
        if os.path.isdir(dir2):
            globals.Tree.append(dir)
            getTree_(src, dir)


def getTree(src):
    for dir_ in os.listdir(src):
        dir = os.path.join(src, dir_)
        if os.path.isdir(dir):
            globals.Tree.append(dir_)
            getTree_(src, dir_)


def copyOtherFiles():
    globals.Tree = []

    getTree(os.path.join(globals.curr_path, 'Files/Other'))
    for dir_ in globals.Tree:
        dir = os.path.join(globals.patchpath, dir_)
        if not os.path.exists(dir):
            os.mkdir(dir)

    copytree(os.path.join(globals.curr_path, 'Files/Other'), globals.patchpath)


def main():
    print("OtherSMBU Patcher v0.1\n(C) 2018 - AboodXD\n")

    globals.gamepath = input("Enter the path to the content folder of NSMBU:\t")
    globals.mod_path = os.path.join(globals.curr_path, 'Files')
    globals.patchpath = os.path.join(globals.curr_path, 'Patch')

    if not globals.gamepath:
        sys.exit(1)

    if not os.path.isdir(globals.gamepath):
        sys.exit(1)

    # Step 1: Create the Patch folder
    print("\nCreating \"Patch\" folder...")
    createPatchFolder()

    # Step 1.5: Create necessary folders
    os.mkdir(os.path.join(globals.patchpath, 'content'))
    os.mkdir(os.path.join(globals.patchpath, 'content/Common'))
    os.mkdir(os.path.join(globals.patchpath, 'content/CAFE'))

    # Step 2: Pack the levels
    print('\nPacking the levels...')
    packLevels()

    # Step 3: Patch the layouts
    print('\nPatching the layouts...')
    patchLayouts()

    # Step 4: Patch the Sound Archive
    print('\nPatching the Sound Archive...\n')
    patchBFSAR()

    # Step 5: Copy the other files
    print('\nCopying the other files...\n')
    copyOtherFiles()


if __name__ == '__main__':
    main()
