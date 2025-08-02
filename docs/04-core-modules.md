# Core Modules and Components

## Backend Core Modules

### 1. Flask API Server (`app/main.py`)

**Purpose:** Central API gateway that handles all HTTP requests and orchestrates processing pipeline.

**File Location:** `app/main.py`

**Key Responsibilities:**
- HTTP request handling and routing
- Input validation and sanitization
- Processing pipeline orchestration
- File storage management
- Error handling and logging

**Internal Structure:**
```python
# Main Flask application setup
app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Core endpoints
@app.route("/api/transcripts/process", methods=["POST"])
@app.route("/api/prompts/save", methods=["POST"])
@app.route("/api/projects", methods=["GET"])
@app.route("/api/config/apikeys", methods=["GET", "POST"])
```

**APIs Exposed:**
- **Transcript Processing:** `/api/transcripts/process`
- **Prompt Management:** `/api/prompts/*`
- **Project Management:** `/api/projects/*`
- **Configuration:** `/api/config/*`
- **Health Check:** `/api/test`

**Example Usage:**
```python
# Processing a transcript request
@app.route("/api/transcripts/process", methods=["POST"])
def process_transcript():
    data = request.json
    
    # Extract and validate input
    url = data.get("url", "Not provided")
    prompt_data = data.get("promptData", {})
    
    # Create combined prompt
    combined_prompt = format_structured_prompt(prompt_data)
    
    # Configure processing pipeline
    config["ai"]["custom_prompt"] = combined_prompt
    config["ai"]["voice_pack"] = data.get("voice")
    config["ai"]["speed"] = data.get("speed")
    
    # Execute pipeline
    result = youtube_to_audio(url, config, json_data=data)
    
    return jsonify({
        "id": "transcript_123",
        "status": "processing",
        "message": "Transcript processing started"
    })
```

### 2. Transcript Fetcher Module (`app/src/transcript_pipeline/fetcher/`)

**Purpose:** Downloads and stores YouTube video transcripts with metadata.

**File Locations:**
- `fetch_and_store.py` - Main fetcher logic
- `youtube_transcript.py` - YouTube API integration

**Key Responsibilities:**
- YouTube transcript extraction
- Metadata collection (title, duration, video ID)
- Directory structure creation
- Raw data storage

**Internal Structure:**
```python
class TranscriptManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.fetcher = YouTubeTranscriptFetcher()
        self.base_output_dir = self.config.get("output_directory", "data/transcripts")
    
    def fetch_and_store_transcript(self, youtube_url, json_data=None):
        # Fetch transcript with metadata
        transcript_data = self.fetcher.fetch_transcript_with_metadata(youtube_url)
        
        # Set up directory structure
        video_dir = self.setup_video_directory(transcript_data["metadata"]["video_id"])
        
        # Save raw transcript and metadata
        self._save_transcript_data(transcript_data, video_dir)
        
        return {
            "video_id": transcript_data["metadata"]["video_id"],
            "video_dir": video_dir,
            "transcript_data": transcript_data
        }
```

**Example Directory Structure Created:**
```
data/transcripts/
└── dQw4w9WgXcQ_20250802_143022/
    ├── raw/
    │   ├── transcript.json      # Raw transcript data
    │   └── transcript.txt       # Plain text version
    ├── processed/               # Will contain AI-processed results
    ├── audio/                   # Will contain generated audio
    └── metadata.json           # Video metadata
```

### 3. AI Processor Module (`app/src/transcript_pipeline/processor/`)

**Purpose:** Transforms raw transcripts into polished narratives using AI models.

**File Locations:**
- `ai_processor.py` - Main AI processing logic
- `chunked_processor.py` - Large transcript handling
- `litellm_processing.py` - AI provider abstraction

**Key Responsibilities:**
- AI model integration via LiteLLM
- Prompt management and formatting
- Large transcript chunking
- Output quality validation

**Internal Structure:**
```python
class TranscriptAIProcessor:
    def __init__(self, config):
        self.model = config.get("model", "gemini-2.0-flash-lite")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 8192)
        self.system_prompt = TRANSCRIPT_TRANSFORMATION_PROMPT
    
    def process_transcript(self, transcript_text):
        """Process transcript using LLM API"""
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": transcript_text}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.exception(f"Error processing transcript: {e}")
            raise
```

**Supported AI Models:**
- **OpenAI:** GPT-3.5 Turbo, GPT-4, GPT-4 Turbo
- **Google:** Gemini Pro, Gemini 1.5 Pro, Gemini 2.0 Flash Lite
- **Anthropic:** Claude 3 Opus, Sonnet, Haiku
- **DeepSeek:** DeepSeek Chat

### 4. TTS Module (`app/src/transcript_pipeline/tts/`)

**Purpose:** Converts processed transcripts to high-quality audio using Kokoro TTS.

**File Location:** `tts_generator.py`

**Key Responsibilities:**
- Text chunking for optimal TTS processing
- Kokoro TTS integration
- Audio file concatenation
- Voice and speed configuration

