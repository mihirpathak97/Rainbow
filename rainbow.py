# Rainbow v0.2
# Copyright 2017, Mihir Pathak.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

from __future__ import division
from __future__ import absolute_import

import os
import json
import requests
import contextlib
import errno
import subprocess
import threading
import time
import gzip
import sys
import argparse
from lib import metadata
from sys import platform
from io import BytesIO


API_BASE_URL = 'http://api.acoustid.org/v2/'
DEFAULT_META = 'recordings'
MAX_AUDIO_LENGTH = 120 # Seconds.


# Exceptions.

class rainbowError(Exception):
    """Base for exceptions in this module."""


class FingerprintGenerationError(rainbowError):
    """The audio could not be fingerprinted."""


class NoBackendError(FingerprintGenerationError):
    """The audio could not be fingerprinted because the
    fpcalc command-line tool is not found."""


class FingerprintSubmissionError(rainbowError):
    """Missing required data for a fingerprint submission."""


class WebServiceError(rainbowError):
    """The Web service request failed. The field ``message`` contains a
    description of the error. If this is an error that was specifically
    sent by the acoustid server, then the ``code`` field contains the
    acoustid error code."""
    def __init__(self, message, response=None):
        """Create an error for the given HTTP response body, if
        provided, with the ``message`` as a fallback."""
        if response:
            # Try to parse the JSON error response.
            try:
                data = json.loads(response)
            except ValueError:
                pass
            else:
                if isinstance(data.get('error'), dict):
                    error = data['error']
                    if 'message' in error:
                        message = error['message']
                    if 'code' in error:
                        self.code = error['code']

        super(WebServiceError, self).__init__(message)
        self.message = message


# Endpoint configuration.

def set_base_url(url):
    """Set the URL of the API server to query."""
    if not url.endswith('/'):
        url += '/'
    global API_BASE_URL
    API_BASE_URL = url


def get_lookup_url():
    """Get the URL of the lookup API endpoint."""
    return API_BASE_URL + 'lookup'


def get_submit_url():
    """Get the URL of the submission API endpoint."""
    return API_BASE_URL + 'submit'


# Compressed HTTP request bodies.

def compress(data):
    """Compress a bytestring to a gzip archive."""
    sio = BytesIO()
    with contextlib.closing(gzip.GzipFile(fileobj=sio, mode='wb')) as f:
        f.write(data)
    return sio.getvalue()


class CompressedHTTPAdapter(requests.adapters.HTTPAdapter):
    """An `HTTPAdapter` that compresses request bodies with gzip. The
    Content-Encoding header is set accordingly."""
    def add_headers(self, request, **kwargs):
        body = request.body
        if not isinstance(body, bytes):
            body = body.encode('utf8')
        request.prepare_body(compress(body), None)
        request.headers['Content-Encoding'] = 'gzip'


def api_request(url, params):
    """Makes a POST request for the URL with the given form parameters,
    which are encoded as compressed form data, and returns a parsed JSON
    response. May raise a WebServiceError if the request fails."""
    headers = {
        'Accept-Encoding': 'gzip',
        "Content-Type": "application/x-www-form-urlencoded"
    }

    session = requests.Session()
    session.mount('http://', CompressedHTTPAdapter())
    try:
        response = session.post(url, data=params, headers=headers)
    except requests.exceptions.RequestException as exc:
        raise WebServiceError("HTTP request failed: {0}".format(exc))

    try:
        return response.json()
    except ValueError:
        raise WebServiceError('response is not valid JSON')


# Main API.

def lookup(apikey, fingerprint, duration, meta=DEFAULT_META):
    """Look up a fingerprint with the Acoustid Web service. Returns the
    Python object reflecting the response JSON data."""
    params = {
        'format': 'json',
        'client': apikey,
        'duration': int(duration),
        'fingerprint': fingerprint,
        'meta': meta,
    }
    return api_request(get_lookup_url(), params)


