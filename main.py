#!/usr/bin/env python3
"""
PiPlayer - Raspberry Pi MP3 Player
A modular music player for Raspberry Pi with support for various DAC HATs and displays.
"""

import logging
import signal
import sys
import time
from threading import Thread

from modules.audio_player import AudioPlayer
from modules.playlist_manager import PlaylistManager
from modules.display_manager import DisplayManager
from modules.button_handler import ButtonHandler
from modules.config_loader import Config


class PiPlayer:
    """Main PiPlayer application"""

    def __init__(self, config_file='config.json'):
        self.config = Config(config_file)
        self.running = False

        # Setup logging
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.get('log_file', 'logs/piplayer.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Initialize modules
        self.logger.info("Initializing PiPlayer...")
        self.playlist_manager = PlaylistManager(self.config)
        self.audio_player = AudioPlayer(self.config, self.playlist_manager)
        self.display_manager = DisplayManager(self.config, self.audio_player)
        self.button_handler = ButtonHandler(self.config, self.audio_player, self.display_manager)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("PiPlayer initialized successfully")

    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("Shutdown signal received")
        self.stop()
        sys.exit(0)

    def start(self):
        """Start the player"""
        self.logger.info("Starting PiPlayer...")
        self.running = True

        # Load default playlist or last played
        last_playlist = self.config.get('player.last_playlist')
        if last_playlist:
            self.playlist_manager.load_playlist(last_playlist)
        else:
            # Load all music if no playlist
            self.playlist_manager.scan_music_directory()

        # Start display
        self.display_manager.start()

        # Start button handler
        self.button_handler.start()

        # Auto-start playback if configured
        if self.config.get('player.auto_start', False):
            self.audio_player.play()

        # Main loop
        self._main_loop()

    def _main_loop(self):
        """Main application loop"""
        try:
            while self.running:
                # Update display
                self.display_manager.update()

                # Check audio player state
                if self.audio_player.is_playing():
                    # Update progress, check if song ended, etc.
                    if self.audio_player.has_ended():
                        self.audio_player.next()

                # Small sleep to prevent CPU spinning
                time.sleep(0.1)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop the player and cleanup"""
        if not self.running:
            return

        self.logger.info("Stopping PiPlayer...")
        self.running = False

        # Save current state
        if self.playlist_manager.current_playlist:
            self.config.set('player.last_playlist', self.playlist_manager.current_playlist)
            self.config.save()

        # Stop modules
        self.audio_player.stop()
        self.button_handler.stop()
        self.display_manager.stop()

        self.logger.info("PiPlayer stopped")


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════╗
    ║         PiPlayer v1.0.0          ║
    ║    Raspberry Pi Music Player      ║
    ╚═══════════════════════════════════╝
    """
    print(banner)


def main():
    print_banner()

    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='PiPlayer - Raspberry Pi Music Player')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to configuration file')
    parser.add_argument('--scan', action='store_true',
                       help='Scan music directory and exit')
    parser.add_argument('--list-playlists', action='store_true',
                       help='List all playlists and exit')

    args = parser.parse_args()

    # Create player instance
    player = PiPlayer(args.config)

    # Handle special commands
    if args.scan:
        print("Scanning music directory...")
        player.playlist_manager.scan_music_directory()
        print(f"Found {len(player.playlist_manager.tracks)} tracks")
        return

    if args.list_playlists:
        playlists = player.playlist_manager.list_playlists()
        print("Available playlists:")
        for pl in playlists:
            print(f"  - {pl}")
        return

    # Start player
    player.start()


if __name__ == "__main__":
    main()
