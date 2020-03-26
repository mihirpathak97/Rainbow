from titlecase import titlecase
import spotipy
import spotipy.oauth2 as oauth2
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover

import urllib.request


def generate_token(clientKey, clientSecret):
    """Generate the token. Please respect these credentials :)"""
    credentials = oauth2.SpotifyClientCredentials(
        client_id=clientKey,
        client_secret=clientSecret)
    token = credentials.get_access_token()
    return token


def generate_and_embed_metadata(music_file, id, clientKey, clientSecret):
    """Fetch a song's metadata from Spotify."""
    # token is required to grab metadata
    token = generate_token(clientKey, clientSecret)
    spotify = spotipy.Spotify(auth=token)
    try:
        meta_tags = spotify.track(id)
    except:
        print("Error requesting form Spotify API")
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
        print("Could not generate metadata")
        return

    if music_file.endswith('.mp3'):
        return embed_mp3(music_file, meta_tags)
    elif music_file.endswith('.m4a'):
        return embed_m4a(music_file, meta_tags)


def embed_mp3(music_file, meta_tags):
    """Embed metadata to MP3 files."""
    audiofile = EasyID3(music_file)
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
    audiofile = ID3(music_file)
    try:
        albumart = urllib.request.urlopen(
            meta_tags['album']['images'][0]['url'])
        audiofile["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3,
                                 desc=u'Cover', data=albumart.read())
        albumart.close()
    except IndexError:
        pass
    audiofile.save(v2_version=3)
    return print("Finished fixing metadata")


def embed_m4a(music_file, meta_tags):
    """Embed metadata to M4A files."""
    # Apple has specific tags - see mutagen docs -
    # http://mutagen.readthedocs.io/en/latest/api/mp4.html
    tags = {'album': '\xa9alb',
            'artist': '\xa9ART',
            'date': '\xa9day',
            'title': '\xa9nam',
            'originaldate': 'purd',
            'comment': '\xa9cmt',
            'group': '\xa9grp',
            'writer': '\xa9wrt',
            'genre': '\xa9gen',
            'tracknumber': 'trkn',
            'albumartist': 'aART',
            'disknumber': 'disk',
            'cpil': 'cpil',
            'albumart': 'covr',
            'copyright': 'cprt',
            'tempo': 'tmpo'}

    audiofile = MP4(music_file)
    audiofile[tags['artist']] = meta_tags['artists'][0]['name']
    audiofile[tags['albumartist']] = meta_tags['artists'][0]['name']
    audiofile[tags['album']] = meta_tags['album']['name']
    audiofile[tags['title']] = meta_tags['name']
    audiofile[tags['tracknumber']] = [(meta_tags['track_number'],
                                       meta_tags['total_tracks'])]
    audiofile[tags['disknumber']] = [(meta_tags['disc_number'], 0)]
    audiofile[tags['date']] = meta_tags['release_date']
    audiofile[tags['originaldate']] = meta_tags['release_date']
    if meta_tags['genre']:
        audiofile[tags['genre']] = meta_tags['genre']
    if meta_tags['copyright']:
        audiofile[tags['copyright']] = meta_tags['copyright']
    try:
        albumart = urllib.request.urlopen(
            meta_tags['album']['images'][0]['url'])
        audiofile[tags['albumart']] = [MP4Cover(
            albumart.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        albumart.close()
    except IndexError:
        pass
    audiofile.save()
    return print("Finished fixing metadata")
