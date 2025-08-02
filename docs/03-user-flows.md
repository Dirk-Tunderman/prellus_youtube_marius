# User Flows

## Concrete User Scenarios and Walkthroughs

This document provides detailed, step-by-step walkthroughs of key user scenarios, showing both what users see and what happens behind the scenes.

## Flow 1: Processing a YouTube Transcript

### User Scenario
Sarah, a content creator, wants to convert a 45-minute educational YouTube video into a polished transcript and audio file for her podcast.

### Step-by-Step Walkthrough

#### Step 1: Initial Setup
**What the user sees:**
- Opens browser to `http://localhost:5174`
- Sees the main transcript processing interface with two tabs: "Basic Info" and "Prompt Configuration"
- The "Basic Info" tab is active by default

**What happens behind the scenes:**
```javascript
// Frontend initialization
const App = () => (
  <TranscriptProvider>
    <ProjectProvider>
      <RouterProvider router={router} />
    </ProjectProvider>
  </TranscriptProvider>
);

// Context initializes with default state
const [formState, setFormState] = useState({
  url: "",
  title: "",
  duration: 0,
  voice: "bm_lewis", // Default British male voice
  speed: 0.8,
  promptData: {
    yourRole: "",
    scriptStructure: "",
    toneAndStyle: "",
    retentionAndFlow: "",
    additionalInstructions: "",
  },
});
```

#### Step 2: Enter YouTube URL
**What the user sees:**
- Enters YouTube URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Sees URL validation in real-time
- Duration field auto-populates (if available from metadata)

**What happens behind the scenes:**
```javascript
// URL validation with React Hook Form
const urlSchema = z.string().url().refine(
  (url) => url.includes('youtube.com') || url.includes('youtu.be'),
  { message: "Please enter a valid YouTube URL" }
);

// State update
setUrl("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
```

#### Step 3: Configure Voice Settings
**What the user sees:**
- Clicks on "Voice & Audio Settings" accordion
- Selects voice: "British Male - Lewis" from dropdown
- Adjusts speed slider to 0.9x (slightly faster)

**What happens behind the scenes:**
```javascript
// Voice selection updates context
setVoice("bm_lewis");
setSpeed(0.9);

// Voice options loaded from configuration
const voiceOptions = [
  { value: "bm_lewis", label: "British Male - Lewis", accent: "British", gender: "Male" },
  { value: "af_bella", label: "American Female - Bella", accent: "American", gender: "Female" },
  // ... more options
];
```

#### Step 4: Configure Processing Prompt
**What the user sees:**
- Switches to "Prompt Configuration" tab
- Sees structured prompt fields:
  - Your Role: "You are a podcast content editor..."
  - Script Structure: "Create clear sections with smooth transitions..."
  - Tone & Style: "Professional yet conversational..."
  - Retention & Flow: "Use storytelling techniques..."
  - Additional Instructions: "Focus on key insights..."

**What happens behind the scenes:**
```javascript
// Prompt data structure
const handlePromptChange = (field, value) => {
  setFormState(prev => ({
    ...prev,
    promptData: {
      ...prev.promptData,
      [field]: value
    }
  }));
};

// Validation ensures required fields are filled
const validateForm = () => {
  const errors = [];
  if (!url) errors.push("YouTube URL is required");
  if (!promptData.yourRole) errors.push("Role description is required");
  return errors;
};
```

#### Step 5: Start Processing
**What the user sees:**
- Clicks "Process Transcript" button
- Button shows loading spinner and changes to "Processing..."
- Success toast appears: "Processing started successfully!"

**What happens behind the scenes:**
```javascript
// Frontend API call
const handleProcessTranscript = async () => {
  try {
    const requestData = {
      url,
      title,
      duration,
      voice,
      speed,
      promptData
    };
    
    const result = await transcriptService.processTranscript(requestData);
    toast.success("Processing started successfully!");
    return { success: true, data: result };
  } catch (error) {
    toast.error(`Processing failed: ${error.message}`);
    return { success: false, error: error.message };
  }
};
```

#### Step 6: Backend Processing Pipeline
**What happens behind the scenes:**

1. **API Endpoint Receives Request**
```python
@app.route("/api/transcripts/process", methods=["POST"])
def process_transcript():
    data = request.json
    url = data.get("url")
    prompt_data = data.get("promptData", {})
    voice = data.get("voice")
    speed = data.get("speed")
    
    # Create combined prompt from structured fields
    combined_prompt = format_structured_prompt(prompt_data)
    
    # Inject settings into config
    config["ai"]["custom_prompt"] = combined_prompt
    config["ai"]["voice_pack"] = voice
    config["ai"]["speed"] = speed
    
    # Start pipeline
    result = youtube_to_audio(url, config, json_data=data)
    
    return jsonify({
        "id": "transcript_123",
        "title": data.get("title", "Processed Video"),
        "status": "processing",
        "message": "Transcript processing started"
    })
```

2. **Transcript Fetching**
```python
# app/src/transcript_pipeline/fetcher/fetch_and_store.py
def fetch_transcript(youtube_url, config, json_data=None):
    manager = TranscriptManager(config)
    
    # Extract video ID and fetch transcript
    transcript_data = manager.fetcher.fetch_transcript_with_metadata(youtube_url)
    
    # Create directory structure
    video_dir = manager.setup_video_directory(transcript_data["metadata"]["video_id"])
    
    # Save raw transcript and metadata
    raw_transcript_path = os.path.join(video_dir, "raw", "transcript.json")
    with open(raw_transcript_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2)
    
    return {
        "video_id": transcript_data["metadata"]["video_id"],
        "video_dir": video_dir,
        "transcript_data": transcript_data
    }
```

