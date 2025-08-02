# API Documentation

## Base URL and Authentication

**Base URL:** `http://localhost:5001/api`

**Authentication:** No authentication required for local development. API keys for AI providers are managed through configuration endpoints.

**Content-Type:** All requests should use `application/json`

**CORS:** Enabled for all origins in development mode

## Core API Endpoints

### Health Check

#### GET `/test`
Test API connectivity and server status.

**Response:**
```json
{
  "status": "ok",
  "message": "API is working on port 5001"
}
```

**Example:**
```bash
curl http://localhost:5001/api/test
```

## Transcript Processing Endpoints

### Process YouTube Transcript

#### POST `/transcripts/process`
Process a YouTube video transcript with AI enhancement and optional audio generation.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "duration": 213,
  "voice": "bm_lewis",
  "speed": 0.8,
  "promptData": {
    "yourRole": "You are an educational content editor...",
    "scriptStructure": "Create clear sections with smooth transitions...",
    "toneAndStyle": "Professional yet conversational...",
    "retentionAndFlow": "Use storytelling techniques...",
    "additionalInstructions": "Focus on key insights and practical applications..."
  }
}
```

**Response:**
```json
{
  "id": "transcript_123",
  "title": "Rick Astley - Never Gonna Give You Up",
  "status": "processing",
  "message": "Transcript processing started"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/transcripts/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "promptData": {
      "yourRole": "Educational content editor",
      "scriptStructure": "Clear sections with examples"
    },
    "voice": "bm_lewis",
    "speed": 0.8
  }'
