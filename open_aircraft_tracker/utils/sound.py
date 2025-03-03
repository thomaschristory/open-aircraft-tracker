"""
Sound alert functionality for aircraft tracking.
Uses simpleaudio to play sound alerts when aircraft enter the specified radius.
"""
import os
import threading
from pathlib import Path
from typing import Optional

import simpleaudio as sa


class SoundAlert:
    """Sound alert functionality for aircraft tracking."""
    
    # Default sound file (a simple beep)
    DEFAULT_SOUND_DATA = bytes([
        # WAV header (44 bytes)
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # Chunk size (36 + data size)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Subchunk1 size (16 bytes)
        0x01, 0x00,              # Audio format (1 = PCM)
        0x01, 0x00,              # Number of channels (1 = mono)
        0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100 Hz)
        0x44, 0xAC, 0x00, 0x00,  # Byte rate (44100 * 1 * 1)
        0x01, 0x00,              # Block align (1 * 1)
        0x08, 0x00,              # Bits per sample (8)
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Subchunk2 size (data size)
        
        # Simple beep sound data (sine wave)
        # This is just a placeholder and will be replaced with actual sound data
    ])
    
    def __init__(self, sound_file: Optional[str] = None):
        """
        Initialize the sound alert.
        
        Args:
            sound_file: Path to a WAV file to use for alerts (optional)
        """
        self.sound_file = sound_file
        self.play_obj = None
        self.lock = threading.Lock()
        
        # Generate a simple beep sound if no sound file is provided
        if not sound_file:
            # Create a simple sine wave beep
            sample_rate = 44100
            duration = 0.5  # seconds
            frequency = 1000  # Hz
            
            # Generate sine wave
            import math
            import array
            
            samples = []
            for i in range(int(duration * sample_rate)):
                sample = int(127 + 127 * math.sin(2 * math.pi * frequency * i / sample_rate))
                samples.append(sample)
            
            # Convert to bytes
            audio_data = array.array('B', samples).tobytes()
            
            # Update WAV header with correct data size
            data_size = len(audio_data)
            chunk_size = 36 + data_size
            
            # Create WAV file with correct header
            header = bytearray(self.DEFAULT_SOUND_DATA[:44])
            
            # Update chunk size (bytes 4-7)
            header[4:8] = chunk_size.to_bytes(4, byteorder='little')
            
            # Update data size (bytes 40-43)
            header[40:44] = data_size.to_bytes(4, byteorder='little')
            
            # Combine header and audio data
            self.sound_data = bytes(header) + audio_data
        else:
            # Load sound file
            if not os.path.exists(sound_file):
                raise FileNotFoundError(f"Sound file not found: {sound_file}")
            
            with open(sound_file, 'rb') as f:
                self.sound_data = f.read()
    
    def play(self):
        """Play the sound alert."""
        with self.lock:
            # Stop any currently playing sound
            if self.play_obj and self.play_obj.is_playing():
                self.play_obj.stop()
            
            # Play the sound
            self.play_obj = sa.play_buffer(
                self.sound_data,
                num_channels=1,
                bytes_per_sample=1,
                sample_rate=44100
            )
    
    def stop(self):
        """Stop the sound alert if it's playing."""
        with self.lock:
            if self.play_obj and self.play_obj.is_playing():
                self.play_obj.stop()
