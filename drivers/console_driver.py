"""
Console Display Driver
Fallback driver that outputs to console - useful for testing without hardware.
"""

import logging
import os
from typing import Dict


class ConsoleDriver:
    """Simple console-based display driver for testing"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_output = ""

    def initialize(self):
        """Initialize console display"""
        self.logger.info("Console driver initialized")
        print("\n" + "="*60)
        print("  PiPlayer Console Mode")
        print("  (No hardware display detected)")
        print("="*60 + "\n")

    def update(self, track_info: Dict):
        """Display track info in console"""
        try:
            # Build display output
            title = track_info.get('title', 'No Track')
            artist = track_info.get('artist', 'Unknown Artist')
            album = track_info.get('album', '')
            state = track_info.get('state', 'STOPPED')
            position = int(track_info.get('position', 0))
            duration = int(track_info.get('duration', 0))
            volume = int(track_info.get('volume', 0) * 100)

            # Create progress bar
            bar_length = 40
            if duration > 0:
                progress = min(1.0, position / duration)
                filled = int(bar_length * progress)
                bar = "█" * filled + "░" * (bar_length - filled)
            else:
                bar = "░" * bar_length

            # Format output
            output = f"""
╔════════════════════════════════════════════════════════════╗
║  {state:<12} Volume: {volume:>3}%                          ║
╠════════════════════════════════════════════════════════════╣
║  Title:  {title[:48]:<48} ║
║  Artist: {artist[:48]:<48} ║
║  Album:  {album[:48]:<48} ║
╠════════════════════════════════════════════════════════════╣
║  [{bar}] ║
║  {self._format_time(position)} / {self._format_time(duration):<48} ║
╚════════════════════════════════════════════════════════════╝
"""

            # Only print if changed (reduce console spam)
            if output != self.last_output:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(output)
                self.last_output = output

        except Exception as e:
            self.logger.error(f"Error updating console: {e}")

    def show_message(self, title: str, message: str):
        """Show a message in console"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"  {message}")
        print(f"{'='*60}\n")

    def cleanup(self):
        """Cleanup console"""
        print("\n" + "="*60)
        print("  PiPlayer Stopped")
        print("="*60 + "\n")

    def _format_time(self, seconds: int) -> str:
        """Format time as MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
