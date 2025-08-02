# Feature Map

## User-Facing Features and Their Implementation

This document maps each user-facing feature to its implementing components, showing the complete path from user interface to backend processing.

## Feature 1: YouTube Transcript Processing

### Functionality Description
Users can input a YouTube URL and have the video's transcript automatically extracted, processed with AI to improve readability and flow, and converted to high-quality audio.

### Entry Points in Code
- **Frontend:** `frontend/src/features/transcript/components/TranscriptPage.jsx`
- **Backend:** `app/main.py` - `/api/transcripts/process` endpoint

### Main Files/Functions Involved

#### Frontend Components
```javascript
// Main processing interface
TranscriptPage.jsx
├── TranscriptForm.jsx          // URL input and basic settings
├── VoiceSelector.jsx           // Voice and speed configuration
├── PromptEditor.jsx            // AI prompt customization
└── ModelSelector.jsx           // AI model selection

// State management
TranscriptContext.jsx           // Form state and processing logic
```

#### Backend Processing Chain
```python
# API endpoint
app/main.py::process_transcript()
├── scripts/youtube_to_audio.py::youtube_to_audio()
    ├── src/transcript_pipeline/fetcher/fetch_and_store.py::fetch_transcript()
    ├── src/transcript_pipeline/processor/ai_processor.py::process_transcript()
    └── src/transcript_pipeline/tts/tts_generator.py::generate_audio_from_transcript()
```

### Data Flow for the Feature

1. **User Input Collection**
   ```javascript
   // TranscriptForm.jsx
   const handleSubmit = () => {
     const formData = {
       url: "https://youtube.com/watch?v=abc123",
       promptData: {
         yourRole: "You are a content editor...",
         scriptStructure: "Create clear sections...",
         // ... other prompt fields
       },
       voice: "bm_lewis",
       speed: 0.8
     };
     
     transcript.handleProcessTranscript(formData);
   };
   ```

2. **API Request**
   ```javascript
   // core/services/transcript.js
   export const transcriptService = {
     processTranscript: (data) => 
       apiRequest(() => api.post("/transcripts/process", data))
   };
   ```

3. **Backend Processing**
   ```python
   # app/main.py
   @app.route("/api/transcripts/process", methods=["POST"])
   def process_transcript():
       # Extract data and configure pipeline
       result = youtube_to_audio(url, config, json_data=data)
       return jsonify({"status": "processing", "id": "transcript_123"})
   ```

### Configuration Options
- **AI Models:** OpenAI GPT, Google Gemini, Anthropic Claude, DeepSeek
- **Voice Options:** Multiple accents and genders (British Male Lewis, American Female Bella, etc.)
- **Speed Control:** 0.5x to 2.0x playback speed
- **Prompt Customization:** Structured fields for role, structure, tone, flow, and additional instructions

### Concrete Example in Action

**User Scenario:** Processing a 30-minute educational video about machine learning

**Input:**
```json
{
  "url": "https://youtube.com/watch?v=Gv9_4yMHFhI",
  "promptData": {
    "yourRole": "You are an educational content editor specializing in technical topics",
    "scriptStructure": "Create clear sections with headings and smooth transitions between concepts",
    "toneAndStyle": "Professional yet accessible, explaining complex concepts simply",
    "retentionAndFlow": "Use examples and analogies to make concepts memorable",
    "additionalInstructions": "Focus on practical applications and real-world examples"
  },
  "voice": "bm_lewis",
  "speed": 0.9
}
```

**Processing Steps:**
1. Fetch transcript from YouTube (2,847 words of raw transcript)
2. Process with Claude 3 Sonnet using custom prompt (produces 3,124 words of polished content)
3. Generate audio using British Male Lewis voice at 0.9x speed (23 minutes final duration)

**Output:**
- Processed transcript file: `narrative_transcript.txt`
- High-quality audio file: `final_audio.wav`
- Metadata with processing details

## Feature 2: Prompt Management System

### Functionality Description
Users can create, save, load, and manage custom prompt templates for different types of content processing.

### Entry Points in Code
- **Frontend:** `frontend/src/features/transcript/components/PromptEditor.jsx`
- **Backend:** `app/main.py` - `/api/prompts/*` endpoints

### Main Files/Functions Involved

#### Frontend Components
```javascript
PromptEditor.jsx
├── PromptSaveDialog.jsx        // Save prompt with custom name
├── PromptListDialog.jsx        // Browse and load saved prompts
└── PromptDeleteConfirm.jsx     // Delete confirmation dialog
```

#### Backend Handlers
```python
# app/main.py
save_prompt()                   # POST /api/prompts/save
list_prompts()                  # GET /api/prompts
get_prompt()                    # GET /api/prompts/{id}
delete_prompt()                 # DELETE /api/prompts/{id}
```

### Data Flow Example

