# Rainbow [Audius Mod]
# Copyright 2017, Mihir Pathak.

import argparse
from lib import metadata

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Embed metadata into audio files using spotify API")
    parser.add_argument('file', type=str, help='Absolute path of audio file')
    parser.add_argument('id', help='Spotify ID of song')
    parser.add_argument('key', help='Spotify API client ID')
    parser.add_argument('secret', help='Spotify API client secret')
    args = parser.parse_args()
    metadata.generate_and_embed_metadata(args.file, args.id, args.key, args.secret)
