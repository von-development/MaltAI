from fastapi import WebSocket, UploadFile, File
from .websocket import ConnectionManager
from . import app
from .services.agent_service import agent_service
from maltai_agent.audio import process_audio
import logging

manager = ConnectionManager()
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process the received data through agent
            async for response in agent_service.process_message(data):
                await manager.broadcast({
                    "type": "message",
                    "data": response
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file using Whisper."""
    try:
        contents = await audio.read()
        text = await process_audio(contents)
        return {"text": text}
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {"error": str(e)} 