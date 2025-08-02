# Project Overview

## High-Level Description

The **YouTube Transcript Processor** is a full-stack web application that automates the extraction, processing, and enhancement of YouTube video transcripts using AI models. The system transforms raw video transcripts into polished, engaging narratives while preserving educational content and generating high-quality audio output.

## Core Functionality and Purpose

### Primary Features
- **YouTube Transcript Extraction**: Automatically fetches transcripts from YouTube videos
- **AI-Powered Enhancement**: Uses multiple AI providers (OpenAI, Google Gemini, Anthropic Claude, DeepSeek) to transform raw transcripts into engaging narratives
- **Text-to-Speech Generation**: Converts processed transcripts to high-quality audio using Kokoro TTS
- **Prompt Management**: Save, load, and manage custom processing prompts
- **Project Management**: Organize and download processed transcripts and audio files
- **Multi-Model Support**: Switch between different AI models for processing

### Target Users
- **Content Creators**: Repurpose YouTube videos for podcasts, articles, or other content formats
- **Researchers**: Extract and analyze information from video content
- **Educators**: Create accessible versions of educational video content
- **Businesses**: Process recorded meetings, presentations, or training materials

## Technology Stack

### Frontend
- **React 18.2.0**: Modern UI library with hooks and functional components
- **Vite 6.2.4**: Fast build tool and development server
- **React Router DOM 7.4.1**: Client-side routing
- **shadcn/ui**: Component library built on Radix UI and Tailwind CSS
- **TanStack Query**: Data fetching, caching, and synchronization
- **Axios**: HTTP client for API communication
- **Tailwind CSS**: Utility-first CSS framework
- **React Hook Form**: Form state management and validation

### Backend
- **Python 3.11+**: Core programming language
- **Flask 3.1.1**: Lightweight web framework
- **Flask-CORS**: Cross-origin resource sharing support
- **LiteLLM**: Unified interface for multiple AI providers
- **YouTube Transcript API**: YouTube transcript extraction
- **Kokoro TTS**: High-quality text-to-speech synthesis
- **PyYAML**: Configuration management
- **python-dotenv**: Environment variable management

### AI Integration
- **OpenAI GPT Models**: GPT-3.5, GPT-4, GPT-4 Turbo
- **Google Gemini**: Gemini Pro, Gemini 1.5 Pro, Gemini 2.0 Flash Lite
- **Anthropic Claude**: Claude 3 Opus, Sonnet, Haiku
- **DeepSeek**: DeepSeek Chat

### Infrastructure
- **Docker & Docker Compose**: Containerization and orchestration
- **File-based Storage**: JSON and text files for data persistence
- **Environment Variables**: Secure API key management

## Key Dependencies

### Critical Backend Dependencies
```python
Flask==3.1.1              # Web framework
Flask-Cors==6.0.1          # CORS support
litellm==1.74.14           # Unified AI model interface
youtube-transcript-api==1.2.1  # YouTube transcript extraction
kokoro==0.9.4              # Text-to-speech synthesis
PyYAML==6.0.2              # Configuration management
python-dotenv==1.1.1       # Environment variables
```

### Critical Frontend Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^7.4.1",
  "@tanstack/react-query": "^5.71.1",
  "axios": "^1.8.4",
  "react-hook-form": "^7.55.0",
  "@radix-ui/react-*": "Various versions",
  "tailwindcss": "^3.4.17",
  "vite": "^6.2.0"
}
```

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YouTube Transcript Processor                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    HTTP/REST API    ┌─────────────────┐   │
│  │   React Frontend │ ◄─────────────────► │  Flask Backend  │   │
│  │                 │                     │                 │   │
│  │  • shadcn/ui    │                     │  • REST API     │   │
│  │  • TanStack     │                     │  • Processing   │   │
│  │  • React Router │                     │  • File Storage │   │
│  └─────────────────┘                     └─────────────────┘   │
│                                                   │             │
│                                          ┌────────▼────────┐    │
│                                          │  Processing     │    │
│                                          │  Pipeline       │    │
│                                          │                 │    │
│                                          │ ┌─────────────┐ │    │
│                                          │ │  Fetcher    │ │    │
│                                          │ │  Module     │ │    │
│                                          │ └─────────────┘ │    │
│                                          │ ┌─────────────┐ │    │
│                                          │ │ AI Processor│ │    │
│                                          │ │   Module    │ │    │
│                                          │ └─────────────┘ │    │
│                                          │ ┌─────────────┐ │    │
│                                          │ │ TTS Module  │ │    │
│                                          │ └─────────────┘ │    │
│                                          └─────────────────┘    │
│                                                   │             │
│  ┌─────────────────────────────────────────────────▼───────────┐ │
│  │                External Services                            │ │
│  │                                                             │ │
│  │  YouTube API  │  OpenAI  │  Gemini  │  Claude  │  Kokoro   │ │
│  │               │          │          │          │    TTS    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    File Storage                             │ │
│  │                                                             │ │
│  │  • Transcripts (JSON/TXT)  • Prompts (JSON)               │ │
│  │  • Audio Files (WAV)       • Metadata (JSON)              │ │
│  │  • Configuration (YAML)    • Logs                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure Overview

```
prellus/
├── app/                    # Backend Python application
│   ├── main.py            # Flask API server
│   ├── config/            # Configuration files
│   ├── data/              # File-based storage
│   ├── scripts/           # Processing scripts
│   └── src/               # Core processing modules
├── frontend/              # React frontend application
│   ├── src/               # Source code
│   │   ├── components/    # UI components
│   │   ├── features/      # Feature-based modules
│   │   ├── core/          # Core services and routing
│   │   └── shared/        # Shared utilities
│   └── public/            # Static assets
├── docs/                  # Documentation
├── docker-compose.yml     # Container orchestration
└── startup.sh            # Development startup script
```

## Development Workflow

### Local Development
1. **Backend Setup**: Create Python virtual environment, install dependencies
2. **Frontend Setup**: Install Node.js dependencies with npm
3. **Environment Configuration**: Set up API keys in `.env` file
4. **Start Services**: Run `./startup.sh` or start services individually
5. **Access Application**: Frontend at `http://localhost:5174`, API at `http://localhost:5001`

### Production Deployment
1. **Docker Build**: Build container images for frontend and backend
2. **Environment Setup**: Configure production environment variables
3. **Container Orchestration**: Deploy using Docker Compose
4. **Service Monitoring**: Monitor logs and health endpoints

## Key Design Principles

### Backend Architecture
- **Modular Pipeline Design**: Separate modules for fetching, processing, and TTS
- **Provider Abstraction**: Unified interface for multiple AI providers
- **Configuration-Driven**: YAML-based configuration for flexibility
- **Error Handling**: Comprehensive error handling and logging
- **File-Based Storage**: Simple, reliable data persistence

### Frontend Architecture
- **Feature-Based Organization**: Code organized by business features
- **Component Composition**: Reusable UI components with shadcn/ui
- **State Management**: Context API for feature state, TanStack Query for server state
- **Type Safety**: Comprehensive form validation with React Hook Form and Zod
- **Responsive Design**: Mobile-first design with Tailwind CSS

This architecture provides a scalable, maintainable foundation for processing YouTube transcripts with AI enhancement and audio generation capabilities.
