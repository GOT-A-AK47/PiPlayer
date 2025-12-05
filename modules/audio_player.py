"""
Audio Player Module
Handles audio playback using pygame.mixer - lightweight and perfect for Pi Zero.
"""

import logging
import os
from enum import Enum
from typing import Optional

try:
    import pygame.mixer as mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class PlayerState(Enum):
    """Player state enumeration"""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class AudioPlayer:
    """Audio playback manager using pygame.mixer"""

    def __init__(self, config, playlist_manager):
        self.config = config
        self.playlist_manager = playlist_manager
        self.logger = logging.getLogger(__name__)

        if not PYGAME_AVAILABLE:
            self.logger.error("pygame not available. Install with: pip3 install pygame")
            return

        # Initialize pygame mixer
        try:
            mixer.init(
                frequency=self.config.get('audio.sample_rate', 44100),
                size=self.config.get('audio.bit_depth', -16),
                channels=self.config.get('audio.channels', 2),
                buffer=self.config.get('audio.buffer_size', 4096)
            )
            self.logger.info("Audio system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {e}")
            return

        # Player state
        self.state = PlayerState.STOPPED
        self.current_track = None
        self.volume = self.config.get('player.default_volume', 0.7)
        mixer.music.set_volume(self.volume)

        # Playback settings
        self.repeat_mode = self.config.get('player.repeat_mode', 'all')  # all, one, off
        self.shuffle = self.config.get('player.shuffle', False)

    def play(self, track_index: Optional[int] = None):
        """
        Start playback

        Args:
            track_index: Specific track index to play (None = continue current/start first)
        """
        if not PYGAME_AVAILABLE:
            return

        try:
            # Get track to play
            if track_index is not None:
                track = self.playlist_manager.get_track(track_index)
            elif self.current_track is None:
                track = self.playlist_manager.get_current_track()
            else:
                track = self.current_track

            if not track:
                self.logger.warning("No track to play")
                return

            # If paused, just unpause
            if self.state == PlayerState.PAUSED and track == self.current_track:
                mixer.music.unpause()
                self.state = PlayerState.PLAYING
                self.logger.info("Playback resumed")
                return

            # Load and play new track
            file_path = track.get('path')
            if not os.path.exists(file_path):
                self.logger.error(f"Track file not found: {file_path}")
                return

            mixer.music.load(file_path)
            mixer.music.play()

            self.current_track = track
            self.state = PlayerState.PLAYING

            self.logger.info(f"Now playing: {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}")

        except Exception as e:
            self.logger.error(f"Error playing track: {e}", exc_info=True)

    def pause(self):
        """Pause playback"""
        if not PYGAME_AVAILABLE or self.state != PlayerState.PLAYING:
            return

        try:
            mixer.music.pause()
            self.state = PlayerState.PAUSED
            self.logger.info("Playback paused")
        except Exception as e:
            self.logger.error(f"Error pausing: {e}")

    def stop(self):
        """Stop playback"""
        if not PYGAME_AVAILABLE:
            return

        try:
            mixer.music.stop()
            self.state = PlayerState.STOPPED
            self.logger.info("Playback stopped")
        except Exception as e:
            self.logger.error(f"Error stopping: {e}")

    def next(self):
        """Play next track"""
        if self.shuffle:
            next_track = self.playlist_manager.get_random_track()
            index = self.playlist_manager.tracks.index(next_track) if next_track else None
        else:
            index = self.playlist_manager.next()

        if index is not None:
            self.play(index)
        elif self.repeat_mode == 'all':
            # Loop back to start
            self.playlist_manager.current_index = 0
            self.play(0)
        else:
            self.stop()

    def previous(self):
        """Play previous track"""
        index = self.playlist_manager.previous()
        if index is not None:
            self.play(index)

    def seek(self, position: float):
        """
        Seek to position in current track

        Args:
            position: Position in seconds
        """
        if not PYGAME_AVAILABLE or self.state == PlayerState.STOPPED:
            return

        try:
            # pygame.mixer doesn't support seeking well
            # Alternative: restart track and skip forward
            mixer.music.set_pos(position)
            self.logger.debug(f"Seeked to {position}s")
        except Exception as e:
            self.logger.warning(f"Seeking not fully supported: {e}")

    def set_volume(self, volume: float):
        """
        Set playback volume

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if not PYGAME_AVAILABLE:
            return

        volume = max(0.0, min(1.0, volume))
        self.volume = volume
        mixer.music.set_volume(volume)
        self.logger.debug(f"Volume set to {volume:.2f}")

    def volume_up(self, step: float = 0.1):
        """Increase volume"""
        self.set_volume(self.volume + step)

    def volume_down(self, step: float = 0.1):
        """Decrease volume"""
        self.set_volume(self.volume - step)

    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if self.state == PlayerState.PLAYING:
            self.pause()
        elif self.state == PlayerState.PAUSED:
            self.play()
        else:
            self.play()

    def is_playing(self) -> bool:
        """Check if currently playing"""
        return self.state == PlayerState.PLAYING

    def is_paused(self) -> bool:
        """Check if paused"""
        return self.state == PlayerState.PAUSED

    def is_stopped(self) -> bool:
        """Check if stopped"""
        return self.state == PlayerState.STOPPED

    def has_ended(self) -> bool:
        """Check if current track has ended"""
        if not PYGAME_AVAILABLE or self.state != PlayerState.PLAYING:
            return False

        return not mixer.music.get_busy()

    def get_position(self) -> float:
        """
        Get current playback position

        Returns:
            Position in seconds (approximate with pygame)
        """
        if not PYGAME_AVAILABLE or self.state == PlayerState.STOPPED:
            return 0.0

        try:
            # pygame returns position in milliseconds
            pos = mixer.music.get_pos() / 1000.0
            return max(0.0, pos)
        except:
            return 0.0

    def get_current_track_info(self) -> dict:
        """
        Get information about current track

        Returns:
            Track information dictionary
        """
        if not self.current_track:
            return {
                'title': 'No track',
                'artist': '',
                'album': '',
                'duration': 0,
                'position': 0,
                'state': self.state.name
            }

        return {
            **self.current_track,
            'position': self.get_position(),
            'state': self.state.name,
            'volume': self.volume
        }

    def toggle_shuffle(self):
        """Toggle shuffle mode"""
        self.shuffle = not self.shuffle
        self.logger.info(f"Shuffle: {'ON' if self.shuffle else 'OFF'}")
        return self.shuffle

    def cycle_repeat_mode(self):
        """Cycle through repeat modes"""
        modes = ['off', 'all', 'one']
        current_index = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(current_index + 1) % len(modes)]
        self.logger.info(f"Repeat mode: {self.repeat_mode}")
        return self.repeat_mode
