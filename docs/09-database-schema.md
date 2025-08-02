# Database Schema and Data Storage

## Storage Architecture Overview

The YouTube Transcript Processor uses a **file-based storage system** instead of a traditional database. This approach provides simplicity, portability, and eliminates the need for database setup and maintenance.

## File-Based Storage Structure

### Root Data Directory
```
app/data/
├── stored_prompts/          # Prompt template storage
└── transcripts/            # Project data storage
```

## Data Models and File Formats

### 1. Prompt Templates (`app/data/stored_prompts/`)

**File Pattern:** `{uuid}.json`

**Purpose:** Store reusable prompt templates for AI processing

**Schema:**
```json
{
  "meta_data": {
    "prompt_name": "string",           // User-defined prompt name
    "date": "ISO 8601 timestamp",     // Creation timestamp
    "unique_identifier": "UUID v4"    // Unique identifier
  },
  "prompt": {
    "Role": "string",                  // AI role description
    "Script_Structure": "string",     // Content structure instructions
    "Tone_Style": "string",           // Tone and style guidelines
    "Retention_Flow": "string",       // Engagement techniques
    "Additional_instructions": "string" // Extra processing instructions
  }
}
```

**Example:**
```json
{
  "meta_data": {
    "prompt_name": "Educational Content Template",
    "date": "2025-08-02T14:30:22.123456",
    "unique_identifier": "af0717d3-b333-48e7-931e-45ddcea4f40c"
  },
  "prompt": {
    "Role": "You are an educational content editor who transforms video transcripts into engaging narratives.",
    "Script_Structure": "Create clear sections with smooth transitions between concepts.",
    "Tone_Style": "Professional yet accessible, explaining complex concepts simply.",
    "Retention_Flow": "Use examples and analogies to make concepts memorable.",
    "Additional_instructions": "Focus on practical applications and real-world examples."
  }
}
```

### 2. Project Data (`app/data/transcripts/`)

**Directory Pattern:** `{video_id}_{timestamp}/`

**Purpose:** Store all data related to a processed YouTube video

#### Project Directory Structure
```
{video_id}_{timestamp}/
├── raw/                    # Original transcript data
│   ├── transcript.json     # Raw transcript with metadata
│   └── transcript.txt      # Plain text version
├── processed/              # AI-processed results
│   ├── narrative_transcript.txt    # Final processed transcript
│   └── narrative_transcript.json  # Processed transcript with metadata
├── audio/                  # Generated audio files
│   ├── chunk_000.wav      # Individual audio chunks
│   ├── chunk_001.wav
│   ├── ...
│   └── final_audio.wav    # Concatenated final audio
└── metadata.json          # Project metadata
```

#### Raw Transcript Schema (`raw/transcript.json`)
```json
{
  "transcript": [
    {
      "text": "string",        // Transcript segment text
      "start": "float",     // Start time in seconds
      "duration": "float"   // Duration in seconds
    }
  ],
  "metadata": {
    "video_id": "string",           // YouTube video ID
    "title": "string",             // Video title
    "duration": "integer",         // Video duration in seconds
    "language": "string",          // Transcript language code
    "fetched_at": "ISO timestamp", // When transcript was fetched
    "source": "string"             // Source (e.g., "youtube_transcript_api")
  }
}
```

#### Project Metadata Schema (`metadata.json`)
```json
{
  "timestamp": "ISO 8601 timestamp",    // Project creation time
  "url": "string",                      // Original YouTube URL
  "title": "string",                    // Video title
  "prompt": "string",                   // Combined prompt used for processing
  "promptData": {                       // Structured prompt data
    "yourRole": "string",
    "scriptStructure": "string",
    "toneAndStyle": "string",
    "retentionAndFlow": "string",
    "additionalInstructions": "string"
  },
  "voice": "string",                    // TTS voice used
  "speed": "float",                     // TTS speed setting
  "processing_info": {                  // Processing metadata
    "model": "string",                  // AI model used
    "temperature": "float",             // AI temperature setting
    "processed_at": "ISO timestamp"     // Processing completion time
  }
}
```

#### Processed Transcript Schema (`processed/narrative_transcript.json`)
```json
{
  "metadata": {
    "video_id": "string",
    "title": "string",
    "original_length": "integer",       // Original transcript character count
    "processed_length": "integer",     // Processed transcript character count
    "processing_time": "float"         // Processing time in seconds
  },
  "processing_info": {
    "model": "string",                  // AI model used
    "temperature": "float",             // Temperature setting
    "processed_at": "ISO timestamp",   // Processing timestamp
    "chunks_processed": "integer"      // Number of chunks (for large transcripts)
  },
  "processed_transcript": "string"     // Final processed transcript text
}
```

