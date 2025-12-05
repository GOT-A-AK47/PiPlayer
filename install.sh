#!/bin/bash
#
# PiPlayer Auto-Installer for Raspberry Pi Zero v1.3
# One-command installation script for Pi with Pimoroni DAC HATs
#
# Usage: curl -sSL https://raw.githubusercontent.com/GOT-A-AK47/PiPlayer/master/install.sh | bash
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════╗"
echo "║        PiPlayer Auto-Installer           ║"
echo "║     Raspberry Pi Zero v1.3 Edition       ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Please run without sudo${NC}"
    echo "The script will ask for sudo when needed"
    exit 1
fi

echo -e "${GREEN}[1/9] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}[2/9] Installing system dependencies...${NC}"
sudo apt install -y \
    python3-pip \
    python3-pygame \
    python3-pil \
    python3-rpi.gpio \
    git \
    alsa-utils \
    mpg123

echo -e "${GREEN}[3/9] Cloning PiPlayer repository...${NC}"
INSTALL_DIR="$HOME/PiPlayer"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}PiPlayer directory already exists. Updating...${NC}"
    cd "$INSTALL_DIR"
    git pull
else
    git clone https://github.com/GOT-A-AK47/PiPlayer.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "${GREEN}[4/9] Installing Python dependencies...${NC}"
pip3 install -r requirements.txt

echo -e "${GREEN}[5/9] Creating directories...${NC}"
mkdir -p music playlists logs

echo -e "${GREEN}[6/9] Detecting DAC HAT...${NC}"
DAC_TYPE="none"

# Check for pHAT DAC
if lsmod | grep -q "snd_soc_hifiberry_dac"; then
    DAC_TYPE="phat_dac"
    echo -e "${GREEN}Detected: pHAT DAC${NC}"
# Check for other I2S DACs
elif lsmod | grep -q "snd_soc"; then
    DAC_TYPE="generic_i2s"
    echo -e "${YELLOW}Detected: Generic I2S DAC${NC}"
else
    echo -e "${YELLOW}No DAC detected, will use onboard audio${NC}"
fi

echo -e "${GREEN}[7/9] Configuring audio...${NC}"

# Configure ALSA for DAC
if [ "$DAC_TYPE" != "none" ]; then
    # Disable onboard audio
    if ! grep -q "^dtparam=audio=off" /boot/config.txt; then
        echo "dtparam=audio=off" | sudo tee -a /boot/config.txt
    fi

    # Enable I2S DAC overlay if not present
    if ! grep -q "^dtoverlay=hifiberry-dac" /boot/config.txt; then
        echo "dtoverlay=hifiberry-dac" | sudo tee -a /boot/config.txt
        echo -e "${YELLOW}Added HiFiBerry DAC overlay - reboot required${NC}"
        REBOOT_REQUIRED=true
    fi

    # Create ALSA config
    cat > $HOME/.asoundrc << 'EOF'
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
EOF
    echo -e "${GREEN}ALSA configured for DAC${NC}"
fi

echo -e "${GREEN}[8/9] Detecting Display HAT...${NC}"
DISPLAY_TYPE="console"

# Check for SPI (needed for ST7789)
if [ -e "/dev/spidev0.0" ] || [ -e "/dev/spidev0.1" ]; then
    DISPLAY_TYPE="st7789"
    echo -e "${GREEN}SPI enabled - assuming ST7789 display${NC}"
else
    echo -e "${YELLOW}No SPI detected - using console mode${NC}"
    echo -e "${YELLOW}Enable SPI: sudo raspi-config -> Interface Options -> SPI${NC}"
fi

# Update config.json
cat > config.json << EOF
{
  "application": {
    "name": "PiPlayer",
    "version": "1.0.0"
  },
  "log_level": "INFO",
  "log_file": "logs/piplayer.log",
  "music": {
    "directory": "music",
    "playlist_directory": "playlists",
    "supported_formats": [".mp3", ".ogg", ".wav", ".flac"]
  },
  "audio": {
    "sample_rate": 44100,
    "bit_depth": -16,
    "channels": 2,
    "buffer_size": 8192
  },
  "player": {
    "auto_start": false,
    "default_volume": 0.7,
    "repeat_mode": "all",
    "shuffle": false,
    "last_playlist": null
  },
  "display": {
    "enabled": true,
    "driver": "$DISPLAY_TYPE",
    "width": 240,
    "height": 240,
    "rotation": 0,
    "backlight_pin": 13
  },
  "buttons": {
    "enabled": true,
    "debounce_time": 0.02,
    "button_a": 5,
    "button_b": 6,
    "button_x": 16,
    "button_y": 24
  },
  "web": {
    "enabled": false,
    "host": "0.0.0.0",
    "port": 5000
  }
}
EOF

echo -e "${GREEN}Created config for detected hardware${NC}"

echo -e "${GREEN}[9/9] Creating systemd service...${NC}"

cat > /tmp/piplayer.service << EOF
[Unit]
Description=PiPlayer Music Player
After=sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/piplayer.service /etc/systemd/system/piplayer.service
sudo systemctl daemon-reload

# Create helper scripts
cat > $INSTALL_DIR/start.sh << 'EOF'
#!/bin/bash
cd ~/PiPlayer
python3 main.py
EOF
chmod +x $INSTALL_DIR/start.sh

cat > $INSTALL_DIR/scan.sh << 'EOF'
#!/bin/bash
cd ~/PiPlayer
python3 main.py --scan
EOF
chmod +x $INSTALL_DIR/scan.sh

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     PiPlayer Installation Complete!      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Installation directory:${NC} $INSTALL_DIR"
echo -e "${BLUE}DAC detected:${NC} $DAC_TYPE"
echo -e "${BLUE}Display mode:${NC} $DISPLAY_TYPE"
echo ""
echo -e "${YELLOW}Quick Start:${NC}"
echo "  1. Add MP3s: cp /path/to/music/*.mp3 $INSTALL_DIR/music/"
echo "  2. Scan library: $INSTALL_DIR/scan.sh"
echo "  3. Start player: $INSTALL_DIR/start.sh"
echo ""
echo -e "${YELLOW}Controls:${NC}"
echo "  Button A - Play/Pause"
echo "  Button B - Next track"
echo "  Button X - Previous track"
echo "  Button Y - Volume up"
echo ""
echo -e "${YELLOW}Auto-start on boot:${NC}"
echo "  sudo systemctl enable piplayer"
echo "  sudo systemctl start piplayer"
echo ""
echo -e "${YELLOW}Test audio:${NC}"
echo "  speaker-test -t wav -c 2"
echo ""

if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${RED}⚠️  REBOOT REQUIRED for DAC changes to take effect${NC}"
    echo "  sudo reboot"
    echo ""
fi

echo -e "${GREEN}Enjoy your music! 🎵${NC}"
