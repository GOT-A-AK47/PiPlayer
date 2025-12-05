"""
ST7789 Display Driver
For Pimoroni displays using ST7789 chip (240x240 LCD).
Compatible with DAC Line-out LCD HAT and Display HAT Mini.
"""

import logging
from typing import Dict

try:
    from PIL import Image, ImageDraw, ImageFont
    import ST7789
    ST7789_AVAILABLE = True
except ImportError:
    ST7789_AVAILABLE = False


class ST7789Driver:
    """Driver for ST7789-based displays"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        if not ST7789_AVAILABLE:
            self.logger.error("ST7789 library not available. Install with: pip3 install st7789 pillow")
            raise ImportError("ST7789 library not available")

        self.width = config.get('display.width', 240)
        self.height = config.get('display.height', 240)
        self.rotation = config.get('display.rotation', 0)

        self.display = None
        self.image = None
        self.draw = None

        # Font settings
        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            self.logger.warning("Could not load TrueType fonts, using default")
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def initialize(self):
        """Initialize the display"""
        try:
            self.display = ST7789.ST7789(
                port=0,
                cs=1,
                dc=9,
                backlight=13,
                rotation=self.rotation,
                spi_speed_hz=80 * 1000 * 1000
            )

            self.display.begin()

            # Create image buffer
            self.image = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
            self.draw = ImageDraw.Draw(self.image)

            self.logger.info("ST7789 display initialized")

        except Exception as e:
            self.logger.error(f"Error initializing ST7789: {e}", exc_info=True)
            raise

    def update(self, track_info: Dict):
        """
        Update display with track information

        Args:
            track_info: Dictionary with track details
        """
        try:
            # Clear screen
            self.draw.rectangle((0, 0, self.width, self.height), fill=(10, 10, 30))

            # Get track info
            title = track_info.get('title', 'No Track')
            artist = track_info.get('artist', '')
            state = track_info.get('state', 'STOPPED')
            position = int(track_info.get('position', 0))
            duration = int(track_info.get('duration', 0))
            volume = int(track_info.get('volume', 0) * 100)

            y_pos = 10

            # Draw state icon
            state_color = (100, 255, 100) if state == 'PLAYING' else (255, 255, 100) if state == 'PAUSED' else (200, 200, 200)
            self.draw.text((10, y_pos), "▶" if state == 'PLAYING' else "⏸" if state == 'PAUSED' else "⏹",
                          fill=state_color, font=self.font_large)

            # Volume indicator
            self.draw.text((self.width - 60, y_pos), f"🔊{volume}%", fill=(200, 200, 200), font=self.font_small)

            y_pos += 40

            # Draw title (truncate if too long)
            title_display = self._truncate_text(title, 18)
            self.draw.text((10, y_pos), title_display, fill=(255, 255, 255), font=self.font_medium)

            y_pos += 30

            # Draw artist
            if artist:
                artist_display = self._truncate_text(artist, 22)
                self.draw.text((10, y_pos), artist_display, fill=(180, 180, 180), font=self.font_small)

            y_pos += 30

            # Draw progress bar
            if duration > 0:
                bar_width = self.width - 20
                bar_height = 10
                bar_x = 10
                bar_y = self.height - 60

                # Background
                self.draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height),
                                   fill=(50, 50, 50))

                # Progress
                progress = min(1.0, position / duration) if duration > 0 else 0
                fill_width = int(bar_width * progress)
                self.draw.rectangle((bar_x, bar_y, bar_x + fill_width, bar_y + bar_height),
                                   fill=(100, 150, 255))

                # Time labels
                time_text = f"{self._format_time(position)} / {self._format_time(duration)}"
                self.draw.text((bar_x, bar_y + bar_height + 5), time_text,
                             fill=(150, 150, 150), font=self.font_small)

            # Update display
            self.display.display(self.image)

        except Exception as e:
            self.logger.error(f"Error updating display: {e}")

    def show_message(self, title: str, message: str):
        """Show a simple message"""
        try:
            self.draw.rectangle((0, 0, self.width, self.height), fill=(10, 10, 30))

            # Center the text
            y_pos = self.height // 2 - 30

            self.draw.text((10, y_pos), title, fill=(255, 255, 255), font=self.font_large)
            self.draw.text((10, y_pos + 35), message, fill=(180, 180, 180), font=self.font_medium)

            self.display.display(self.image)

        except Exception as e:
            self.logger.error(f"Error showing message: {e}")

    def cleanup(self):
        """Cleanup display"""
        try:
            if self.display:
                # Clear to black
                self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
                self.display.display(self.image)
                self.logger.info("ST7789 display cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to fit display"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _format_time(self, seconds: int) -> str:
        """Format time as MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