**Internal Structure:**
```python
class TTSGenerator:
    def __init__(self, config):
        self.voice = config.get("voice_pack", "bm_lewis")
        self.speed = config.get("speed", 0.8)
        self.language_code = config.get("language", "b")  # British English
        self.chunk_size = config.get("chunk_size", 500)
    
    def generate_audio(self, text, output_path, metadata):
        """Generate audio from text using Kokoro TTS"""
        
        # Split text into manageable chunks
        chunks = self.split_text_into_chunks(text)
        audio_files = []
        
        for i, chunk in enumerate(chunks):
            chunk_file = f"chunk_{i:03d}.wav"
            
            # Build Kokoro command
            cmd = ['kokoro', 
                   '-l', self.language_code,
                   '-i', chunk_text_file,
                   '-o', chunk_file,
                   '-m', self.voice,
                   '-s', str(self.speed)]
            
            # Execute TTS generation
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                audio_files.append(chunk_file)
        
        # Concatenate all audio chunks
        final_audio = self.concatenate_audio_files(audio_files)
        
        return {
            "output_path": output_path,
            "audio_duration_seconds": len(final_audio) / self.sample_rate,
            "chunks_processed": len(chunks)
        }
```

## Frontend Core Modules

### 1. Router Configuration (`frontend/src/core/router.jsx`)

**Purpose:** Centralized routing configuration for the React application.

**File Location:** `frontend/src/core/router.jsx`

**Internal Structure:**
```javascript
import { createBrowserRouter } from "react-router-dom";
import { RootLayout, NotFound } from "@/shared/components";
import { TranscriptPage } from "@/features/transcript/components";
import { ConfigPage } from "@/features/config/components";
import { DownloadsPage } from "@/features/downloads/components";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <NotFound />,
    children: [
      { index: true, element: <TranscriptPage /> },
      { path: "config", element: <ConfigPage /> },
      { path: "downloads", element: <DownloadsPage /> },
    ],
  },
]);
```

### 2. API Services Layer (`frontend/src/core/services/`)

**Purpose:** Centralized API communication with error handling and request management.

**File Locations:**
- `api.js` - Base API client
- `transcript.js` - Transcript-related API calls
- `prompt.js` - Prompt management API calls
- `project.js` - Project management API calls
- `config.js` - Configuration API calls

**Key Pattern:**
```javascript
// Base API client with error handling
export const apiRequest = async (requestFn) => {
  try {
    const response = await requestFn();
    return response.data;
  } catch (error) {
    toast.error(`API Error: ${error.response?.data?.message || error.message}`);
    throw error;
  }
};

// Feature-specific service
export const transcriptService = {
  processTranscript: (data) => 
    apiRequest(() => api.post("/transcripts/process", data)),
  
  getTranscripts: () => 
    apiRequest(() => api.get("/transcripts")),
};
```

### 3. Feature Modules (`frontend/src/features/`)

**Purpose:** Feature-based organization with self-contained modules.

#### Transcript Feature (`frontend/src/features/transcript/`)
- **Components:** Form UI, voice selector, prompt editor
- **Context:** State management for transcript processing
- **Hooks:** Data fetching and processing operations

#### Downloads Feature (`frontend/src/features/downloads/`)
- **Components:** Project list, transcript viewer, download buttons
- **Context:** Project management state
- **Hooks:** Project data operations

#### Config Feature (`frontend/src/features/config/`)
- **Components:** API key management, model selection
- **Hooks:** Configuration data operations

**Example Feature Structure:**
```javascript
// TranscriptContext.jsx
export function TranscriptProvider({ children }) {
  const [formState, setFormState] = useState({
    url: "",
    promptData: { /* structured prompt fields */ },
    voice: "bm_lewis",
    speed: 0.8
  });
  
  const handleProcessTranscript = async () => {
    const result = await transcriptService.processTranscript(formState);
    // Handle success/error
  };
  
  return (
    <TranscriptContext.Provider value={{
      ...formState,
      handleProcessTranscript,
      // ... other operations
    }}>
      {children}
    </TranscriptContext.Provider>
  );
}
```

### 4. Shared Components (`frontend/src/shared/`)

**Purpose:** Reusable components and utilities used across features.

**File Locations:**
- `components/RootLayout.jsx` - Main application layout
- `components/Navbar.jsx` - Navigation component
- `ui/` - shadcn/ui component library

**Key Components:**
```javascript
// RootLayout provides global context providers
export function RootLayout() {
  return (
    <TranscriptProvider>
      <ProjectProvider>
        <div className="min-h-screen bg-background">
          <Navbar />
          <main className="container mx-auto py-6 px-4">
            <Outlet />
          </main>
          <Toaster />
        </div>
      </ProjectProvider>
    </TranscriptProvider>
  );
}
```

## Module Interactions

### Backend Pipeline Flow
```
Flask API → youtube_to_audio() → fetch_transcript() → process_transcript() → generate_audio_from_transcript()
```

### Frontend Data Flow
```
User Action → Context State → API Service → Backend → Response → Context Update → UI Re-render
```

### Cross-Module Communication
- **Configuration:** YAML files drive backend behavior
- **State Management:** React Context for UI state, TanStack Query for server state
- **Error Handling:** Consistent error propagation and user feedback
- **Logging:** Structured logging throughout backend pipeline

This modular architecture ensures clear separation of concerns while maintaining efficient communication between components.
