# Author: Jasper Lanting
# Based on nmj.py by Nico Berlee: http://nico.berlee.nl/
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

import time
from xml.dom.minidom import parseString

from .generic import BaseNotifier
import sickgear
from exceptions_helper import ex

from _23 import etree, urlencode
# noinspection PyUnresolvedReferences
from six.moves import urllib


class NMJv2Notifier(BaseNotifier):

    def notify_settings(self, host, db_loc, instance):
        """
        Retrieves the NMJv2 database location from Popcorn hour

        host: The hostname/IP of the Popcorn Hour server
        dbloc: 'local' for PCH internal harddrive. 'network' for PCH network shares
        instance: Allows for selection of different DB in case of multiple databases

        Returns: True if the settings were retrieved successfully, False otherwise
        """
        result = False
        try:
            base_url = 'http://%s:8008/' % host

            req = urllib.request.Request('%s%s%s' % (base_url, 'file_operation?', urlencode(
                dict(arg0='list_user_storage_file', arg1='', arg2=instance, arg3=20, arg4='true', arg5='true',
                     arg6='true', arg7='all', arg8='name_asc', arg9='false', arg10='false'))))
            http_response_obj = urllib.request.urlopen(req)  # PY2 http_response_obj has no `with` context manager
            response = http_response_obj.read()
            http_response_obj.close()
            xml_data = parseString(response)

            time.sleep(300.0 / 1000.0)
            for node in xml_data.getElementsByTagName('path'):
                xml_tag = node.toxml()

                reqdb = urllib.request.Request('%s%s%s' % (base_url, 'metadata_database?', urlencode(
                    dict(arg0='check_database',
                         arg1=xml_tag.replace('<path>', '').replace('</path>', '').replace('[=]', '')))))
                http_response_obj_db = urllib.request.urlopen(reqdb)  # PY2 http_response_obj has no `with` context mgr
                responsedb = http_response_obj_db.read()
                http_response_obj.close()
                xml_db = parseString(responsedb)

                if '0' == xml_db.getElementsByTagName('returnValue')[0].toxml().replace(
                        '<returnValue>', '').replace('</returnValue>', ''):
                    db_path = xml_db.getElementsByTagName('database_path')[0].toxml().replace(
                        '<database_path>', '').replace('</database_path>', '').replace('[=]', '')
                    if 'local' == db_loc and db_path.find('localhost') > -1:
                        sickgear.NMJv2_HOST = host
                        sickgear.NMJv2_DATABASE = db_path
                        result = True
                    if 'network' == db_loc and db_path.find('://') > -1:
                        sickgear.NMJv2_HOST = host
                        sickgear.NMJv2_DATABASE = db_path
                        result = True

        except IOError as e:
            self._log_warning(u'Couldn\'t contact popcorn hour on host %s: %s' % (host, ex(e)))

        if result:
            return '{"message": "Success, NMJ Database found at: %(host)s", "database": "%(database)s"}' % {
                "host": host, "database": sickgear.NMJv2_DATABASE}

        return '{"message": "Failed to find NMJ Database at location: %(dbloc)s. ' \
               'Is the right location selected and PCH running? ", "database": ""}' % {"dbloc": db_loc}

    def _send(self, host=None):
        """
        Sends a NMJ update command to the specified machine

        host: The hostname/IP to send the request to (no port)
        database: The database to send the request to
        mount: The mount URL to use (optional)

        Returns: True if the request succeeded, False otherwise
        """

        host = self._choose(host, sickgear.NMJv2_HOST)

        self._log_debug(u'Sending scan command for NMJ ')

        # if a host is provided then attempt to open a handle to that URL
        try:
            base_url = 'http://%s:8008/' % host

            url_scandir = '%s%s%s' % (base_url, 'metadata_database?', urlencode(
                dict(arg0='update_scandir', arg1=sickgear.NMJv2_DATABASE, arg2='', arg3='update_all')))
            self._log_debug(u'Scan update command sent to host: %s' % host)

            url_updatedb = '%s%s%s' % (base_url, 'metadata_database?', urlencode(
                dict(arg0='scanner_start', arg1=sickgear.NMJv2_DATABASE, arg2='background', arg3='')))
            self._log_debug(u'Try to mount network drive via url: %s' % host)

            prereq = urllib.request.Request(url_scandir)
            req = urllib.request.Request(url_updatedb)

            http_response_obj1 = urllib.request.urlopen(prereq)  # PY2 http_response_obj has no `with` context manager
            response1 = http_response_obj1.read()
            http_response_obj1.close()

            time.sleep(300.0 / 1000.0)

            http_response_obj2 = urllib.request.urlopen(req)  # PY2 http_response_obj has no `with` context manager
            response2 = http_response_obj2.read()
            http_response_obj2.close()
        except IOError as e:
            self._log_warning(u'Couldn\'t contact popcorn hour on host %s: %s' % (host, ex(e)))
            return False

        try:
            et = etree.fromstring(response1)
            result1 = et.findtext('returnValue')
        except SyntaxError as e:
            self._log_error(u'Unable to parse XML returned from the Popcorn Hour: update_scandir, %s' % ex(e))
            return False

        try:
            et = etree.fromstring(response2)
            result2 = et.findtext('returnValue')
        except SyntaxError as e:
            self._log_error(u'Unable to parse XML returned from the Popcorn Hour: scanner_start, %s' % ex(e))
            return False

        # if the result was a number then consider that an error
        error_codes = ['8', '11', '22', '49', '50', '51', '60']
        error_messages = ['Invalid parameter(s)/argument(s)',
                          'Invalid database path',
                          'Insufficient size',
                          'Database write error',
                          'Database read error',
                          'Open fifo pipe failed',
                          'Read only file system']
        if 0 < int(result1):
            index = error_codes.index(result1)
            self._log_error(u'Popcorn Hour returned an error: %s' % (error_messages[index]))
            return False

        elif 0 < int(result2):
            index = error_codes.index(result2)
            self._log_error(u'Popcorn Hour returned an error: %s' % (error_messages[index]))
            return False

        self._log(u'NMJv2 started background scan')
        return True

    def _notify(self, host=None, **kwargs):

        result = self._send(host)

        return self._choose((('Success, started %s', 'Failed to start %s')[not result] % 'the scan update at "%s"'
                             % host), result)

    def test_notify(self, host):
        self._testing = True
        return self._notify(host)

    # notify_snatch() Not implemented: Start the scanner when snatched does not make sense
    # notify_git_update() Not implemented, no reason to start scanner

    def notify_download(self, *args, **kwargs):
        self._notify()

    def notify_subtitle_download(self, *args, **kwargs):
        self._notify()


notifier = NMJv2Notifier
