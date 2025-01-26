"""Test audio processing functionality."""

import pytest
from maltai_agent.audio import AudioProcessor

@pytest.mark.asyncio
async def test_audio_processor_initialization():
    """Test AudioProcessor initialization."""
    processor = AudioProcessor()
    assert processor.sample_rate == 44100
    assert processor._recording is False
    assert processor.voice_settings is not None 