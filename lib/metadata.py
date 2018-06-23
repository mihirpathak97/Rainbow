from titlecase import titlecase
import spotipy
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover

import urllib.request

def generate_token():
    """Generate the token. Please respect these credentials :)"""
    credentials = oauth2.SpotifyClientCredentials(
        client_id='05a27dfaa107438eb78215d18ce0aedc',
        client_secret='16a88c04b61941b39a1aa3f3f2190e9e')
    token = credentials.get_access_token()
    return token


def generate_and_embed_metadata(path, id):
    """Fetch a song's metadata from Spotify."""
    # token is required to grab metadata
    token = generate_token()
    spotify = spotipy.Spotify(auth=token)
    try:
        meta_tags = spotify.track(id)
    except:
        print("Error generating metadata from Spotify")
        return
    artist = spotify.artist(meta_tags['artists'][0]['id'])
    album = spotify.album(meta_tags['album']['id'])

    try:
        meta_tags[u'genre'] = titlecase(artist['genres'][0])
    except IndexError:
        meta_tags[u'genre'] = None
    try:
        meta_tags[u'copyright'] = album['copyrights'][0]['text']
    except IndexError:
        meta_tags[u'copyright'] = None
    try:
        meta_tags['isrc']
    except KeyError:
        meta_tags['isrc'] = None

    meta_tags[u'release_date'] = album['release_date']
    meta_tags[u'publisher'] = album['label']
    meta_tags[u'total_tracks'] = album['tracks']['total']

    if meta_tags is None:
        print("Invalid metadata!")
        return

    """Embed metadata to MP3 files."""
    audiofile = EasyID3(path)
    audiofile['artist'] = meta_tags['artists'][0]['name']
    audiofile['albumartist'] = meta_tags['artists'][0]['name']
    audiofile['album'] = meta_tags['album']['name']
    audiofile['title'] = meta_tags['name']
    audiofile['tracknumber'] = [meta_tags['track_number'],
                                meta_tags['total_tracks']]
    audiofile['discnumber'] = [meta_tags['disc_number'], 0]
    audiofile['date'] = meta_tags['release_date']
    audiofile['originaldate'] = meta_tags['release_date']
    audiofile['media'] = meta_tags['type']
    audiofile['author'] = meta_tags['artists'][0]['name']
    audiofile['lyricist'] = meta_tags['artists'][0]['name']
    audiofile['arranger'] = meta_tags['artists'][0]['name']
    audiofile['performer'] = meta_tags['artists'][0]['name']
    audiofile['encodedby'] = meta_tags['publisher']
    audiofile['website'] = meta_tags['external_urls']['spotify']
    audiofile['length'] = str(meta_tags['duration_ms'] / 1000)
    if meta_tags['genre']:
        audiofile['genre'] = meta_tags['genre']
    if meta_tags['copyright']:
        audiofile['copyright'] = meta_tags['copyright']
    if meta_tags['isrc']:
        audiofile['isrc'] = meta_tags['external_ids']['isrc']
    audiofile.save(v2_version=3)
    audiofile = ID3(path)
    try:
        albumart = urllib.request.urlopen(meta_tags['album']['images'][0]['url'])
        audiofile["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3,
                                 desc=u'Cover', data=albumart.read())
        albumart.close()
    except IndexError:
        pass
    audiofile.save(v2_version=3)
    print('Fixed metadata!')
    return
