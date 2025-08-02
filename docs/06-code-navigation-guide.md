# Code Navigation Guide

## Directory Structure Overview

### Root Directory Structure
```
prellus/
├── app/                        # Backend Python application
├── frontend/                   # React frontend application
├── docs/                       # Documentation files
├── archive/                    # Legacy/archived code
├── logs/                       # Application logs
├── docker-compose.yml          # Container orchestration
├── startup.sh                  # Development startup script
└── README.md                   # Project overview
```

## Backend Directory Structure (`app/`)

### Main Application Files
```
app/
├── main.py                     # 🚀 Flask API server (MAIN ENTRY POINT)
├── requirements.txt            # Python dependencies
├── config.yaml                 # Legacy configuration (not used)
└── nixpacks.toml              # Deployment configuration
```

### Configuration
```
app/config/
└── config.yaml                # ⚙️ Active configuration file
                               # Contains AI models, TTS settings, processing parameters
```

### Data Storage
```
app/data/
├── stored_prompts/            # 💾 JSON files for saved prompt templates
│   ├── {uuid}.json           # Individual prompt files
│   └── ...
└── transcripts/              # 📁 Project directories
    └── {video_id}_{timestamp}/
        ├── raw/              # Original transcript data
        ├── processed/        # AI-processed results
        ├── audio/           # Generated audio files
        └── metadata.json    # Project metadata
```

### Processing Scripts
```
app/scripts/
├── youtube_to_audio.py        # 🎯 Main processing pipeline
├── process_transcript.py      # AI processing script
├── generate_audio.py          # TTS generation script
├── fetch_youtube_transcript.py # YouTube transcript fetcher
└── ...                       # Additional utility scripts
```

### Core Processing Modules
```
app/src/
├── main.py                    # Alternative entry point
├── transcript_pipeline/       # 🔧 Core processing pipeline
│   ├── fetcher/              # YouTube transcript extraction
│   │   ├── fetch_and_store.py
│   │   └── youtube_transcript.py
│   ├── processor/            # AI processing modules
│   │   ├── ai_processor.py   # Main AI processing logic
│   │   ├── chunked_processor.py # Large transcript handling
│   │   ├── litellm_processing.py # AI provider abstraction
│   │   └── ...
│   ├── tts/                  # Text-to-speech generation
│   │   └── tts_generator.py
│   └── utils/                # Utility functions
│       ├── config.py
│       └── ...
└── utils/                    # General utilities
    ├── logger.py
    └── ...
```

## Frontend Directory Structure (`frontend/`)

### Main Application Files
```
frontend/
├── index.html                 # HTML entry point
├── package.json              # Dependencies and scripts
├── vite.config.js            # Vite build configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── components.json           # shadcn/ui configuration
└── jsconfig.json             # JavaScript configuration
```

### Source Code Structure
```
frontend/src/
├── main.jsx                   # 🚀 React application entry point
├── App.jsx                    # Root App component
├── index.css                  # Global styles
└── ...
```

### Feature-Based Organization
```
frontend/src/features/
├── transcript/                # 📝 Transcript processing feature
│   ├── components/           # UI components
│   │   ├── TranscriptPage.jsx # Main processing interface
│   │   ├── TranscriptForm.jsx # URL input form
│   │   ├── PromptEditor.jsx  # Prompt customization
│   │   ├── VoiceSelector.jsx # Voice/speed settings
│   │   └── ...
│   ├── context/              # State management
│   │   └── TranscriptContext.jsx
│   ├── hooks/                # Data fetching hooks
│   └── index.js              # Feature exports
├── downloads/                 # 📥 Project management feature
│   ├── components/
│   │   ├── DownloadsPage.jsx # Project list interface
│   │   ├── ProjectCard.jsx   # Individual project display
│   │   └── ...
│   ├── context/
│   │   └── ProjectContext.jsx
│   └── ...
└── config/                   # ⚙️ Configuration management
    ├── components/
    │   ├── ConfigPage.jsx    # Settings interface
    │   ├── ApiKeyManager.jsx # API key management
    │   └── ...
    └── ...
```

### Core Application Infrastructure
```
frontend/src/core/
├── router.jsx                 # 🛣️ Application routing configuration
├── services/                  # API communication layer
│   ├── api.js                # Base API client with error handling
│   ├── transcript.js         # Transcript-related API calls
│   ├── prompt.js             # Prompt management API calls
│   ├── project.js            # Project management API calls
│   ├── config.js             # Configuration API calls
│   └── index.js              # Services exports
└── index.js                  # Core exports
```

### Shared Resources
```
frontend/src/shared/
├── components/               # Reusable UI components
│   ├── RootLayout.jsx       # Main application layout
│   ├── Navbar.jsx           # Navigation component
│   ├── NotFound.jsx         # 404 error page
│   └── index.js             # Component exports
├── ui/                      # Utility components
└── index.js                 # Shared exports
```

