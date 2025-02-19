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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickGear. If not, see <http://www.gnu.org/licenses/>.

from .generic import Notifier
from json_helper import json_dumps
import sickgear
import requests

from _23 import b64encodestring, decode_str


PUSHAPI_ENDPOINT = 'https://api.pushbullet.com/v2/pushes'
DEVICEAPI_ENDPOINT = 'https://api.pushbullet.com/v2/devices'


class PushbulletNotifier(Notifier):

    @staticmethod
    def get_devices(access_token=None):
        # fill in omitted parameters
        if not access_token:
            access_token = sickgear.PUSHBULLET_ACCESS_TOKEN

        # get devices from pushbullet
        try:
            headers = dict(Authorization='Basic %s' % b64encodestring('%s:%s' % (access_token, '')))
            return requests.get(DEVICEAPI_ENDPOINT, headers=headers).text
        except (BaseException, Exception):
            return json_dumps(dict(error=dict(message='Error failed to connect')))

    def _notify(self, title, body, access_token=None, device_iden=None, **kwargs):
        """
        Sends a pushbullet notification based on the provided info or SG config

        title: The title of the notification to send
        body: The body string to send
        access_token: The access token to grant access
        device_iden: The iden of a specific target, if none provided send to all devices
        """
        access_token = self._choose(access_token, sickgear.PUSHBULLET_ACCESS_TOKEN)
        device_iden = self._choose(device_iden, sickgear.PUSHBULLET_DEVICE_IDEN)

        # send the request to Pushbullet
        result = None
        try:
            headers = {'Authorization': 'Basic %s' % b64encodestring('%s:%s' % (access_token, '')),
                       'Content-Type': 'application/json'}
            resp = requests.post(PUSHAPI_ENDPOINT, headers=headers,
                                 data=json_dumps(dict(
                                     type='note', title=title, body=decode_str(body.strip()),
                                     device_iden=device_iden)))
            resp.raise_for_status()
        except (BaseException, Exception):
            try:
                # noinspection PyUnboundLocalVariable
                result = resp.json()['error']['message']
            except (BaseException, Exception):
                result = 'no response'
            self._log_warning(u'%s' % result)

        return self._choose((True, 'Failed to send notification: %s' % result)[bool(result)], not bool(result))


notifier = PushbulletNotifier
