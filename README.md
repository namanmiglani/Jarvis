# Jarvis AI Assistant

A futuristic voice-activated AI assistant with Iron Man-style HUD overlay.

## Features

- 🎤 **Wake Word Detection**: Activate with "Hey Jarvis"
- 🗣️ **Voice Activity Detection**: Automatically detects when you stop speaking
- 🧠 **LangChain + LangGraph**: Intelligent intent classification and tool orchestration
- 🌡️ **Weather Tool**: Real-time weather information
- 🎨 **Futuristic HUD**: Iron Man-style overlay with animated widgets
- 💬 **Multi-turn Conversations**: Natural conversation flow with context awareness

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Required API Keys:**
   - `OPENAI_API_KEY`: For TTS (Text-to-Speech)
   - `OPENROUTER_API_KEY`: For LLM (Gemini via OpenRouter)
   - `WEATHER_API_KEY`: For weather data (WeatherAPI.com)

## Usage

### Run Backend (Jarvis Agent)

```bash
python main.py
```

### Run Frontend (HUD Overlay)

In a separate terminal:

```bash
python hud.py
```

## Controls

**HUD Controls:**

- `ESC` or `Q`: Exit HUD

**Voice Commands:**

- "Hey Jarvis" - Activate
- "What's the weather in [city]?" - Get weather
- Ask any general question
- Natural conversation with followup questions

## Project Structure

```
Jarvis/
├── main.py                 # Backend entry point
├── hud.py                  # HUD overlay entry point
├── requirements.txt        # All dependencies
├── .env                    # API keys (create from .env.example)
├── agents/                 # Backend agents
│   ├── audio/             # Audio I/O (STT, TTS, wake word)
│   ├── reasoning/         # Intent classification & LLM
│   ├── memory/            # Conversation history
│   ├── tools/             # Weather and other tools
│   ├── graph/             # LangGraph workflow
│   ├── orchestrator/      # Main orchestration
│   └── hud_server.py      # WebSocket server for HUD
└── frontend/              # HUD components
    ├── widgets/           # Weather, voice widgets
    ├── graphics/          # Drawing utilities
    ├── animations/        # Animation system
    └── backend_client.py  # WebSocket client
```

## Architecture

- **Backend**: Python async with LangChain/LangGraph
- **Frontend**: PyQt5 with OpenCV for camera feed
- **Communication**: WebSocket for real-time state sync
- **LLM**: Gemini via OpenRouter
- **STT**: OpenAI Whisper (local)
- **TTS**: OpenAI TTS
- **Wake Word**: OpenWakeWord (local, no API needed)

## Technologies

- LangChain & LangGraph for agent orchestration
- OpenAI Whisper for speech-to-text
- OpenAI TTS for text-to-speech
- OpenWakeWord for wake word detection
- WebRTC VAD for voice activity detection
- PyQt5 for HUD interface
- WebSocket for real-time communication
