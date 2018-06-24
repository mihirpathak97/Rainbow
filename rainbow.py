# Rainbow [Audius Mod]
# Copyright 2017, Mihir Pathak.

import argparse
from lib import metadata

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Embed metadata into audio files using spotify API")
    parser.add_argument('-f', '--file', help='Absolute path of audio file')
    parser.add_argument('-id', help='Spotify ID of song')
    args = parser.parse_args()
    metadata.generate_and_embed_metadata(args.file, args.id)
