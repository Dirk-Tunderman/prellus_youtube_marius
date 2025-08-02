# Development Workflows

## Build Process

### Backend Build Process

#### Development Setup
```bash
# 1. Create Python virtual environment
cd app
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables (optional)
cp .env.example .env       # If .env.example exists
# Edit .env with your API keys
```

#### Running Backend
```bash
# Development mode (with auto-reload)
cd app
source .venv/bin/activate
python main.py

# The server will start on http://localhost:5001
# API endpoints available at http://localhost:5001/api/*
```

#### Backend Dependencies Management
```bash
# Add new dependency
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt
```

### Frontend Build Process

#### Development Setup
```bash
# 1. Install Node.js dependencies
cd frontend
npm install

# 2. Start development server
npm run dev

# The frontend will start on http://localhost:5174 (or next available port)
```

#### Frontend Build Commands
```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

#### Frontend Dependencies Management
```bash
# Add new dependency
npm install package-name

# Add development dependency
npm install --save-dev package-name

# Remove dependency
npm uninstall package-name

# Update dependencies
npm update
```

## Testing Framework

### Backend Testing

Currently, the backend uses **manual testing** and **logging** for validation:

#### API Testing
```bash
# Test API connectivity
curl http://localhost:5001/api/test

# Test transcript processing (example)
curl -X POST http://localhost:5001/api/transcripts/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=test",
    "promptData": {
      "yourRole": "Test role",
      "scriptStructure": "Test structure"
    },
    "voice": "bm_lewis",
    "speed": 0.8
  }'
```

#### Processing Pipeline Testing
```bash
# Test individual scripts
cd app
source .venv/bin/activate

# Test transcript fetching
python scripts/fetch_youtube_transcript.py --video-id=test_id

# Test AI processing
python scripts/process_transcript.py --video-id=test_id --mock

# Test TTS generation
python scripts/generate_audio.py --transcript-dir=path/to/transcript
```

### Frontend Testing

The frontend uses **browser-based testing** and **React DevTools**:

#### Manual Testing Workflow
1. Start development server: `npm run dev`
2. Open browser to `http://localhost:5174`
3. Test user flows manually
4. Check browser console for errors
5. Use React DevTools for component inspection

#### Linting and Code Quality
```bash
# Run ESLint
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix
```

## Deployment Process

### Local Development Deployment

#### Quick Start (Recommended)
```bash
# Start both frontend and backend
./startup.sh

# This script:
# 1. Starts frontend on available port (usually 5174)
# 2. Starts backend on port 5001
# 3. Runs both in background
```

#### Manual Start
```bash
# Terminal 1: Start backend
cd app
source .venv/bin/activate
python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### Docker Deployment

#### Build Docker Images
```bash
# Build backend image
docker build -t prellus_backend:latest ./app

# Build frontend image
docker build -t prellus_frontend:latest ./frontend
```

#### Run with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build -d
```

#### Docker Configuration
```yaml
# docker-compose.yml
version: "3.8"
services:
  backend:
    image: prellus_backend:latest
    ports:
      - "5001:5001"
    volumes:
      - prellus_data:/app/data
      - prellus_config:/app/config
    
  frontend:
    image: prellus_frontend:latest
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## Common Development Tasks

### Adding a New API Endpoint

1. **Define the endpoint in Flask** (`app/main.py`):
```python
@app.route("/api/new-feature", methods=["POST"])
def new_feature():
    try:
        data = request.json
        # Process the request
        result = process_new_feature(data)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

2. **Create frontend service** (`frontend/src/core/services/`):
```javascript
// newFeatureService.js
export const newFeatureService = {
  processNewFeature: (data) => 
    apiRequest(() => api.post("/new-feature", data))
};
```

3. **Add to main services export**:
```javascript
// frontend/src/core/services/index.js
export { newFeatureService } from './newFeatureService';
```

### Adding a New Frontend Feature

1. **Create feature directory structure**:
```bash
mkdir -p frontend/src/features/new-feature/{components,context,hooks}
```

2. **Create main component**:
```javascript
// frontend/src/features/new-feature/components/NewFeaturePage.jsx
export function NewFeaturePage() {
  return (
    <div>
      <h1>New Feature</h1>
      {/* Feature implementation */}
    </div>
  );
}
```

3. **Add route** (`frontend/src/core/router.jsx`):
```javascript
{
  path: "new-feature",
  element: <NewFeaturePage />,
}
```

4. **Create feature exports**:
```javascript
// frontend/src/features/new-feature/index.js
export { NewFeaturePage } from './components/NewFeaturePage';
```

### Modifying AI Processing

1. **Update configuration** (`app/config/config.yaml`):
```yaml
ai:
  model: new-model-name
  temperature: 0.7
  custom_parameter: value
```

2. **Modify processor** (`app/src/transcript_pipeline/processor/ai_processor.py`):
```python
class TranscriptAIProcessor:
    def __init__(self, config):
        self.custom_parameter = config.get("custom_parameter", "default")
        # ... existing initialization
    
    def process_transcript(self, transcript_text):
        # Add new processing logic
        enhanced_prompt = self.enhance_prompt_with_custom_logic()
        # ... existing processing
```

### Adding New Voice Options

1. **Update voice configuration** (`frontend/src/lib/ttsOptions.js`):
```javascript
export const voiceOptions = [
  // ... existing voices
  {
    value: "new_voice_code",
    label: "New Voice Name",
    accent: "Accent",
    gender: "Gender",
    description: "Description of the voice"
  }
];
```

2. **Test voice availability**:
```bash
# Test if Kokoro TTS supports the new voice
kokoro -l b -m new_voice_code -i test.txt -o test.wav
```

### Environment Configuration

#### Backend Environment Variables
Create `.env` file in project root:
```bash
# AI Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
GEMINI_API_KEY=your-gemini-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key

# Optional: Override default model
DEFAULT_AI_MODEL=claude-3-7-sonnet-20250219
```

#### Frontend Environment Variables
Create `.env.local` in frontend directory:
```bash
# API URL (if different from default)
VITE_API_URL=http://localhost:5001/api

# Development flags
VITE_DEBUG_MODE=true
```

### Debugging Common Issues

#### Backend Issues
```bash
# Check if backend is running
curl http://localhost:5001/api/test

# View backend logs
tail -f logs/backend.log

# Check Python dependencies
cd app && source .venv/bin/activate && pip list

# Test individual processing components
python scripts/test_voice_options.py
```

#### Frontend Issues
```bash
# Check if frontend is running
curl http://localhost:5174

# View frontend logs in browser console
# Open Developer Tools → Console

# Check Node.js dependencies
cd frontend && npm list

# Clear npm cache if needed
npm cache clean --force
```

#### Connection Issues
```bash
# Check if ports are available
lsof -i :5001  # Backend port
lsof -i :5174  # Frontend port

# Restart services
./shutdown.sh && ./startup.sh
```

### Performance Optimization

#### Backend Optimization
- Monitor processing times in logs
- Optimize AI model selection for speed vs. quality
- Implement caching for repeated requests
- Use chunked processing for large transcripts

#### Frontend Optimization
- Use React DevTools Profiler to identify slow components
- Implement proper memoization with `useMemo` and `useCallback`
- Optimize bundle size with code splitting
- Monitor Core Web Vitals in browser DevTools

This development workflow guide provides practical steps for common development tasks and troubleshooting procedures.
