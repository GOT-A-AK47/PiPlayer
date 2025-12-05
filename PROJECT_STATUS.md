# PiPlayer - Project Status

## Project Overview
**PiPlayer** is a modular MP3 player for Raspberry Pi with support for Pimoroni DAC and Display HATs.
- **Target Hardware**: Raspberry Pi Zero v1.3
- **Status**: ✅ Complete and deployed
- **GitHub**: https://github.com/GOT-A-AK47/PiPlayer

## Quick Context for AI Assistants

This project was created in collaboration with Claude Code. It's a fully functional music player optimized for Raspberry Pi Zero with modular HAT support.

### What's Implemented

✅ **Complete Features**:
- Pygame-based audio playback (MP3, OGG, WAV, FLAC)
- Modular display system (ST7789 + Console fallback)
- GPIO button controls (4 buttons)
- Playlist management with ID3 metadata
- Volume control, shuffle, repeat modes
- Auto-installer with hardware detection
- Systemd service support

✅ **Hardware Support**:
- pHAT DAC (high-quality I2S audio)
- DAC Line-out LCD HAT (240x240 ST7789 display + 4 buttons)
- Console mode (testing without hardware)
- Auto-detection of DAC and display

✅ **Deployment**:
- Git repository initialized
- Pushed to GitHub
- Auto-installer with hardware detection
- ALSA audio configuration
- Helper scripts (start.sh, scan.sh)
- Complete documentation

### Project Structure

```
PiPlayer/
├── main.py                    # Main application
├── config.json               # Configuration
├── requirements.txt          # Python dependencies
├── install.sh               # Auto-installer (detects HATs)
├── README.md                # User documentation
├── IMAGE_CREATION.md        # Pi image creation guide
├── LICENSE                  # MIT License
├── .gitignore              # Git ignore rules
├── modules/                 # Core functionality
│   ├── __init__.py
│   ├── audio_player.py      # Pygame audio engine
│   ├── playlist_manager.py  # Library & playlist management
│   ├── display_manager.py   # Display abstraction layer
│   ├── button_handler.py    # GPIO button controls
│   └── config_loader.py     # Config management
├── drivers/                 # Modular display drivers
│   ├── __init__.py
│   ├── st7789_driver.py     # ST7789 LCD (240x240)
│   ├── console_driver.py    # Console/terminal fallback
│   └── (ssd1306_driver.py)  # Placeholder for OLED
├── music/                   # MP3 files (user content)
├── playlists/              # Saved playlists (.json)
└── logs/                   # Application logs
```

### User's Hardware

**Confirmed Hardware**:
- Raspberry Pi Zero v1.3 (no WiFi - standalone player)
- pHAT DAC (I2S high-quality audio output)
- DAC Line-out LCD HAT (ST7789 display + 4 buttons)

**Button Mapping** (GPIO BCM):
- Button A (GPIO 5): Play/Pause
- Button B (GPIO 6): Next track
- Button X (GPIO 16): Previous track
- Button Y (GPIO 24): Volume up

### Configuration Notes

**Optimized for Pi Zero v1.3**:
- `buffer_size`: 8192 (larger for smooth playback)
- `sample_rate`: 44100 Hz
- `display.driver`: "st7789" (or "console" for testing)
- `buttons.enabled`: true
- `web.enabled`: false (no WiFi on this Pi)

**Audio Setup**:
- I2S DAC via HiFiBerry driver overlay
- ALSA configured for hardware card 0
- Onboard audio disabled

### Installation Command

```bash
curl -sSL https://raw.githubusercontent.com/GOT-A-AK47/PiPlayer/master/install.sh | bash
```

The installer will:
1. Detect DAC HAT (pHAT DAC or compatible)
2. Detect display (ST7789 or fallback to console)
3. Configure ALSA for I2S audio
4. Update /boot/config.txt for HiFiBerry overlay
5. Create systemd service
6. Generate helper scripts

### Usage

```bash
# Add music
cp /path/to/music/*.mp3 ~/PiPlayer/music/

# Scan library
~/PiPlayer/scan.sh

# Start player
~/PiPlayer/start.sh

# Auto-start on boot
sudo systemctl enable piplayer
sudo systemctl start piplayer
```

### What Needs Work (Future)

⚠️ **Not Yet Implemented**:
- Web interface (optional, for Pi Zero W version)
- Equalizer/audio effects
- Album art display
- Spectrum analyzer visualization
- Internet radio support
- Bluetooth audio
- Volume down button (currently only volume up)

### Dependencies

**System**:
- Python 3.8+
- pygame
- python3-pil (Pillow)
- RPi.GPIO
- ALSA utils
- ST7789 library (for display HAT)

**Python**:
- pygame (audio playback)
- mutagen (ID3 metadata)
- Pillow (image processing for display)
- st7789 (display driver)
- RPi.GPIO (button handling)

### Important Notes for Next Session

1. **Target**: Raspberry Pi Zero v1.3 (non-WiFi)
2. **Audio**: pHAT DAC via I2S (HiFiBerry driver)
3. **Display**: ST7789 240x240 LCD with 4 buttons
4. **Modular Design**: Easy to add new display/DAC drivers
5. **Console Mode**: Testing without hardware works
6. **No Web Interface**: Not needed for current use case (no WiFi)
7. **GitHub Sync**: All changes pushed to origin/master

### Last Updated

- Date: 2025-12-05
- Last Commit: `727eee3` - Auto-installer added
- Working Directory: `C:\Users\tijnw\OneDrive - Scholengroep Sint-Michiel vzw\Documenten\PiPlayer`

### If You Need to Continue Development

1. **Check status**: `git status`
2. **Recent changes**: `git log --oneline -5`
3. **Test audio**: Pygame mixer tested and working
4. **Test display**: ST7789 driver ready (needs hardware to test)
5. **Deploy changes**: Commit and push to GitHub
6. **User testing**: User will test on actual Pi Zero v1.3

### Development Notes

**Display Driver System**:
- Modular: Easy to add new drivers
- Current: ST7789 (LCD HAT), Console (fallback)
- Future: SSD1306 (OLED), others as needed

**Audio System**:
- Using pygame.mixer (lightweight)
- Alternative considered: MPD (too heavy for Pi Zero)
- Buffer tuned for Pi Zero (8192 samples)

**Button System**:
- Uses RPi.GPIO with event detection
- Debounce: 20ms
- Fallback: KeyboardButtonHandler for testing

### Known Issues

- None reported (project just created)
- Awaiting user testing on Pi Zero v1.3
- Volume down button not mapped (only volume up on Button Y)

### Contact & Context

- **User**: Tijn (intermediate level, experimenting with Pi HATs)
- **Use Case**: Standalone MP3 player for Raspberry Pi Zero
- **Environment**: Pi Zero v1.3 with pHAT DAC and LCD HAT
- **Experience**: User knows how to use software but wants modular design
- **Testing**: User will test on actual hardware soon
