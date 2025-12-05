# PiPlayer

**Raspberry Pi Music Player** - Een modulaire MP3 speler voor Raspberry Pi met support voor verschillende Pimoroni DAC en Display HATs.

## Features

### 🎵 Audio
- High-quality audio playback met pygame.mixer
- Support voor meerdere formaten: MP3, OGG, WAV, FLAC
- Volume controle
- Shuffle en repeat modes

### 📺 Display
- Modulaire display drivers
- Support voor ST7789 displays (240x240 LCD)
- Fallback naar console mode voor testing
- Real-time track info en progress bar

### 🎮 Controls
- 4 fysieke knoppen (A, B, X, Y)
- Button A: Play/Pause
- Button B: Next track
- Button X: Previous track
- Button Y: Volume up

### 📝 Playlist Management
- Automatisch scannen van music directory
- Playlists opslaan en laden
- ID3 metadata ondersteuning
- Zoeken op titel, artist, album

## Hardware Support

### Compatibele Pimoroni HATs
- ✅ pHAT DAC - High-quality audio output
- ✅ DAC Line-out LCD HAT - Display + 4 buttons + DAC
- ✅ Display HAT Mini - 240x240 LCD met knoppen
- ✅ Console mode - Testing zonder hardware

### Raspberry Pi Modellen
- Raspberry Pi Zero v1.3
- Raspberry Pi Zero W (optionele WiFi voor web interface)
- Raspberry Pi 3/4 (more power for larger libraries)

## Installatie

### 1. Raspberry Pi Setup

```bash
# Update systeem
sudo apt update && sudo apt upgrade -y

# Installeer system dependencies
sudo apt install -y python3-pip python3-pygame git

# Optioneel: voor betere audio
sudo apt install -y alsa-utils
```

### 2. PiPlayer Installeren

```bash
# Clone repository
git clone https://github.com/jouw-username/PiPlayer.git
cd PiPlayer

# Installeer Python dependencies
pip3 install -r requirements.txt

# Maak directories
mkdir -p music playlists logs
```

### 3. Audio Configuratie

Voor pHAT DAC of DAC Line-out LCD HAT:

```bash
# Edit /boot/config.txt
sudo nano /boot/config.txt

# Voeg toe (voor pHAT DAC):
dtoverlay=hifiberry-dac
gpio_pin=25

# Herstart
sudo reboot
```

Test audio:
```bash
speaker-test -t wav -c 2
```

## Configuratie

Edit `config.json`:

```json
{
  "music": {
    "directory": "music",
    "playlist_directory": "playlists"
  },
  "audio": {
    "sample_rate": 44100,
    "channels": 2,
    "buffer_size": 4096
  },
  "display": {
    "enabled": true,
    "driver": "st7789",
    "width": 240,
    "height": 240
  },
  "buttons": {
    "enabled": true,
    "button_a": 5,
    "button_b": 6,
    "button_x": 16,
    "button_y": 24
  }
}
```

### Display Drivers

**Voor DAC Line-out LCD HAT** (ST7789):
```json
{
  "display": {
    "driver": "st7789",
    "width": 240,
    "height": 240,
    "rotation": 0
  }
}
```

**Console mode** (testing zonder hardware):
```json
{
  "display": {
    "driver": "console"
  }
}
```

### Button Mapping

Voor DAC Line-out LCD HAT (4 knoppen):
```json
{
  "buttons": {
    "button_a": 5,    // Play/Pause
    "button_b": 6,    // Next
    "button_x": 16,   // Previous
    "button_y": 24    // Volume Up
  }
}
```

## Gebruik

### Muziek Toevoegen

```bash
# Kopieer MP3s naar music directory
cp /path/to/music/*.mp3 music/

# Of via USB
sudo mount /dev/sda1 /mnt/usb
cp /mnt/usb/music/*.mp3 music/
```

### Player Starten

```bash
# Normale start
python3 main.py

# Scan music directory eerst
python3 main.py --scan

# List playlists
python3 main.py --list-playlists
```

