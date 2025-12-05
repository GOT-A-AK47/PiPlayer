# PiPlayer - Custom Raspberry Pi Image Creation

Guide voor het maken van een custom Raspberry Pi OS image met PiPlayer en DAC support voorgeïnstalleerd.

## Optie 1: Automatische Installatie (Aanbevolen)

De snelste methode is een verse Raspbian Lite met het auto-install script:

### Quick Start

```bash
# 1. Flash Raspberry Pi OS Lite naar SD kaart

# 2. Boot Pi en run installer:
curl -sSL https://raw.githubusercontent.com/GOT-A-AK47/PiPlayer/master/install.sh | bash

# 3. Reboot (voor DAC support)
sudo reboot

# 4. Add muziek en start
cp /path/to/music/*.mp3 ~/PiPlayer/music/
~/PiPlayer/scan.sh
~/PiPlayer/start.sh
```

## Optie 2: Custom Image met Pi-Gen

Voor een volledige custom image:

### Voorbereiding

```bash
# Linux machine nodig (of WSL2)
git clone https://github.com/RPi-Distro/pi-gen.git
cd pi-gen

# Config voor PiPlayer
cat > config << EOF
IMG_NAME='PiPlayer-PiZero'
RELEASE='bookworm'
DEPLOY_COMPRESSION='zip'
TARGET_HOSTNAME='piplayer'
FIRST_USER_NAME='piplayer'
FIRST_USER_PASS='piplayer123'
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2 stage-piplayer"
EOF
```

### Custom Stage Maken

```bash
mkdir -p stage-piplayer/00-install-piplayer
cat > stage-piplayer/00-install-piplayer/00-run.sh << 'SCRIPT'
#!/bin/bash -e

on_chroot << EOF

# Install dependencies
apt-get install -y \
    python3-pip \
    python3-pygame \
    python3-pil \
    python3-rpi.gpio \
    alsa-utils \
    git

# Clone PiPlayer
cd /home/piplayer
git clone https://github.com/GOT-A-AK47/PiPlayer.git
chown -R piplayer:piplayer PiPlayer

cd PiPlayer
pip3 install -r requirements.txt

# Create directories
mkdir -p music playlists logs

# Configure for pHAT DAC
cat >> /boot/config.txt << 'BOOTCONF'
# PiPlayer Audio Configuration
dtparam=audio=off
dtoverlay=hifiberry-dac
gpio_pin=25
BOOTCONF

# ALSA config
cat > /home/piplayer/.asoundrc << 'ALSA'
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
ALSA

chown piplayer:piplayer /home/piplayer/.asoundrc

# Systemd service
cat > /etc/systemd/system/piplayer.service << 'SERVICE'
[Unit]
Description=PiPlayer Music Player
After=sound.target

[Service]
Type=simple
User=piplayer
WorkingDirectory=/home/piplayer/PiPlayer
ExecStart=/usr/bin/python3 /home/piplayer/PiPlayer/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Don't enable by default - let user choose
# systemctl enable piplayer

EOF

SCRIPT

chmod +x stage-piplayer/00-install-piplayer/00-run.sh
```

### Build Image

```bash
sudo ./build.sh

# Image wordt gegenereerd in deploy/
```

## Optie 3: Modify Bestaande Image

Snellere methode - pas bestaande image aan:

### Setup

```bash
# Download Raspbian Lite
wget https://downloads.raspberrypi.org/raspios_lite_armhf_latest

# Extract
unzip *raspios_lite*.zip

# Mount
sudo kpartx -av *.img
# Dit geeft bijv. /dev/mapper/loop0p1 en loop0p2

sudo mount /dev/mapper/loop0p2 /mnt
sudo mount /dev/mapper/loop0p1 /mnt/boot
```

### Installeer PiPlayer

```bash
# Chroot
sudo mount --bind /dev /mnt/dev
sudo mount --bind /dev/pts /mnt/dev/pts
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys

# Enable QEMU (als je op x86 machine bent)
sudo cp /usr/bin/qemu-arm-static /mnt/usr/bin/

# Chroot
sudo chroot /mnt /bin/bash

# Now in Pi filesystem
cd /home/pi

# Install system packages
apt-get update
apt-get install -y python3-pip python3-pygame python3-pil python3-rpi.gpio alsa-utils git

# Clone PiPlayer
git clone https://github.com/GOT-A-AK47/PiPlayer.git
cd PiPlayer
pip3 install -r requirements.txt

# Configure audio
echo "dtparam=audio=off" >> /boot/config.txt
echo "dtoverlay=hifiberry-dac" >> /boot/config.txt

# Exit chroot
exit

# Cleanup
sudo umount /mnt/boot /mnt/dev/pts /mnt/dev /mnt/proc /mnt/sys /mnt
sudo kpartx -dv *.img
```

