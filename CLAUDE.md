# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Transcript Processor - A React/Flask application that fetches YouTube video transcripts and processes them using AI providers (OpenAI, Anthropic, Google Gemini, DeepSeek). The system uses a response-aware processing approach with dynamic catch-up for precise length control and multi-response generation.

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
npm run dev        # Start development server (port 5173)
npm run build      # Build for production
npm run lint       # Run ESLint
```

### Backend development
```bash
cd app
python -m venv .venv                    # Create virtual environment
source .venv/bin/activate               # Activate (macOS/Linux)
pip install -r requirements.txt         # Install dependencies
python main.py                          # Run Flask server (port 5001)
```

## High-Level Architecture

### System Components

1. **Frontend (React + Vite)**
   - Port: 5173
   - Feature-based organization: transcript, config, downloads
   - UI: shadcn/ui components with Radix UI primitives
   - State: React Context API + TanStack Query for server state
   - Routing: React Router v7

2. **Backend (Flask)**
   - Port: 5001 (avoiding macOS AirPlay conflict on 5000)
   - RESTful API with CORS enabled
   - Endpoints grouped by feature: transcripts, prompts, projects, config
   - File-based storage (no database)

3. **Core Processing Pipeline** (`app/src/core/`)
   - **Fetcher Module**: YouTube transcript retrieval
   - **Processor Module**: Response-aware AI processing with dynamic catch-up
   - **Storage Module**: Structured file management
   - Uses LiteLLM for unified AI provider interface

### Processing Flow
```
User Input → Frontend → Flask API → Core Pipeline → AI Providers
    ↓            ↓          ↓              ↓              ↓
UI Event → State/Context → HTTP → youtube_to_transcript() → LiteLLM
    ↓            ↓          ↓              ↓              ↓
Re-render ← State Update ← JSON ← Processed Files ← AI Response
```

### Response-Aware Processing System

The processor implements sophisticated multi-response generation:
1. Creates master document with response planning
2. Respects model-specific token limits (64K Claude, 16K OpenAI, etc.)
3. Dynamic catch-up system for precise length control
4. Seamless continuation across multiple API calls
5. TTS-optimized formatting (though TTS currently disabled)

## Important Files and Locations

### Configuration
- `app/config/config.yaml` - Main configuration file
- `.env` - API keys and environment variables
- `Makefile` - Development commands and automation

### Core Processing
- `app/main.py` - Flask application and API routes
- `app/scripts/youtube_to_transcript.py` - Main processing pipeline
- `app/src/core/processor/simple_processor.py` - Response-aware AI processor
- `app/src/core/fetcher/youtube_transcript.py` - YouTube transcript fetcher
- `app/src/core/storage/transcript_storage.py` - File management

### Frontend Entry Points
- `frontend/src/main.jsx` - Application entry
- `frontend/src/App.jsx` - Main application component
- `frontend/src/core/router.jsx` - Route definitions
- `frontend/src/core/services/api.js` - API client

### Data Storage
- `app/data/transcripts/<VIDEO_ID_TIMESTAMP>/` - Project directories
  - `/raw/` - Original transcript
  - `/processed/` - AI-processed content
  - `/final/` - Final output
  - `metadata.json` - Project metadata

## API Endpoints

### Transcript Processing
- `POST /api/transcripts/process` - Process YouTube video
- `GET /api/transcripts` - List transcripts

### Prompt Management
- `POST /api/prompts/save` - Save prompt template
- `GET /api/prompts` - List saved prompts
- `GET /api/prompts/<id>` - Get specific prompt
- `DELETE /api/prompts/<id>` - Delete prompt

### Project Management
- `GET /api/projects` - List all projects
- `GET /api/projects/<id>/transcript` - Get transcript text
- `GET /api/projects/<id>/transcript/download` - Download transcript
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
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Google Gemini models
- `ANTHROPIC_API_KEY` - Claude models
- `DEEPSEEK_API_KEY` - DeepSeek models
- `QWEN_API_KEY` - Qwen models (if used)

## Common Development Tasks

### Adding a new AI provider
1. Add API key to `.env`
2. Update provider configuration in `app/src/core/processor/simple_processor.py`
3. Add model options to `frontend/src/core/registry/models.js`
4. Update `/api/config/models` endpoint in `app/main.py`

### Debugging processing issues
1. Check logs: `make logs SERVICE=backend`
2. Review `app/main.py:process_transcript()` for API errors
3. Check `app/src/core/processor/simple_processor.py` for processing logic
4. Verify API keys are set correctly in `.env`
5. Check model token limits in processor configuration

### Frontend state debugging
1. Check React Developer Tools for context values
2. Monitor Network tab for API calls
3. Review TanStack Query cache in dev tools
4. Check `frontend/src/core/services/api.js` for request handling

### Testing new processing methods
```bash
cd app
python test_new_method.py  # Test the new processing pipeline
```

## Notes

- Port 5001 is used for backend (not 5000) due to macOS AirPlay conflicts
- The application uses file-based storage, not a database
- All processing is synchronous - no background job queue
- CORS is enabled for all routes in development
- TTS generation code exists but is currently disabled in favor of transcript-only processing
- The new "response-aware" processor handles long transcripts by intelligently splitting across multiple AI calls