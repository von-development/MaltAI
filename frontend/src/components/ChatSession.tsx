import React, { useState, useEffect, useRef } from 'react';
import { AudioVisualizer } from './AudioVisualizer';
import { audioService } from '../services/audioService';

export const ChatSession: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<Array<{type: 'user' | 'agent', content: string}>>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    ws.current = new WebSocket('ws://localhost:8000/ws');
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, { type: 'agent', content: data.data }]);
      }
    };

    // Setup audio service
    audioService.setupMediaRecorder().catch(console.error);

    return () => {
      ws.current?.close();
    };
  }, []);

  const toggleListening = async () => {
    if (!isListening) {
      // Start recording
      setIsListening(true);
      audioService.startRecording();
    } else {
      // Stop recording and send audio
      setIsListening(false);
      const audioBlob = await audioService.stopRecording();
      
      // Send audio to backend
      const formData = new FormData();
      formData.append('audio', audioBlob);
      
      try {
        const response = await fetch('http://localhost:8000/transcribe', {
          method: 'POST',
          body: formData
        });
        
        const transcription = await response.json();
        setMessages(prev => [...prev, { type: 'user', content: transcription.text }]);
        
        // Send transcribed text to WebSocket
        ws.current?.send(transcription.text);
      } catch (error) {
        console.error('Error processing audio:', error);
      }
    }
  };

  return (
    <div className="chat-session">
      <div className="visualizer-container">
        <AudioVisualizer isListening={isListening} />
        <button onClick={toggleListening}>
          {isListening ? 'Stop' : 'Start'} Listening
        </button>
      </div>
      
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            {msg.content}
          </div>
        ))}
      </div>
    </div>
  );
}; 