### Shrink Image

```bash
# Install pishrink
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
chmod +x pishrink.sh

# Shrink
sudo ./pishrink.sh raspios.img piplayer.img

# Compress
zip piplayer-pizero-$(date +%Y%m%d).zip piplayer.img
```

## Pre-configured Image Specificaties

### Included Features
- PiPlayer (latest)
- All Python dependencies
- pHAT DAC drivers configured
- ST7789 display support
- GPIO button handlers
- ALSA configured for I2S DAC

### Default Config
```json
{
  "display": {"driver": "st7789"},
  "audio": {"buffer_size": 8192},
  "buttons": {"enabled": true}
}
```

### Default Credentials
- **Username**: `piplayer`
- **Password**: `piplayer123`
- **Hostname**: `piplayer.local`

⚠️ **Change password on first boot!**

### Services
- `piplayer.service` - Auto-start player (disabled by default)

### Helper Scripts
- `~/PiPlayer/start.sh` - Start player
- `~/PiPlayer/scan.sh` - Scan music library

## First Boot Customization

Create `/boot/firstboot.sh`:

```bash
#!/bin/bash

# Expand filesystem
raspi-config --expand-rootfs

# Force password change
chage -d 0 piplayer

# Update system
apt-get update && apt-get upgrade -y

# Regenerate SSH keys
rm -f /etc/ssh/ssh_host_*
dpkg-reconfigure openssh-server

# Remove firstboot script
rm /boot/firstboot.sh
systemctl disable firstboot

# Reboot
reboot
```

Enable as service:
```ini
[Unit]
Description=First Boot Setup
After=network.target

[Service]
Type=oneshot
ExecStart=/boot/firstboot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

## Hardware Detection Script

Automatisch detecteer welke HAT is aangesloten:

```bash
#!/bin/bash
# ~/PiPlayer/detect_hardware.sh

# Check voor pHAT DAC
if lsmod | grep -q "snd_soc_hifiberry_dac"; then
    echo "Detected: pHAT DAC"
    # Configure for pHAT DAC
fi

# Check voor ST7789 display
if [ -e "/dev/spidev0.1" ]; then
    echo "Detected: ST7789 Display"
    # Configure for ST7789
fi

# Update config.json accordingly
python3 -c "import json; ..."
```

## User Guide voor Pre-made Image

### Installation

1. **Download** `piplayer-pizero-YYYYMMDD.zip`
2. **Extract** de .img file
3. **Flash** naar SD kaart (min 8GB) met Raspberry Pi Imager
4. **Insert** SD kaart in Pi Zero v1.3
5. **Connect** DAC HAT (pHAT DAC of DAC Line-out LCD HAT)
6. **Boot** - eerste boot duurt 2-3 minuten

### First Login

```bash
# SSH (als enabled)
ssh piplayer@piplayer.local
# Password: piplayer123

# Change password
passwd

# Check hardware detection
~/PiPlayer/detect_hardware.sh
```

### Add Music

```bash
# Via USB stick
sudo mount /dev/sda1 /mnt
cp /mnt/*.mp3 ~/PiPlayer/music/

# Via SCP from PC
scp /path/to/music/*.mp3 piplayer@piplayer.local:~/PiPlayer/music/

# Scan library
~/PiPlayer/scan.sh
```

### Start Playing

```bash
# Manual start
~/PiPlayer/start.sh

# Auto-start on boot
sudo systemctl enable piplayer
sudo systemctl start piplayer
```

## Testing Image

Before distribution:

```bash
# Test in QEMU
qemu-system-arm \
  -M versatilepb \
  -cpu arm1176 \
  -m 256 \
  -hda piplayer.img \
  -kernel kernel-qemu \
  -append "root=/dev/sda2"

# Or test on actual Pi Zero
```

## Distribution Checklist

- [ ] Test all features werken
- [ ] SSH keys verwijderd/regenerated
- [ ] Default password gedocumenteerd
- [ ] Image geshrinked
- [ ] Gecompressed (zip/xz)
- [ ] SHA256 checksum aangemaakt
- [ ] README included
- [ ] License file included

## Image Size

- Base Raspbian Lite: ~2GB
- With PiPlayer: ~2.5GB
- After shrink: ~1.8GB
- Compressed: ~650MB

## Legal & Credits

- Raspberry Pi OS: Raspberry Pi Foundation
- PiPlayer: MIT License
- Pimoroni Libraries: Pimoroni Ltd

Educational project - for personal use only.
