import React from 'react';
import { ChatSession } from './components/ChatSession';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>MaltAI Assistant</h1>
      </header>
      <main>
        <ChatSession />
      </main>
    </div>
  );
}

export default App; 