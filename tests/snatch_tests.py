# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
#
# This file is part of SickGear.
#
# SickGear is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickGear is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickGear.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
# import random
import unittest

import test_lib as test

# import sys, os.path

import sickgear.search as search
import sickgear
from sickgear.tv import TVEpisode, TVShow
import sickgear.common as c

tests = {'Dexter': {'a': 1, 'q': c.HD, 's': 5, 'e': [7], 'b': 'Dexter.S05E07.720p.BluRay.X264-REWARD', 'i': ['Dexter.S05E07.720p.BluRay.X264-REWARD', 'Dexter.S05E07.720p.X264-REWARD']},
         'House': {'a': 1, 'q': c.HD, 's': 4, 'e': [5], 'b': 'House.4x5.720p.BluRay.X264-REWARD', 'i': ['Dexter.S05E04.720p.X264-REWARD', 'House.4x5.720p.BluRay.X264-REWARD']},
         'Hells Kitchen': {'a': 1, 'q': c.SD, 's': 6, 'e': [14, 15], 'b': 'Hells.Kitchen.s6e14e15.HDTV.XviD-ASAP', 'i': ['Hells.Kitchen.S06E14.HDTV.XviD-ASAP', 'Hells.Kitchen.6x14.HDTV.XviD-ASAP', 'Hells.Kitchen.s6e14e15.HDTV.XviD-ASAP']}
       }


def _create_fake_xml(items):
    xml = '<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:newznab="http://www.newznab.com/DTD/2010/feeds/attributes/" encoding="utf-8"><channel>'
    for item in items:
        xml += '<item><title>' + item + '</title>\n'
        xml += '<link>http://fantasy.com/' + item + '</link></item>'
    xml += '</channel></rss>'
    return xml


searchItems = []


class SearchTest(test.SickbeardTestDBCase):

    def _fake_getURL(self, url, headers=None):
        global searchItems
        return _create_fake_xml(searchItems)

    def _fake_isActive(self):
        return True

    def __init__(self, something):
        for provider in sickgear.providers.sortedProviderList():
            provider.get_url = self._fake_getURL
            #provider.isActive = self._fake_isActive

        super(SearchTest, self).__init__(something)


def test_generator(tvdbdid, show_name, curData, forceSearch):

    def test(self):
        global searchItems
        searchItems = curData['i']
        show_obj = TVShow(1, tvdbdid)
        show_obj.name = show_name
        show_obj.quality = curData['q']
        show_obj.save_to_db()
        sickgear.showList.append(show_obj)
        sickgear.showDict[show_obj.sid_int] = show_obj
        episode = None

        for epNumber in curData['e']:
            episode = TVEpisode(show_obj, curData['s'], epNumber)
            episode.status = c.WANTED
            episode.save_to_db()

        bestResult = search.search_providers(show_obj, episode.season, episode.episode, forceSearch)
        if not bestResult:
            self.assertEqual(curData['b'], bestResult)
        self.assertEqual(curData['b'], bestResult.name) #first is expected, second is chosen one
    return test


if '__main__' == __name__:
    print('==================')
    print('STARTING - Snatch TESTS')
    print('==================')
    print('######################################################################')
    # create the test methods
    tvdbdid = 1
    for forceSearch in (True, False):
        for name, curData in tests.items():
            if not curData['a']:
                continue
            fname = name.replace(' ', '_')
            if forceSearch:
                test_name = 'test_manual_%s_%s' % (fname, tvdbdid)
            else:
                test_name = 'test_%s_%s' % (fname, tvdbdid)

            test = test_generator(tvdbdid, name, curData, forceSearch)
            setattr(SearchTest, test_name, test)
            tvdbdid += 1

    suite = unittest.TestLoader().loadTestsFromTestCase(SearchTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
