# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube Transcript Processor application with a React frontend and Flask backend that processes YouTube video transcripts using AI and generates audio narration. The application follows a microservices architecture with clear separation between the frontend (port 5173), backend API (port 5001), and processing pipeline components.

## Essential Commands

### Development
```bash
# Start the application (preferred method)
make start

# Stop the application
make stop

# Restart services
make restart

# Check service status
make status

# View logs
make logs SERVICE=frontend  # Frontend logs
make logs SERVICE=backend   # Backend logs

# Clean start (stops services, kills ports, starts fresh)
make clean-start
```

### Alternative startup methods
```bash
# Using startup script
./startup.sh                # Background mode
./foreground_startup.sh     # Foreground mode with live logs

# Manual startup
cd app && source .venv/bin/activate && python main.py  # Backend
cd frontend && npm run dev                              # Frontend
```

### Frontend development
```bash
cd frontend
npm install        # Install dependencies
npm run dev        # Start development server
npm run build      # Build for production
npm run lint       # Run ESLint
```

### Backend development
```bash
cd app
python -m venv .venv                    # Create virtual environment
source .venv/bin/activate               # Activate (macOS/Linux)
pip install -r requirements.txt         # Install dependencies
python main.py                          # Run Flask server
```

## High-Level Architecture

### System Components

1. **Frontend (React + Vite)**
   - Port: 5173
   - Feature-based organization: transcript, config, downloads
   - UI components: shadcn/ui with Radix UI primitives
   - State management: React Context API + TanStack Query
   - Routing: React Router v7

2. **Backend (Flask)**
   - Port: 5001 (not 5000 due to macOS conflicts)
   - RESTful API with CORS enabled
   - Endpoints grouped by feature: transcripts, prompts, projects, config
   - Processing pipeline integration

3. **Processing Pipeline**
   - **Fetcher Module**: YouTube transcript retrieval
   - **AI Processor Module**: Multi-provider AI processing (OpenAI, Gemini, Claude, DeepSeek)
   - **TTS Module**: Kokoro TTS for audio generation
   - **Storage**: File-based with structured directories

### Data Flow
```
User Input → Frontend → Flask API → Processing Pipeline → External Services
    ↓            ↓          ↓              ↓                    ↓
UI Event → State/Context → HTTP → youtube_to_audio() → AI/TTS APIs
    ↓            ↓          ↓              ↓                    ↓
Re-render ← State Update ← JSON ← Processed Files ← Service Response
```

### Key Design Patterns

1. **Pipeline Pattern**: Sequential processing stages in `youtube_to_audio()`
2. **Provider Pattern**: Unified AI interface via LiteLLM
3. **Context Pattern**: Feature-specific state management
4. **Service Layer**: Centralized API communication in frontend
5. **Configuration-Driven**: YAML-based configuration system

## Important Files and Locations

### Configuration
- `app/config/config.yaml` - Main configuration file
- `.env` - API keys and environment variables
- `Makefile` - Development commands and automation

### Core Processing
- `app/main.py` - Flask application and API routes
- `app/scripts/youtube_to_audio.py` - Main processing pipeline
- `app/src/transcript_pipeline/` - Processing modules

### Frontend Entry Points
- `frontend/src/main.jsx` - Application entry
- `frontend/src/App.jsx` - Main application component
- `frontend/src/core/router.jsx` - Route definitions

### Data Storage
- `app/data/transcripts/` - Processed transcript projects
- `app/data/stored_prompts/` - Saved prompt templates

## API Endpoints

### Transcript Processing
- `POST /api/transcripts/process` - Process YouTube video
- `GET /api/transcripts` - List transcripts (mock data)

### Prompt Management
- `POST /api/prompts/save` - Save prompt template
- `GET /api/prompts` - List saved prompts
- `GET /api/prompts/<id>` - Get specific prompt
- `DELETE /api/prompts/<id>` - Delete prompt

### Project Management
- `GET /api/projects` - List all projects
- `GET /api/projects/<id>/transcript` - Get transcript text
- `GET /api/projects/<id>/transcript/download` - Download transcript
- `GET /api/projects/<id>/audio/<filename>` - Download audio
- `DELETE /api/projects/<id>` - Delete project

### Configuration
- `GET /api/config/apikeys` - Check configured API keys
- `POST /api/config/apikeys` - Save API key
- `DELETE /api/config/apikeys/<provider>` - Delete API key
- `GET /api/config/defaultmodel` - Get default AI model
- `POST /api/config/defaultmodel` - Set default AI model
- `GET /api/config/models` - List available models

## Environment Variables

Required API keys (set in `.env`):
- `OPENAI_API_KEY` - OpenAI GPT models
- `GEMINI_API_KEY` - Google Gemini models
- `ANTHROPIC_API_KEY` - Claude models
- `DEEPSEEK_API_KEY` - DeepSeek models
- `QWEN_API_KEY` - Qwen models

## Common Development Tasks

### Adding a new AI provider
1. Add API key to `.env`
2. Update `app/src/transcript_pipeline/processor/litellm_processing.py`
3. Add model options to `frontend/src/core/registry/models.js`
4. Update `/api/config/models` endpoint in `app/main.py`

### Debugging processing issues
1. Check logs: `make logs SERVICE=backend`
2. Look for errors in `app/main.py:process_transcript()`
3. Check pipeline execution in `youtube_to_audio()`
4. Verify API keys are set correctly

### Frontend state debugging
1. Check React Developer Tools for context values
2. Monitor Network tab for API calls
3. Check `frontend/src/core/services/api.js` for request handling

## Notes

- Port 5001 is used instead of 5000 due to macOS AirPlay conflicts
- The application uses file-based storage, not a database
- TTS generation uses local Kokoro TTS, not an external API
- All processing is synchronous - no background job queue
- CORS is enabled for all routes in development