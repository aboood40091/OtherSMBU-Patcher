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

# Code from:
# http://code.activestate.com/recipes/410469-xml-as-dictionary/

################################################################
################################################################

from xml.etree import cElementTree as ElementTree


def XmlToDict(xml):
    # https://stackoverflow.com/a/5807028
    tree = ElementTree.parse(xml)
    root = tree.getroot()

    return XmlDictConfig(root)


class XmlListConfig(list):
    def __init__(self, aList):
        super().__init__()

        for element in aList:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))

                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))

            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDictConfig(dict):
    def __init__(self, parent_element):
        super().__init__()

        if parent_element.items():
            self.update(dict(parent_element.items()))

        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)

                else:
                    aDict = {element[0].tag: XmlListConfig(element)}

                if element.items():
                    aDict.update(dict(element.items()))

                self.update({element.tag: aDict})

            elif element.items():
                self.update({element.tag: dict(element.items())})

            else:
                self.update({element.tag: element.text})
