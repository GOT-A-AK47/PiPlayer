"""
Playlist Manager Module
Manages music library, playlists, and track metadata.
"""

import logging
import os
import json
import random
from pathlib import Path
from typing import List, Dict, Optional

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class PlaylistManager:
    """Manages music library and playlists"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.music_dir = config.get('music.directory', 'music')
        self.playlist_dir = config.get('music.playlist_directory', 'playlists')

        # Create directories if they don't exist
        os.makedirs(self.music_dir, exist_ok=True)
        os.makedirs(self.playlist_dir, exist_ok=True)

        # Track storage
        self.tracks = []
        self.current_index = 0
        self.current_playlist = None

        self.logger.info("Playlist manager initialized")

    def scan_music_directory(self) -> int:
        """
        Scan music directory for audio files

        Returns:
            Number of tracks found
        """
        self.logger.info(f"Scanning music directory: {self.music_dir}")
        self.tracks = []

        supported_formats = self.config.get('music.supported_formats', ['.mp3', '.ogg', '.wav', '.flac'])

        for root, dirs, files in os.walk(self.music_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                if file_ext in supported_formats:
                    track_info = self._extract_metadata(file_path)
                    if track_info:
                        self.tracks.append(track_info)

        self.tracks.sort(key=lambda x: (x.get('artist', ''), x.get('album', ''), x.get('track_num', 0)))
        self.logger.info(f"Found {len(self.tracks)} tracks")

        return len(self.tracks)

    def _extract_metadata(self, file_path: str) -> Optional[Dict]:
        """
        Extract metadata from audio file

        Args:
            file_path: Path to audio file

        Returns:
            Track information dictionary
        """
        try:
            track_info = {
                'path': file_path,
                'filename': os.path.basename(file_path),
                'title': os.path.splitext(os.path.basename(file_path))[0],
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
                'track_num': 0,
                'duration': 0
            }

            if MUTAGEN_AVAILABLE:
                try:
                    audio = MutagenFile(file_path, easy=True)

                    if audio is not None:
                        # Extract metadata
                        if 'title' in audio:
                            track_info['title'] = audio['title'][0]
                        if 'artist' in audio:
                            track_info['artist'] = audio['artist'][0]
                        if 'album' in audio:
                            track_info['album'] = audio['album'][0]
                        if 'tracknumber' in audio:
                            try:
                                track_info['track_num'] = int(str(audio['tracknumber'][0]).split('/')[0])
                            except:
                                pass

                        # Get duration
                        if hasattr(audio.info, 'length'):
                            track_info['duration'] = int(audio.info.length)

                except Exception as e:
                    self.logger.debug(f"Could not read metadata for {file_path}: {e}")

            return track_info

        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return None

    def get_track(self, index: int) -> Optional[Dict]:
        """Get track by index"""
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None

    def get_current_track(self) -> Optional[Dict]:
        """Get currently selected track"""
        return self.get_track(self.current_index)

    def next(self) -> Optional[int]:
        """Move to next track"""
        if not self.tracks:
            return None

        self.current_index = (self.current_index + 1) % len(self.tracks)
        return self.current_index

    def previous(self) -> Optional[int]:
        """Move to previous track"""
        if not self.tracks:
            return None

        self.current_index = (self.current_index - 1) % len(self.tracks)
        return self.current_index

    def get_random_track(self) -> Optional[Dict]:
        """Get a random track"""
        if not self.tracks:
            return None

        return random.choice(self.tracks)

    def create_playlist(self, name: str, track_indices: List[int]) -> bool:
        """
        Create a new playlist

        Args:
            name: Playlist name
            track_indices: List of track indices

        Returns:
            True if successful
        """
        try:
            playlist_file = os.path.join(self.playlist_dir, f"{name}.json")

            playlist_tracks = []
            for index in track_indices:
                track = self.get_track(index)
                if track:
                    playlist_tracks.append({
                        'path': track['path'],
                        'title': track['title'],
                        'artist': track['artist']
                    })

            playlist_data = {
                'name': name,
                'tracks': playlist_tracks,
                'created': str(Path(playlist_file).stat().st_mtime if os.path.exists(playlist_file) else 0)
            }

            with open(playlist_file, 'w') as f:
                json.dump(playlist_data, f, indent=2)

            self.logger.info(f"Playlist '{name}' created with {len(playlist_tracks)} tracks")
            return True

        except Exception as e:
            self.logger.error(f"Error creating playlist: {e}")
            return False

    def load_playlist(self, name: str) -> bool:
        """
        Load a playlist

        Args:
            name: Playlist name

        Returns:
            True if successful
        """
        try:
            playlist_file = os.path.join(self.playlist_dir, f"{name}.json")

            if not os.path.exists(playlist_file):
                self.logger.warning(f"Playlist not found: {name}")
                return False

            with open(playlist_file, 'r') as f:
                playlist_data = json.load(f)

            # Load tracks from playlist
            self.tracks = []
            for track_data in playlist_data.get('tracks', []):
                if os.path.exists(track_data['path']):
                    # Re-extract full metadata
                    track_info = self._extract_metadata(track_data['path'])
                    if track_info:
                        self.tracks.append(track_info)

            self.current_playlist = name
            self.current_index = 0

            self.logger.info(f"Loaded playlist '{name}' with {len(self.tracks)} tracks")
            return True

        except Exception as e:
            self.logger.error(f"Error loading playlist: {e}")
            return False

    def list_playlists(self) -> List[str]:
        """
        List all available playlists

        Returns:
            List of playlist names
        """
        playlists = []

        try:
            for file in os.listdir(self.playlist_dir):
                if file.endswith('.json'):
                    playlists.append(os.path.splitext(file)[0])
        except Exception as e:
            self.logger.error(f"Error listing playlists: {e}")

        return sorted(playlists)

    def delete_playlist(self, name: str) -> bool:
        """Delete a playlist"""
        try:
            playlist_file = os.path.join(self.playlist_dir, f"{name}.json")

            if os.path.exists(playlist_file):
                os.remove(playlist_file)
                self.logger.info(f"Playlist '{name}' deleted")
                return True
            else:
                self.logger.warning(f"Playlist not found: {name}")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting playlist: {e}")
            return False

    def search_tracks(self, query: str) -> List[Dict]:
        """
        Search tracks by title, artist, or album

        Args:
            query: Search query

        Returns:
            List of matching tracks
        """
        query = query.lower()
        results = []

        for track in self.tracks:
            if (query in track.get('title', '').lower() or
                query in track.get('artist', '').lower() or
                query in track.get('album', '').lower()):
                results.append(track)

        return results

    def get_track_count(self) -> int:
        """Get total number of tracks"""
        return len(self.tracks)

    def get_artists(self) -> List[str]:
        """Get list of all artists"""
        artists = set()
        for track in self.tracks:
            artists.add(track.get('artist', 'Unknown Artist'))
        return sorted(list(artists))

    def get_albums(self) -> List[str]:
        """Get list of all albums"""
        albums = set()
        for track in self.tracks:
            albums.add(track.get('album', 'Unknown Album'))
        return sorted(list(albums))

    def get_tracks_by_artist(self, artist: str) -> List[Dict]:
        """Get all tracks by an artist"""
        return [track for track in self.tracks if track.get('artist') == artist]

    def get_tracks_by_album(self, album: str) -> List[Dict]:
        """Get all tracks from an album"""
        return [track for track in self.tracks if track.get('album') == album]
