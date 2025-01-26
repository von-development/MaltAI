"""Audio input and output functionality for the agent."""

import io
import threading
from typing import List
import os

import numpy as np
import sounddevice as sd
from elevenlabs import play, VoiceSettings
from elevenlabs.client import ElevenLabs
from langchain_core.messages import HumanMessage
from scipy.io.wavfile import write
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI()
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

class AudioProcessor:
    """Handles audio input and output for the agent."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize audio processor.
        
        Args:
            sample_rate: Sample rate for audio recording
        """
        self.sample_rate = sample_rate
        self._recording = False
        self.voice_settings = VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True
        )
        
    def record_audio(self) -> HumanMessage:
        """Record audio from microphone until user presses Enter.
        
        Returns:
            HumanMessage containing transcribed text
        """
        print("Recording your instruction! ... Press Enter to stop recording.")
        
        audio_data: List[np.ndarray] = []
        self._recording = True

        def record_callback():
            """Record audio in chunks."""
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
                while self._recording:
                    audio_chunk, _ = stream.read(1024)
                    audio_data.append(audio_chunk)

        def stop_recording():
            """Wait for Enter key to stop recording."""
            input()
            self._recording = False

        # Start recording threads
        recording_thread = threading.Thread(target=record_callback)
        stop_thread = threading.Thread(target=stop_recording)
        
        recording_thread.start()
        stop_thread.start()
        
        # Wait for completion
        stop_thread.join()
        recording_thread.join()

        # Process recorded audio
        audio_array = np.concatenate(audio_data, axis=0)
        audio_bytes = io.BytesIO()
        write(audio_bytes, self.sample_rate, audio_array)
        audio_bytes.seek(0)
        audio_bytes.name = "audio.wav"

        # Transcribe with Whisper
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_bytes
        )

        print(f"Transcribed: {transcription.text}")
        return HumanMessage(content=transcription.text)

    def speak_response(self, text: str):
        """Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
        """
        # Clean text of markdown formatting
        cleaned_text = text.replace("**", "")
        
        # Generate speech using ElevenLabs client
        audio = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
            output_format="mp3_22050_32",
            text=cleaned_text,
            model_id="eleven_turbo_v2_5",
            voice_settings=self.voice_settings
        )
        
        # Play audio response
        play(audio) 