## Data Relationships

### Prompt Templates → Projects
- **Relationship Type:** Many-to-Many (conceptual)
- **Implementation:** Prompt data is copied into project metadata
- **Rationale:** Projects are self-contained and don't depend on external prompt files

### Projects → Files
- **Relationship Type:** One-to-Many
- **Implementation:** Directory structure with multiple file types
- **Files per Project:**
  - 1 metadata file
  - 1-2 raw transcript files
  - 1-2 processed transcript files
  - 1-N audio chunk files
  - 1 final audio file

## Data Access Patterns

### Reading Data

#### Load All Prompts
```python
def get_all_prompts():
    prompts = []
    for filename in os.listdir(PROMPT_STORAGE_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(PROMPT_STORAGE_DIR, filename), 'r') as f:
                prompt_data = json.load(f)
                prompts.append(prompt_data["meta_data"])
    return sorted(prompts, key=lambda x: x.get("date", ""), reverse=True)
```

#### Load All Projects
```python
def get_projects():
    projects = []
    transcripts_dir = "app/data/transcripts"
    
    for project_name in os.listdir(transcripts_dir):
        project_path = os.path.join(transcripts_dir, project_name)
        if os.path.isdir(project_path):
            metadata_path = os.path.join(project_path, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                projects.append({
                    "id": project_name,
                    "name": metadata.get("title", project_name),
                    "date": metadata.get("timestamp", "Unknown"),
                    "hasTranscript": os.path.exists(
                        os.path.join(project_path, "processed", "narrative_transcript.txt")
                    ),
                    "audioFiles": [
                        f for f in os.listdir(os.path.join(project_path, "audio"))
                        if f.endswith(".wav")
                    ] if os.path.exists(os.path.join(project_path, "audio")) else [],
                    "url": metadata.get("url", "")
                })
    
    return sorted(projects, key=lambda x: x.get("id", ""), reverse=True)
```

### Writing Data

#### Save Prompt Template
```python
def save_prompt_to_file(prompt_data, prompt_name):
    unique_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
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
    
    filename = f"{unique_id}.json"
    file_path = os.path.join(PROMPT_STORAGE_DIR, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(prompt_file, f, indent=2)
    
    return {
        "success": True,
        "filename": filename,
        "unique_id": unique_id,
        "timestamp": timestamp,
    }
```

#### Create Project Directory
```python
def setup_video_directory(video_id):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = os.path.join(self.base_output_dir, f"{video_id}_{timestamp}")
    
    # Create directory structure
    os.makedirs(os.path.join(video_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(video_dir, "processed"), exist_ok=True)
    os.makedirs(os.path.join(video_dir, "audio"), exist_ok=True)
    
    return video_dir
```

## Data Migration and Backup

### Backup Strategy
```bash
# Backup all data
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz app/data/

# Backup only prompts
tar -czf prompts_backup_$(date +%Y%m%d_%H%M%S).tar.gz app/data/stored_prompts/

# Backup specific project
tar -czf project_backup_$(date +%Y%m%d_%H%M%S).tar.gz app/data/transcripts/{project_id}/
```

### Data Migration
Since the system uses file-based storage, migration involves:
1. **File System Operations:** Copy/move directories
2. **Format Validation:** Ensure JSON files are valid
3. **Schema Updates:** Update file formats if schema changes

### Data Integrity
- **Atomic Writes:** Use temporary files and atomic moves
- **Validation:** JSON schema validation on read/write
- **Error Handling:** Graceful handling of corrupted files
- **Logging:** Comprehensive logging of all data operations

## Storage Considerations

### Advantages of File-Based Storage
- **Simplicity:** No database setup or maintenance
- **Portability:** Easy to backup, move, and inspect
- **Transparency:** Human-readable JSON files
- **Version Control:** Can be tracked in Git if needed
- **No Dependencies:** No database server required

### Limitations
- **Scalability:** Not suitable for high-volume concurrent access
- **Querying:** Limited query capabilities compared to SQL
- **Transactions:** No ACID transaction support
- **Concurrency:** Basic file locking only

### Performance Characteristics
- **Read Performance:** Fast for small to medium datasets
- **Write Performance:** Good for append-heavy workloads
- **Storage Efficiency:** JSON overhead, but human-readable
- **Memory Usage:** Loads entire files into memory

This file-based storage system provides a robust, simple solution for the YouTube Transcript Processor's data persistence needs while maintaining transparency and ease of management.
