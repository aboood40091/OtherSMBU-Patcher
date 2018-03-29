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

from os import listdir
import os.path
import struct
from xml.etree import ElementTree as etree

from bytes import bytes_to_string
import globals
import SARC as SarcLib
from yaz0 import decompressLIBYAZ0 as DecompYaz0


class Area:
    def __init__(self):
        self.blocks = [None] * 15
        self.block1pos = 0

        self.areanum = 1

        self.course = None
        self.L0 = None
        self.L1 = None
        self.L2 = None

        self.blocks = [b''] * 15

        self.tileset0 = ''
        self.tileset1 = ''
        self.tileset2 = ''
        self.tileset3 = ''

        self.sprites = []

    def load(self, course, L0, L1, L2):
        self.course = course
        self.L0 = L0
        self.L1 = L1
        self.L2 = L2
        self.LoadBlocks(course)
        self.LoadTilesetNames()
        self.LoadSprites()

    def LoadBlocks(self, course):
        self.blocks = [b''] * 15
        getblock = struct.Struct('>II')

        for i in range(15):
            data = getblock.unpack_from(course, i * 8)

            if data[1] == 0:
                self.blocks[i] = b''
            else:
                self.blocks[i] = course[data[0]:data[0] + data[1]]

        self.block1pos = getblock.unpack_from(course, 0)

    def LoadTilesetNames(self):
        data = struct.unpack_from('32s32s32s32s', self.blocks[0])
        self.tileset0 = bytes_to_string(data[0])
        self.tileset1 = bytes_to_string(data[1])
        self.tileset2 = bytes_to_string(data[2])
        self.tileset3 = bytes_to_string(data[3])

    def LoadSprites(self):
        spritedata = self.blocks[7]
        sprcount = len(spritedata) // 24
        sprstruct = struct.Struct('>HHH10sxx2sxxxx')
        offset = 0
        sprites = []

        unpack = sprstruct.unpack_from
        append = sprites.append
        for i in range(sprcount):
            data = unpack(spritedata, offset)
            append(data[0])
            offset += 24

        self.sprites = sprites


class Level:
    def __init__(self, name):
        self.name = ''.join(name.split('.sarc')[:-1])
        self.areas = []
        self.szsData = {}

    def load(self, data):
        self.szsData[self.name] = data
        self.szsData['levelname'] = self.name.encode('utf-8')

        arc = SarcLib.SARC_Archive()
        arc.load(data)

        try:
            courseFolder = arc['course']

        except:
            return False

        areaData = {}
        for file in courseFolder.contents:
            name, val = file.name, file.data

            if val is None:
                continue

            if not name.startswith('course'):
                continue

            if not name.endswith('.bin'):
                continue

            if '_bgdatL' in name:
                # It's a layer file
                if len(name) != 19:
                    continue

                try:
                    thisArea = int(name[6])
                    laynum = int(name[14])

                except ValueError:
                    continue

                if not (0 < thisArea < 5):
                    continue

                if thisArea not in areaData:
                    areaData[thisArea] = [None] * 4

                areaData[thisArea][laynum + 1] = val

            else:
                # It's the course file
                if len(name) != 11:
                    continue

                try:
                    thisArea = int(name[6])

                except ValueError:
                    continue

                if not (0 < thisArea < 5):
                    continue

                if thisArea not in areaData:
                    areaData[thisArea] = [None] * 4

                areaData[thisArea][0] = val

        # Create area objects
        self.areas = []
        thisArea = 1
        while thisArea in areaData:
            course = areaData[thisArea][0]
            L0 = areaData[thisArea][1]
            L1 = areaData[thisArea][2]
            L2 = areaData[thisArea][3]

            newarea = Area()
            newarea.areanum = thisArea
            newarea.load(course, L0, L1, L2)
            self.areas.append(newarea)

            thisArea += 1

        return True

    def addSpriteFiles(self):
        # Read the sprites resources xml
        tree = etree.parse(os.path.join(globals.curr_path, 'spriteresources.xml'))
        root = tree.getroot()

        # Get all sprites' filenames and add them to a tuple
        sprites_xml = {}
        for sprite in root.iter('sprite'):
            id = int(sprite.get('id'))

            name = []
            for id2 in sprite:
                name.append(id2.get('name'))

            sprites_xml[id] = tuple(name)

        # Look up every sprite used in each area
        sprites_SARC = []
        for area_SARC in self.areas:
            for sprite in area_SARC.sprites:
                sprites_SARC.append(sprite)

        sprites_SARC = tuple(set(sprites_SARC))

        # Sort the filenames for each "used" sprite
        sprites_names = []
        for sprite in sprites_SARC:
            for sprite_name in sprites_xml[sprite]:
                sprites_names.append(sprite_name)

        sprites_names = tuple(set(sprites_names))

        # Look up each needed file and add it to our archive
        for sprite_name in sprites_names:
            if sprite_name not in self.szsData:
                # Get it if it has been cached
                if sprite_name in globals.SpriteCache:
                    self.szsData[sprite_name] = globals.SpriteCache[sprite_name]

                # Get it from the actor folder from the game files
                elif os.path.isfile(os.path.join(globals.gamepath, 'Common/actor/%s.szs' % sprite_name)):
                    with open(os.path.join(globals.gamepath, 'Common/actor/%s.szs' % sprite_name), 'rb') as inf:
                        inb = inf.read()

                    data = DecompYaz0(inb)
                    self.szsData[sprite_name] = data
                    globals.SpriteCache[sprite_name] = data

                    del inb
                    del data

                # Throw a warning because the file was not found...
                else:
                    print("WARNING: Could not find the file: %s" % sprite_name)
                    print("Expect the level to crash ingame...")

    def save(self):
        arc = SarcLib.SARC_Archive()

        if os.path.isdir(os.path.join(globals.mod_path, 'Sprites/' + self.name)):
            for f in listdir(os.path.join(globals.mod_path, 'Sprites/' + self.name)):
                if os.path.isfile(os.path.join(globals.mod_path, 'Sprites/%s/%s' % (self.name, f))):
                    with open(os.path.join(globals.mod_path, 'Sprites/%s/%s' % (self.name, f)), "rb") as inf:
                        self.szsData[f] = inf.read()

        self.addSpriteFiles()

        # Look up every tileset used in each area
        tilesets_names = []
        for area_SARC in self.areas:
            if area_SARC.tileset0 not in ('', None):
                tilesets_names.append(area_SARC.tileset0)

            if area_SARC.tileset1 not in ('', None):
                tilesets_names.append(area_SARC.tileset1)

            if area_SARC.tileset2 not in ('', None):
                tilesets_names.append(area_SARC.tileset2)

            if area_SARC.tileset3 not in ('', None):
                tilesets_names.append(area_SARC.tileset3)

        tilesets_names = tuple(set(tilesets_names))

        # Add each tileset to our archive
        for tileset_name in tilesets_names:
            if os.path.isfile(os.path.join(globals.mod_path, 'Stage/Texture/%s.sarc' % tileset_name)):
                with open(os.path.join(globals.mod_path, 'Stage/Texture/%s.sarc' % tileset_name), "rb") as inf:
                    self.szsData[tileset_name] = inf.read()

            else:
                print("Tileset %s not found!" % tileset_name)

        for file in self.szsData:
            arc.addFile(SarcLib.File(file, self.szsData[file]))

        return arc.save(0x2000)
