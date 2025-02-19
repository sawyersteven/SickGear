# Author: Rafael Silva <rpluto@gmail.com>
# Author: Marvin Pinto <me@marvinp.ca>
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

from .generic import Notifier
import sickgear

from exceptions_helper import ex

from _23 import decode_bytes, decode_str, urlencode
# noinspection PyUnresolvedReferences
from six.moves import urllib


class Boxcar2Notifier(Notifier):

    def __init__(self):
        super(Boxcar2Notifier, self).__init__()

        self.sg_logo_file = 'apple-touch-icon-60x60.png'

    def _notify(self, title, body, access_token=None, sound=None, **kwargs):
        """
        Sends a boxcar2 notification to the address provided

        title: The title of the message
        body: The message to send
        access_token: To send to this device
        sound: Sound profile to use

        returns: True if the message succeeded, False otherwise
        """
        access_token = self._choose(access_token, sickgear.BOXCAR2_ACCESSTOKEN)
        sound = self._choose(sound, sickgear.BOXCAR2_SOUND)

        # build up the URL and parameters
        # more info goes here -
        # https://boxcar.uservoice.com/knowledgebase/articles/306788-how-to-send-your-boxcar-account-a-notification
        body = decode_str(body.strip())

        data = urlencode({
                'user_credentials': access_token,
                'notification[title]': '%s - %s' % (title, body),
                'notification[long_message]': body,
                'notification[sound]': sound,
                'notification[source_name]': 'SickGear',
                'notification[icon_url]': self._sg_logo_url
            })

        # send the request to boxcar2
        result = None
        try:
            req = urllib.request.Request('https://new.boxcar.io/api/notifications')
            # PY2 http_response_obj has no `with` context manager
            http_response_obj = urllib.request.urlopen(req, decode_bytes(data))
            http_response_obj.close()

        except urllib.error.HTTPError as e:
            if not hasattr(e, 'code'):
                self._log_error(u'Notification failed: %s' % ex(e))
            else:
                result = 'Notification failed. Error code: %s' % e.code
                self._log_error(result)

                if 503 == e.code:
                    result = 'Server too busy to handle the request at this time'
                    self._log_warning(result)
                else:
                    if 404 == e.code:
                        result = 'Access token is wrong/not associated to a device'
                        self._log_error(result)
                    elif 401 == e.code:
                        result = 'Access token not recognized'
                        self._log_error(result)
                    elif 400 == e.code:
                        result = 'Wrong data sent to Boxcar'
                        self._log_error(result)
        except urllib.error.URLError as e:
            self._log_error(u'Notification failed: %s' % ex(e))

        return self._choose((True, 'Failed to send notification: %s' % result)[bool(result)], not bool(result))


notifier = Boxcar2Notifier