3. **AI Processing**
```python
# app/src/transcript_pipeline/processor/ai_processor.py
class TranscriptAIProcessor:
    def process_transcript(self, transcript_text):
        # Use LiteLLM for unified AI provider interface
        response = litellm.completion(
            model=self.model,  # e.g., "claude-3-7-sonnet-20250219"
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": transcript_text}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        processed_text = response.choices[0].message.content
        
        # Save processed transcript
        output_path = os.path.join(self.output_dir, "narrative_transcript.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
        
        return processed_text
```

4. **Audio Generation**
```python
# app/src/transcript_pipeline/tts/tts_generator.py
class TTSGenerator:
    def generate_audio(self, text, output_path, metadata):
        # Split text into chunks for processing
        chunks = self.split_text_into_chunks(text)
        audio_files = []
        
        for i, chunk in enumerate(chunks):
            chunk_file = f"chunk_{i:03d}.wav"
            
            # Generate audio with Kokoro TTS
            cmd = ['kokoro', 
                   '-l', self.language_code,  # 'b' for British
                   '-i', chunk_text_file,
                   '-o', chunk_file,
                   '-m', self.voice,          # 'bm_lewis'
                   '-s', str(self.speed)]     # '0.9'
            
            subprocess.run(cmd, check=True)
            audio_files.append(chunk_file)
        
        # Concatenate all audio chunks
        final_audio = self.concatenate_audio_files(audio_files)
        
        return {
            "output_path": output_path,
            "audio_duration_seconds": len(final_audio) / self.sample_rate,
            "chunks_processed": len(chunks)
        }
```

#### Step 7: View Results
**What the user sees:**
- Navigates to "Downloads" tab
- Sees new project listed with:
  - Title: "Rick Astley - Never Gonna Give You Up"
  - Date: "2025-08-02"
  - Status indicators: ✅ Transcript, ✅ Audio
- Can click "View Transcript" to see processed text
- Can download transcript file and audio file

**What happens behind the scenes:**
```javascript
// Downloads page loads projects
const { projects, isLoadingProjects } = useProjectData();

// Project data structure
const project = {
  id: "dQw4w9WgXcQ_20250802_143022",
  name: "Rick Astley - Never Gonna Give You Up",
  date: "2025-08-02T14:30:22",
  hasTranscript: true,
  audioFiles: ["final_audio.wav"],
  url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
};

// Download handlers
const handleDownloadTranscript = async (projectId) => {
  const response = await projectService.downloadTranscript(projectId);
  // Browser downloads file automatically
};
```

## Flow 2: Managing Custom Prompts

### User Scenario
Mark, a researcher, wants to create and save a custom prompt template for analyzing educational content, then reuse it for multiple videos.

### Step-by-Step Walkthrough

#### Step 1: Create Custom Prompt
**What the user sees:**
- In "Prompt Configuration" tab, fills out detailed prompt fields
- Clicks "Save Prompt" button
- Modal dialog appears asking for prompt name

**What happens behind the scenes:**
```javascript
// Save prompt dialog
const [showSavePrompt, setShowSavePrompt] = useState(false);
const [promptName, setPromptName] = useState("");

const handleSavePrompt = async () => {
  const promptData = {
    promptData: formState.promptData,
    promptName: promptName
  };
  
  await promptService.savePrompt(promptData);
  toast.success("Prompt saved successfully!");
  setShowSavePrompt(false);
};
```

#### Step 2: Backend Prompt Storage
**What happens behind the scenes:**
```python
@app.route("/api/prompts/save", methods=["POST"])
def save_prompt():
    data = request.json
    prompt_data = data.get("promptData", {})
    prompt_name = data.get("promptName", "Unnamed Prompt")
    
    # Create unique identifier and timestamp
    unique_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    # Structure prompt file
    prompt_file = {
        "meta_data": {
            "prompt_name": prompt_name,
            "date": timestamp,
            "unique_identifier": unique_id,
        },
        "prompt": {
            "Role": prompt_data.get("yourRole", ""),
            "Script_Structure": prompt_data.get("scriptStructure", ""),
            "Tone_Style": prompt_data.get("toneAndStyle", ""),
            "Retention_Flow": prompt_data.get("retentionAndFlow", ""),
            "Additional_instructions": prompt_data.get("additionalInstructions", ""),
        },
    }
    
    # Save to file system
    filename = f"{unique_id}.json"
    file_path = os.path.join(PROMPT_STORAGE_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(prompt_file, f, indent=2)
    
    return jsonify({
        "success": True,
        "promptId": unique_id,
        "promptName": prompt_name
    })
```

#### Step 3: Load Saved Prompt
**What the user sees:**
- Clicks "Load Prompt" button
- Modal shows list of saved prompts with names and dates
- Selects "Educational Content Analysis" prompt
- Form fields auto-populate with saved prompt data

**What happens behind the scenes:**
```javascript
const handleLoadPrompt = async (promptId) => {
  try {
    const promptData = await promptService.getPrompt(promptId);
    
    // Update form state with loaded prompt
    setFormState(prev => ({
      ...prev,
      promptData: promptData.promptData
    }));
    
    setShowPromptList(false);
    toast.success("Prompt loaded successfully!");
  } catch (error) {
    toast.error("Failed to load prompt");
  }
};
```

This comprehensive flow documentation shows how users interact with the system and provides insight into the underlying technical implementation at each step.