### UI Component Library
```
frontend/src/components/ui/   # 🎨 shadcn/ui components (DO NOT MODIFY)
├── button.jsx               # Button component
├── input.jsx                # Input component
├── dialog.jsx               # Modal dialog component
├── tabs.jsx                 # Tab component
├── accordion.jsx            # Accordion component
├── sonner.jsx               # Toast notifications
└── ...                      # Other UI components
```

### Utility Libraries
```
frontend/src/lib/
├── utils.js                 # General utility functions
└── ttsOptions.js           # Text-to-speech configuration options
```

### Custom Hooks
```
frontend/src/hooks/
└── use-mobile.jsx          # Mobile device detection hook
```

## Key File Locations and Purposes

### 🚀 Main Entry Points
- **Backend:** `app/main.py` - Flask API server
- **Frontend:** `frontend/src/main.jsx` - React application root
- **Processing:** `app/scripts/youtube_to_audio.py` - Main processing pipeline

### ⚙️ Configuration Files
- **Backend Config:** `app/config/config.yaml` - AI models, TTS settings, processing parameters
- **Frontend Config:** `frontend/vite.config.js` - Build configuration
- **UI Config:** `frontend/components.json` - shadcn/ui component configuration
- **Styling:** `frontend/tailwind.config.js` - Tailwind CSS configuration

### 🔧 Core Processing Logic
- **AI Processing:** `app/src/transcript_pipeline/processor/ai_processor.py`
- **TTS Generation:** `app/src/transcript_pipeline/tts/tts_generator.py`
- **Transcript Fetching:** `app/src/transcript_pipeline/fetcher/fetch_and_store.py`

### 🎨 Main UI Components
- **Transcript Processing:** `frontend/src/features/transcript/components/TranscriptPage.jsx`
- **Project Management:** `frontend/src/features/downloads/components/DownloadsPage.jsx`
- **Configuration:** `frontend/src/features/config/components/ConfigPage.jsx`

### 📡 API Communication
- **Base API Client:** `frontend/src/core/services/api.js`
- **Backend API Routes:** `app/main.py` (search for `@app.route`)

## How to Locate Specific Functionality

### Finding Backend Features
1. **API Endpoints:** Search `app/main.py` for `@app.route`
2. **Processing Logic:** Look in `app/src/transcript_pipeline/`
3. **Configuration:** Check `app/config/config.yaml`
4. **Data Storage:** Examine `app/data/` directory structure

### Finding Frontend Features
1. **Pages/Routes:** Check `frontend/src/core/router.jsx`
2. **Feature Components:** Look in `frontend/src/features/{feature}/components/`
3. **State Management:** Find contexts in `frontend/src/features/{feature}/context/`
4. **API Calls:** Check `frontend/src/core/services/`

### Finding UI Components
1. **Custom Components:** `frontend/src/shared/components/`
2. **shadcn/ui Components:** `frontend/src/components/ui/` (don't modify these)
3. **Feature-Specific Components:** `frontend/src/features/{feature}/components/`

### Finding Configuration
1. **Backend Settings:** `app/config/config.yaml`
2. **Environment Variables:** `.env` file (create if needed)
3. **Frontend Build:** `frontend/vite.config.js`
4. **Styling:** `frontend/tailwind.config.js`

## File Naming Conventions

### Backend Python Files
- **Snake_case:** `fetch_and_store.py`, `ai_processor.py`
- **Descriptive names:** Files clearly indicate their purpose
- **Module structure:** Related functionality grouped in directories

### Frontend JavaScript Files
- **PascalCase for Components:** `TranscriptPage.jsx`, `ApiKeyManager.jsx`
- **camelCase for utilities:** `api.js`, `utils.js`
- **Feature prefixes:** Components often prefixed with feature name

### Configuration Files
- **Lowercase with extensions:** `config.yaml`, `package.json`
- **Descriptive names:** `docker-compose.yml`, `tailwind.config.js`

## Quick Navigation Tips

### 🔍 Finding Specific Features
- **Search by route:** Find `/api/transcripts/process` to locate transcript processing
- **Search by component:** Find `TranscriptPage` to locate main processing UI
- **Search by function:** Find `youtube_to_audio` to locate main pipeline

### 🚀 Starting Points for Development
- **Adding new API endpoint:** Start with `app/main.py`
- **Adding new UI feature:** Start with `frontend/src/features/`
- **Modifying processing logic:** Start with `app/src/transcript_pipeline/`
- **Changing configuration:** Start with `app/config/config.yaml`

### 📁 Understanding Data Flow
- **Follow the pipeline:** `main.py` → `youtube_to_audio.py` → processing modules
- **Trace API calls:** Frontend service → API endpoint → processing function
- **Check file storage:** `app/data/` for understanding data persistence

This navigation guide provides a roadmap for efficiently finding and understanding any part of the codebase.
