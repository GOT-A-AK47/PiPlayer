# Music Directory

Plaats hier je MP3 bestanden.

## Ondersteunde Formaten

- MP3 (.mp3)
- OGG Vorbis (.ogg)
- WAV (.wav)
- FLAC (.flac)

## Muziek Toevoegen

### Via SCP (vanaf PC):
```bash
scp /path/to/music/*.mp3 pi@raspberrypi.local:~/PiPlayer/music/
```

### Via USB stick:
```bash
sudo mount /dev/sda1 /mnt/usb
cp /mnt/usb/music/*.mp3 ~/PiPlayer/music/
```

### Directe copy op Pi:
```bash
cp /path/to/music/*.mp3 ~/PiPlayer/music/
```

## Scannen

Na het toevoegen van nieuwe muziek:

```bash
python3 main.py --scan
```

Dit scant de music directory en leest metadata (titel, artist, album) uit de bestanden.
