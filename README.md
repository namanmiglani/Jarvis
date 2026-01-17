# Jarvis AI Assistant

> A voice-activated AI assistant with calendar management, live translation, and weather queries using a multiagent architecture.

## 🎯 Features

- **Wake Word Detection**: "Hey Jarvis" activation
- **Calendar Management**: Add/query Google Calendar events with intelligent follow-ups
- **Live Translation**: OCR text translation and speech-to-text translation
- **Weather Queries**: Current conditions and forecasts

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Google Cloud account (for Calendar, Translate, Vision APIs)
- OpenRouter account (for Gemini LLM)
- OpenWeatherMap account (for weather data)
- Porcupine account (for wake word detection)

### 2. Installation

```bash
# Clone the repository
cd /Users/harshamin/Desktop/Jarvis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 4. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable these APIs:
   - Google Calendar API
   - Cloud Translation API
   - Cloud Vision API
4. Create OAuth 2.0 credentials for Calendar
5. Download credentials and save to `config/google_calendar_credentials.json`

### 5. Get API Keys

- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai/)
- **OpenWeatherMap**: Sign up at [openweathermap.org](https://openweathermap.org/api)
- **Porcupine**: Sign up at [picovoice.ai](https://console.picovoice.ai/)

### 6. Run Jarvis

```bash
# Activate virtual environment
source venv/bin/activate

# Run the main application
python main.py
```

## 📁 Project Structure

```
Jarvis/
├── agents/
│   ├── orchestrator/      # Central coordinator
│   ├── audio/            # Wake word, STT, TTS
│   ├── vision/           # Screen capture, OCR
│   ├── reasoning/        # LLM, intent classification
│   ├── tool_executor/    # API integrations
│   └── memory/           # Conversation context
├── config/               # Configuration files
├── logs/                 # Application logs
├── data/                 # Local data storage
├── .env                  # Environment variables (not committed)
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── main.py              # Application entry point
└── README.md            # This file
```

## 🎤 Usage Examples

### Calendar Management

```
You: "Hey Jarvis, remind me to take my creatine"
Jarvis: "When would you like me to remind you?"
You: "Every day at 8 AM"
Jarvis: "Done. Daily reminder created."
```

### Translation

```
You: "Hey Jarvis, translate this text"
Jarvis: *captures screen* "I detected Spanish. The text says: 'Hello, how are you today?'"
```

### Weather

```
You: "Hey Jarvis, how's the weather?"
Jarvis: "It's currently 72°F and sunny in San Francisco."
```

## 🛠️ Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
pylint agents/
```

## 📊 Cost Estimates

With moderate usage (~1000 requests/month):

- OpenRouter (Gemini): ~$2-3/month
- Google Translate: ~$1-2/month
- Google Vision (OCR): ~$1/month
- OpenWeatherMap: Free tier
- Porcupine: Free tier

**Total: ~$5-10/month**

## 🔐 Privacy & Security

- All audio processing happens locally
- Screenshots are temporary and deleted after OCR
- API keys stored in `.env` (never committed)
- OAuth 2.0 for Google Calendar access
- Wake word required (no always-on listening)

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📚 Documentation

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for detailed architecture and implementation roadmap.

---

**Built with ❤️ using Python, Gemini, and a multiagent architecture**
