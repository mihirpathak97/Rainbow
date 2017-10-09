# Audius

- Utilizes AcoustID audio recognition service

- Can recognize unknown audio files and also set their ID3 metadata


## Installation & Usage

- **This tool works only with Python 3**

- Download and extract the [zip file](https://github.com/mihirpathak97/Audius/archive/master.zip) from master branch.

- For all available options, run `python audius.py --help`.

```
usage: audius.py [-h] [-d DIRECTORY] [-f] [-fm]

Recognise unknown audio files and fix metadata

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        Directory in which you want to perform audio
                        fingerprinting
  -f                    Perform audio fingerprinting. Default=True
  -fm                   Fix metadata after recognition. Default=False

```

### Recognize all songs in a directory

- Open up `cmd` and run `python audius.py -d path-to-your-directory`.

- This will then check all the songs in the directory [`.mp3` only] and try to recognize it.

- If you don't specify directory, the script will assume a default value of `sys.path[0]`, i.e where you are invoking the script

- List of all skipped audio files will be stored in `skipped.txt` at the root of the code base


### Fixing ID3 MetaData

- To embed proper metadata for the songs, just add `-fm` option when running the script

- The script will then try to find the song in Spotify and embed the details to the file


## License

- Licensed under `The Apache License`