```

### Get Transcript List

#### GET `/transcripts`
Retrieve a list of mock transcripts (for compatibility).

**Response:**
```json
[
  {
    "id": "1",
    "title": "Introduction to AI",
    "url": "https://www.youtube.com/watch?v=abc123",
    "createdAt": "2023-04-15",
    "status": "completed",
    "audioStatus": "completed",
    "audioUrl": "https://example.com/audio/transcript_1.mp3"
  }
]
```

## Prompt Management Endpoints

### Save Prompt Template

#### POST `/prompts/save`
Save a custom prompt template for reuse.

**Request Body:**
```json
{
  "promptName": "Educational Content Template",
  "promptData": {
    "yourRole": "You are an educational content editor...",
    "scriptStructure": "Create clear sections with examples...",
    "toneAndStyle": "Professional yet accessible...",
    "retentionAndFlow": "Use examples and analogies...",
    "additionalInstructions": "Focus on practical applications..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prompt saved successfully",
  "promptId": "af0717d3-b333-48e7-931e-45ddcea4f40c",
  "promptName": "Educational Content Template"
}
```

### List Saved Prompts

#### GET `/prompts`
Retrieve all saved prompt templates.

**Response:**
```json
[
  {
    "unique_id": "af0717d3-b333-48e7-931e-45ddcea4f40c",
    "prompt_name": "Educational Content Template",
    "date": "2025-08-02T14:30:22",
    "filename": "af0717d3-b333-48e7-931e-45ddcea4f40c.json"
  }
]
```

### Get Specific Prompt

#### GET `/prompts/{prompt_id}`
Retrieve a specific prompt template by ID.

**Response:**
```json
{
  "promptData": {
    "yourRole": "You are an educational content editor...",
    "scriptStructure": "Create clear sections with examples...",
    "toneAndStyle": "Professional yet accessible...",
    "retentionAndFlow": "Use examples and analogies...",
    "additionalInstructions": "Focus on practical applications..."
  },
  "metaData": {
    "prompt_name": "Educational Content Template",
    "date": "2025-08-02T14:30:22",
    "unique_identifier": "af0717d3-b333-48e7-931e-45ddcea4f40c"
  }
}
```

### Delete Prompt

#### DELETE `/prompts/{prompt_id}`
Delete a saved prompt template.

**Response:**
```json
{
  "success": true,
  "message": "Prompt af0717d3-b333-48e7-931e-45ddcea4f40c deleted successfully"
}
```

## Project Management Endpoints

### Get All Projects

#### GET `/projects`
Retrieve all processed transcript projects.

**Response:**
```json
[
  {
    "id": "dQw4w9WgXcQ_20250802_143022",
    "name": "Rick Astley - Never Gonna Give You Up",
    "date": "2025-08-02T14:30:22",
    "hasTranscript": true,
    "audioFiles": ["final_audio.wav"],
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }
]
```

### Get Project Transcript

#### GET `/projects/{project_id}/transcript`
Retrieve the processed transcript text for a project.

**Response:**
```json
{
  "projectId": "dQw4w9WgXcQ_20250802_143022",
  "text": "We're no strangers to love, you know the rules and so do I..."
}
```

### Download Transcript File

#### GET `/projects/{project_id}/transcript/download`
Download the transcript as a text file.

**Response:** File download with appropriate headers
- `Content-Type: text/plain`
- `Content-Disposition: attachment; filename="Rick_Astley_transcript.txt"`

### Download Audio File

#### GET `/projects/{project_id}/audio/{filename}`
Download an audio file for a project.

**Response:** File download with appropriate headers
- `Content-Type: audio/wav`
- `Content-Disposition: attachment; filename="final_audio.wav"`

### Delete Project

#### DELETE `/projects/{project_id}`
Delete an entire project and all its files.

**Response:**
```json
{
  "success": true,
  "message": "Project dQw4w9WgXcQ_20250802_143022 deleted successfully"
}
```

## Configuration Management Endpoints

### Get API Keys Status

#### GET `/config/apikeys`
Check which API keys are configured (without revealing the actual keys).

**Response:**
```json
{
  "openai": true,
  "gemini": false,
  "anthropic": true,
  "deepseek": false,
  "qwen": false
}
```

### Save API Key

#### POST `/config/apikeys`
Save an API key for a specific provider.

**Request Body:**
```json
{
  "provider": "openai",
  "key": "sk-your-api-key-here"
}
```

**Response:**
```json
{
  "success": true
}
```

### Delete API Key

#### DELETE `/config/apikeys/{provider}`
Remove an API key for a specific provider.

**Response:**
```json
{
  "success": true
}
```

### Get Available Models

#### GET `/config/models`
Get list of available AI models based on configured API keys.

**Response:**
```json
[
  {
    "value": "gpt-4",
    "label": "OpenAI GPT-4",
    "provider": "openai",
    "available": true
  },
  {
    "value": "gemini-pro",
    "label": "Google Gemini Pro",
    "provider": "gemini",
    "available": false
  }
]
```

### Get Default Model

#### GET `/config/defaultmodel`
Get the currently configured default AI model.

**Response:**
```json
{
  "model": "claude-3-7-sonnet-20250219"
}
```

### Set Default Model

#### POST `/config/defaultmodel`
Set the default AI model for processing.

**Request Body:**
```json
{
  "model": "gpt-4"
}
```

**Response:**
```json
{
  "success": true
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": "Error message describing what went wrong",
  "success": false
}
```

### Common HTTP Status Codes
- **200 OK:** Request successful
- **400 Bad Request:** Invalid request data
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server processing error

### Example Error Responses

**400 Bad Request:**
```json
{
  "error": "YouTube URL is required",
  "success": false
}
```

**404 Not Found:**
```json
{
  "error": "Prompt not found",
  "success": false
}
```

**500 Internal Server Error:**
```json
{
  "error": "Pipeline error: Failed to process transcript",
  "success": false
}
```

## Data Formats

### Prompt Data Structure
```json
{
  "yourRole": "String - Description of the AI's role",
  "scriptStructure": "String - Instructions for content structure",
  "toneAndStyle": "String - Tone and style guidelines",
  "retentionAndFlow": "String - Engagement and flow techniques",
  "additionalInstructions": "String - Any additional processing instructions"
}
```

### Voice Options
- `bm_lewis` - British Male Lewis
- `af_bella` - American Female Bella
- `am_adam` - American Male Adam
- `bf_emma` - British Female Emma

### Speed Range
- Minimum: `0.5` (half speed)
- Maximum: `2.0` (double speed)
- Default: `0.8` (slightly slower than normal)

This API documentation provides complete reference for integrating with the YouTube Transcript Processor backend.