**Saving a Prompt:**
```javascript
// Frontend
const handleSavePrompt = async () => {
  const promptData = {
    promptName: "Educational Content Template",
    promptData: {
      yourRole: "Educational content editor...",
      scriptStructure: "Clear sections with examples...",
      // ... other fields
    }
  };
  
  await promptService.savePrompt(promptData);
};
```

**Backend Storage:**
```python
# Creates file: app/data/stored_prompts/{uuid}.json
{
  "meta_data": {
    "prompt_name": "Educational Content Template",
    "date": "2025-08-02T14:30:22",
    "unique_identifier": "af0717d3-b333-48e7-931e-45ddcea4f40c"
  },
  "prompt": {
    "Role": "Educational content editor...",
    "Script_Structure": "Clear sections with examples...",
    "Tone_Style": "Professional yet accessible...",
    "Retention_Flow": "Use examples and analogies...",
    "Additional_instructions": "Focus on practical applications..."
  }
}
```

## Feature 3: Project Management and Downloads

### Functionality Description
Users can view all processed projects, download transcript files and audio files, and manage their project library.

### Entry Points in Code
- **Frontend:** `frontend/src/features/downloads/components/DownloadsPage.jsx`
- **Backend:** `app/main.py` - `/api/projects/*` endpoints

### Main Files/Functions Involved

#### Frontend Components
```javascript
DownloadsPage.jsx
├── ProjectList.jsx             // List of all projects
├── ProjectCard.jsx             // Individual project display
├── TranscriptViewer.jsx        // Modal transcript viewer
└── DeleteConfirmDialog.jsx     // Project deletion confirmation
```

#### Backend Handlers
```python
get_projects()                  # GET /api/projects
get_transcript()                # GET /api/projects/{id}/transcript
download_transcript()           # GET /api/projects/{id}/transcript/download
download_audio()                # GET /api/projects/{id}/audio/{filename}
delete_project()                # DELETE /api/projects/{id}
```

### Data Flow Example

**Loading Projects:**
```javascript
// Frontend data fetching
const { projects, isLoading } = useProjectData();

// Backend scans file system
const projects = [];
const transcripts_dir = "app/data/transcripts";

for (const project_name of os.listdir(transcripts_dir)) {
  const metadata_path = path.join(transcripts_dir, project_name, "metadata.json");
  const metadata = JSON.parse(fs.readFileSync(metadata_path));
  
  projects.push({
    id: project_name,
    name: metadata.title,
    date: metadata.timestamp,
    hasTranscript: fs.existsSync(path.join(project_name, "processed", "narrative_transcript.txt")),
    audioFiles: fs.readdirSync(path.join(project_name, "audio")).filter(f => f.endsWith('.wav'))
  });
}
```

## Feature 4: Configuration Management

### Functionality Description
Users can manage API keys for different AI providers, select default models, and configure system settings.

### Entry Points in Code
- **Frontend:** `frontend/src/features/config/components/ConfigPage.jsx`
- **Backend:** `app/main.py` - `/api/config/*` endpoints

### Main Files/Functions Involved

#### Frontend Components
```javascript
ConfigPage.jsx
├── ApiKeyManager.jsx           // Manage API keys for each provider
├── DefaultModelSelector.jsx    // Select default AI model
└── ModelAvailability.jsx       // Show which models are available
```

#### Backend Configuration
```python
get_api_keys()                  # GET /api/config/apikeys
save_api_key()                  # POST /api/config/apikeys
delete_api_key()                # DELETE /api/config/apikeys/{provider}
get_available_models()          # GET /api/config/models
get_default_model()             # GET /api/config/defaultmodel
save_default_model()            # POST /api/config/defaultmodel
```

### Configuration Storage

**Environment Variables (.env):**
```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
```

**YAML Configuration (app/config/config.yaml):**
```yaml
ai:
  model: claude-3-7-sonnet-20250219
  temperature: 0.7
  max_tokens: 8192

tts:
  voice_pack: bm_lewis
  speed: 0.8
```

## Feature 5: Real-time Processing Status

### Functionality Description
Users receive immediate feedback on processing status through toast notifications and UI state updates.

### Implementation Details

**Frontend State Management:**
```javascript
// TranscriptContext.jsx
const [isProcessing, setIsProcessing] = useState(false);

const handleProcessTranscript = async () => {
  setIsProcessing(true);
  try {
    const result = await transcriptService.processTranscript(formData);
    toast.success("Processing started successfully!");
  } catch (error) {
    toast.error(`Processing failed: ${error.message}`);
  } finally {
    setIsProcessing(false);
  }
};
```

**UI Feedback:**
- Loading spinners on buttons during processing
- Toast notifications for success/error states
- Disabled form inputs during processing
- Progress indicators where applicable

This feature mapping provides a complete understanding of how user-facing functionality connects to the underlying implementation, making it easier for developers to locate and modify specific features.