### Auto-start bij Boot

Maak een systemd service:

```bash
sudo nano /etc/systemd/system/piplayer.service
```

```ini
[Unit]
Description=PiPlayer Music Player
After=sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PiPlayer
ExecStart=/usr/bin/python3 /home/pi/PiPlayer/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl enable piplayer
sudo systemctl start piplayer
```

## Project Structuur

```
PiPlayer/
├── main.py                    # Main applicatie
├── config.json               # Configuratie
├── requirements.txt          # Dependencies
├── modules/                  # Core modules
│   ├── audio_player.py       # Audio playback (pygame)
│   ├── playlist_manager.py   # Playlist & library management
│   ├── display_manager.py    # Display control
│   ├── button_handler.py     # Button input handling
│   └── config_loader.py      # Config management
├── drivers/                  # Display drivers
│   ├── st7789_driver.py      # ST7789 LCD driver
│   ├── console_driver.py     # Console fallback
│   └── ssd1306_driver.py     # OLED driver (optioneel)
├── music/                    # MP3 files
├── playlists/               # Saved playlists (.json)
├── logs/                    # Log files
└── templates/               # Web interface (optioneel)
```

## Troubleshooting

### Geen Audio Output

```bash
# Check audio devices
aplay -l

# Test audio
speaker-test -t wav -c 2

# Set default output
sudo raspi-config
# Select: System Options > Audio > Select your DAC
```

### Display Werkt Niet

```bash
# Check SPI enabled
ls /dev/spi*

# Enable SPI
sudo raspi-config
# Interface Options > SPI > Enable

# Test display
python3 -c "import ST7789; print('ST7789 OK')"
```

### Buttons Werken Niet

```bash
# Check GPIO
gpio readall

# Test button (GPIO 5)
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP); print(GPIO.input(5))"
```

### Permission Errors

```bash
# Add user to audio/gpio groups
sudo usermod -a -G audio,gpio,spi pi

# Logout and login again
```

## Development

### Testing Zonder Hardware

Gebruik console mode:

```bash
# Edit config.json
{
  "display": {"driver": "console"},
  "buttons": {"enabled": false}
}

# Run
python3 main.py
```

### Nieuwe Display Driver Toevoegen

1. Create `drivers/my_display_driver.py`
2. Implement `MyDisplayDriver` class met deze methods:
   - `initialize()`
   - `update(track_info)`
   - `show_message(title, message)`
   - `cleanup()`
3. Update `config.json`: `"driver": "my_display"`

## Roadmap

- [x] Audio playback (pygame)
- [x] Display support (ST7789)
- [x] Button controls
- [x] Playlist management
- [ ] Web interface
- [ ] Equalizer/Audio effects
- [ ] Internet radio support
- [ ] Bluetooth audio
- [ ] Album art display
- [ ] Spectrum analyzer visualization

## Tips & Tricks

### Optimalisatie voor Pi Zero

In `config.json`:
```json
{
  "audio": {
    "buffer_size": 8192,  // Grotere buffer = minder clicks
    "sample_rate": 44100
  }
}
```

### Betere Audio Kwaliteit

```bash
# Disable on-board audio (gebruik alleen HAT)
# Edit /boot/config.txt
dtparam=audio=off
dtoverlay=hifiberry-dac

# Reduce audio latency
sudo nano /etc/asound.conf
# Add:
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
```

### SSH File Transfer

```bash
# Van PC naar Pi
scp /path/to/music/*.mp3 pi@raspberrypi.local:~/PiPlayer/music/

# Met rsync (sneller voor veel files)
rsync -avz --progress /path/to/music/ pi@raspberrypi.local:~/PiPlayer/music/
```

## License

MIT License - See LICENSE file

## Credits

- Gebouwd met Python en pygame
- Pimoroni voor geweldige Pi HATs
- Mutagen voor metadata extraction

## Support

Voor vragen of issues: maak een GitHub issue aan of check de documentatie.

Enjoy your music! 🎵