def parse_lookup_result(data):
    """Given a parsed JSON response, generate tuples containing the match
    score, the MusicBrainz recording ID, the title of the recording, and
    the name of the recording's first artist. (If an artist is not
    available, the last item is None.) If the response is incomplete,
    raises a WebServiceError."""
    if data['status'] != 'ok':
        raise WebServiceError("status: %s" % data['status'])
    if 'results' not in data:
        raise WebServiceError("results not included")

    for result in data['results']:
        score = result['score']
        if 'recordings' not in result:
            # No recording attached. This result is not very useful.
            continue

        for recording in result['recordings']:
            # Get the artist if available.
            if recording.get('artists'):
                names = [artist['name'] for artist in recording['artists']]
                artist_name = '; '.join(names)
            else:
                artist_name = None

            yield score, recording['id'], recording.get('title'), artist_name


def fingerprint_file(path, maxlength=MAX_AUDIO_LENGTH):
    """Fingerprint a file by calling the fpcalc application."""
    if platform.find("win") != -1:
        fpcalc = 'fpcalc\\fpcalc.exe'
    elif platform.find("linux") != -1:
        fpcalc = 'fpcalc/fpcalc' #use unix binary for linux
    command = [fpcalc, "-length", str(maxlength), path]
    try:
        with open(os.devnull, 'wb') as devnull:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=devnull)
            output, _ = proc.communicate()
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            raise NoBackendError("fpcalc not found")
        else:
            raise FingerprintGenerationError("fpcalc invocation failed: %s" % str(exc))
    except UnicodeEncodeError:
        raise FingerprintGenerationError("argument encoding failed")
    retcode = proc.poll()
    if retcode:
        print("fpcalc exited with status %i" % retcode)

    duration = fp = None
    for line in output.splitlines():
        try:
            parts = line.split(b'=', 1)
        except ValueError:
            raise FingerprintGenerationError("malformed fpcalc output")
        if parts[0] == b'DURATION':
            try:
                duration = float(parts[1])
            except ValueError:
                raise FingerprintGenerationError("fpcalc duration not numeric")
        elif parts[0] == b'FINGERPRINT':
            fp = parts[1]

    if duration is None or fp is None:
        print("Skipping {0}...".format(path))
        return None
    return duration, fp


def match(apikey, path, meta=DEFAULT_META, parse=True):
    """Look up the metadata for an audio file. If ``parse`` is true,
    then ``parse_lookup_result`` is used to return an iterator over
    small tuple of relevant information; otherwise, the full parsed JSON
    response is returned."""
    if fingerprint_file(path) is not None:
        duration, fp = fingerprint_file(path)
        response = lookup(apikey, fp, duration, meta)
    else:
        return None
    if parse:
        return parse_lookup_result(response)
    else:
        return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recognise unknown audio files and fix metadata")
    parser.add_argument('-d', '--directory', default=sys.path[0], help='Directory in which you want to perform audio fingerprinting')
    parser.add_argument('-f', default=True, help='Perform audio fingerprinting. Default=True', action='store_true')
    parser.add_argument('-fm', default=False, help='Fix metadata after recognition. Default=False', action='store_true')
    args = parser.parse_args()
    if args.directory:
        directory = args.directory
        API_KEY = 'cSpUJKpD' # please respect these credentials :)
        number = 0
        total = 0
        for audio_file in os.listdir(directory):
            if os.path.splitext(audio_file)[-1] == '.mp3':
                total +=1
                audio_file = os.path.join(directory, audio_file)
                results = match(API_KEY, audio_file)
                time.sleep(0.35) # only 3 requests per second
                done = False
                if results is not None:
                    done = True
                    for score, rid, title, artist in results:
                        if title and artist is not None:
                            number+=1
                            print('{0}. {1} By {2}'.format(number, title, artist))
                            if args.fm:
                                if metadata.generate_metadata(audio_file, title, artist):
                                    done = True
                                else:
                                    done = False
                            break
                        else:
                            continue
                    if not done:
                        fo = open('skipped.txt', 'a')
                        fo.write(audio_file + '\n')
                        fo.close()
                else:
                    fo = open('skipped.txt', 'a')
                    fo.write(audio_file + '\n')
                    fo.close()
        print("finished querying {0} audio files in directory".format(total))
        print("Success : {0}".format(number))
        print("List of skipped files (if any) is stored in 'skipped.txt'")

    else:
        print('Directory missing!\nExecute `rainbow.py -h` for instructions')
