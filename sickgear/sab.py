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

import sickgear
from . import logger
from .classes import NZBDataSearchResult, NZBSearchResult


def send_nzb(search_result):
    """
    Sends an nzb to SABnzbd via the API.

    :param search_result: The NZBSearchResult object to send to SAB
    :type search_result: NZBSearchResult or NZBDataSearchResult
    :return: success
    :rtype: bool
    """

    success, result, nzb_type = True, '', 'nzb'
    if search_result.resultType in ('nzb', 'nzbdata'):

        # set up a dict with the URL params in it
        params = {'output': 'json'}
        if None is not sickgear.SAB_USERNAME:
            params['ma_username'] = sickgear.SAB_USERNAME
        if None is not sickgear.SAB_PASSWORD:
            params['ma_password'] = sickgear.SAB_PASSWORD
        if None is not sickgear.SAB_APIKEY:
            params['apikey'] = sickgear.SAB_APIKEY
        if None is not sickgear.SAB_CATEGORY:
            params['cat'] = sickgear.SAB_CATEGORY

        # use high priority if specified (recently aired episode)
        if 1 == search_result.priority:
            params['priority'] = 1

        params['nzbname'] = '%s.nzb' % search_result.name

        kwargs = {}
        # if it's a normal result we just pass SAB the URL
        if 'nzb' == search_result.resultType:
            nzb_type = 'nzb url'
            params['mode'] = 'addurl'
            params['name'] = search_result.url
            kwargs['params'] = params

        # if we get a raw data result we want to upload it to SAB
        else:
            nzb_type = 'file nzb'
            params['mode'] = 'addfile'
            kwargs['post_data'] = params
            nzb_data = search_result.get_data()
            if not nzb_data:
                return False
            kwargs['files'] = {'nzbfile': ('%s.nzb' % search_result.name, nzb_data)}

        logger.log(u'Sending %s to SABnzbd: %s' % (nzb_type, search_result.name))

        url = '%sapi' % sickgear.SAB_HOST
        logger.log(u'SABnzbd at %s sent params: %s' % (url, params), logger.DEBUG)
        success, result = _get_url(url, **kwargs)

    if not success:
        return False

    # do some crude parsing of the result text to determine what SAB said
    if result.get('status'):
        logger.log(u'Success from SABnzbd using %s' % nzb_type, logger.DEBUG)
        return True
    elif 'error' in result:
        logger.log(u'Failed using %s with SABnzbd, response: %s' % (nzb_type, result.get('error', 'und')), logger.ERROR)
    else:
        logger.log(u'Failure unknown using %s with SABnzbd, response: %s' % (nzb_type, result), logger.ERROR)
    return False


def _check_sab_response(result):

    if 0 == len(result):
        logger.log('No data returned from SABnzbd, nzb not used', logger.ERROR)
        return False, 'No data from SABnzbd'

    if 'error' in result:
        logger.log(result['error'], logger.ERROR)
        return False, result['error']
    return True, result


def _get_url(url, params=None, **kwargs):

    result = sickgear.helpers.get_url(url, params=params, parse_json=True, **kwargs)
    if None is result:
        logger.log('Error, no response from SABnzbd', logger.ERROR)
        return False, 'Error, no response from SABnzbd'
    return True, result


def access_method(host):

    success, result = _get_url('%sapi' % host, params={'mode': 'auth', 'output': 'json'})
    if not success:
        return False, result
    return True, result['auth']


def test_authentication(host=None, username=None, password=None, apikey=None):
    """
    Sends a simple API request to SAB to determine if the given connection information is connect

    Returns: A tuple containing the success boolean and a message
    :param host: The host where SAB is running (incl port)
    :param username: The username to use for the HTTP request
    :param password: The password to use for the HTTP request
    :param apikey: The API key to provide to SAB
    """

    # build up the URL parameters
    params = {'mode': 'queue', 'ma_username': username, 'ma_password': password, 'apikey': apikey, 'output': 'json'}
    url = '%sapi' % host

    # send the test request
    logger.log(u'SABnzbd test URL: %s with parameters: %s' % (url, params), logger.DEBUG)
    success, result = _get_url(url, params=params)
    if not success:
        return False, result

    # check the result and determine if it's good or not
    success, response = _check_sab_response(result)
    if not success:
        return False, response
    return True, 'Success'
