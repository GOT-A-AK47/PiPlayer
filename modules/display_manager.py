"""
Display Manager Module
Modular display management supporting various Pimoroni HATs.
"""

import logging
import time
from typing import Optional


class DisplayManager:
    """Manages display output with support for multiple HAT types"""

    def __init__(self, config, audio_player):
        self.config = config
        self.audio_player = audio_player
        self.logger = logging.getLogger(__name__)

        self.enabled = config.get('display.enabled', True)
        if not self.enabled:
            self.logger.info("Display disabled in config")
            return

        # Determine which display driver to use
        driver_name = config.get('display.driver', 'st7789')
        self.driver = self._load_driver(driver_name)

        if self.driver:
            self.logger.info(f"Display driver loaded: {driver_name}")
        else:
            self.logger.warning("No display driver loaded")

    def _load_driver(self, driver_name: str):
        """
        Load appropriate display driver

        Args:
            driver_name: Name of the driver to load

        Returns:
            Driver instance or None
        """
        try:
            if driver_name == 'st7789':
                from drivers.st7789_driver import ST7789Driver
                return ST7789Driver(self.config)
            elif driver_name == 'ssd1306':
                from drivers.ssd1306_driver import SSD1306Driver
                return SSD1306Driver(self.config)
            elif driver_name == 'console':
                from drivers.console_driver import ConsoleDriver
                return ConsoleDriver(self.config)
            else:
                self.logger.error(f"Unknown driver: {driver_name}")
                # Fallback to console driver
                from drivers.console_driver import ConsoleDriver
                return ConsoleDriver(self.config)

        except ImportError as e:
            self.logger.error(f"Could not import driver {driver_name}: {e}")
            self.logger.info("Falling back to console driver")
            try:
                from drivers.console_driver import ConsoleDriver
                return ConsoleDriver(self.config)
            except:
                return None
        except Exception as e:
            self.logger.error(f"Error loading driver: {e}", exc_info=True)
            return None

    def start(self):
        """Initialize display"""
        if not self.enabled or not self.driver:
            return

        try:
            self.driver.initialize()
            self.display_welcome()
        except Exception as e:
            self.logger.error(f"Error starting display: {e}")

    def update(self):
        """Update display with current player state"""
        if not self.enabled or not self.driver:
            return

        try:
            track_info = self.audio_player.get_current_track_info()
            self.driver.update(track_info)
        except Exception as e:
            self.logger.debug(f"Error updating display: {e}")

    def display_welcome(self):
        """Show welcome screen"""
        if not self.driver:
            return

        try:
            self.driver.show_message("PiPlayer", "Ready")
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"Error showing welcome: {e}")

    def show_message(self, title: str, message: str, duration: float = 2.0):
        """
        Display a temporary message

        Args:
            title: Message title
            message: Message text
            duration: How long to show (seconds)
        """
        if not self.driver:
            return

        try:
            self.driver.show_message(title, message)
            if duration > 0:
                time.sleep(duration)
        except Exception as e:
            self.logger.error(f"Error showing message: {e}")

    def stop(self):
        """Cleanup display"""
        if not self.enabled or not self.driver:
            return

        try:
            self.driver.cleanup()
        except Exception as e:
            self.logger.error(f"Error stopping display: {e}")
