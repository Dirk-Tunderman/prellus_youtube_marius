# System Architecture

## Detailed Architecture Breakdown

The YouTube Transcript Processor follows a **microservices architecture** with clear separation between frontend presentation, backend API, and processing pipeline components.

## Component Relationships and Interactions

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    React Frontend (Port 5174)                      │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ Transcript  │  │   Config    │  │  Downloads  │  │   Shared    │ │   │
│  │  │  Feature    │  │  Feature    │  │   Feature   │  │ Components  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    Core Services Layer                         │ │   │
│  │  │  • API Client (Axios)  • Router  • State Management           │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                     │
│                                      │ HTTP/REST API                       │
│                                      ▼                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Server Layer                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Flask API Server (Port 5001)                    │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │ Transcript  │  │   Prompt    │  │   Project   │  │   Config    │ │   │
│  │  │ Endpoints   │  │ Endpoints   │  │ Endpoints   │  │ Endpoints   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │                 Processing Orchestration                       │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                     │
│                                      │ Function Calls                      │
│                                      ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Processing Pipeline                              │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   Fetcher   │  │ AI Processor│  │ TTS Module  │  │   Utils     │ │   │
│  │  │   Module    │  │   Module    │  │             │  │   Module    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                     │
│                                      │ API Calls                           │
│                                      ▼                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                        External Services                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  YouTube    │  │   OpenAI    │  │   Google    │  │ Anthropic   │       │
│  │ Transcript  │  │     API     │  │   Gemini    │  │   Claude    │       │
│  │     API     │  └─────────────┘  └─────────────┘  └─────────────┘       │
│  └─────────────┘                                                           │
│                                                                             │
│  ┌─────────────┐  ┌─────────────────────────────────────────────────────┐ │
│  │  DeepSeek   │  │                Kokoro TTS                           │ │
│  │     API     │  │            (Local/System)                           │ │
│  └─────────────┘  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Request Processing Flow

```
User Action → Frontend → API Gateway → Processing Pipeline → External Services
     ↓            ↓           ↓              ↓                    ↓
  UI Event → State Update → HTTP Request → Business Logic → Service Calls
     ↓            ↓           ↓              ↓                    ↓
  Component → Context/Query → Flask Route → Pipeline Module → AI/TTS APIs
     ↓            ↓           ↓              ↓                    ↓
  Re-render ← State Update ← JSON Response ← Processed Data ← API Response
```

### Detailed Data Flow Example: Transcript Processing

1. **User Input** (Frontend)
   - User enters YouTube URL in `TranscriptForm`
   - Form validation with React Hook Form + Zod
   - State managed by `TranscriptContext`

2. **API Request** (Frontend → Backend)
   - `transcriptService.processTranscript()` called
   - Axios sends POST to `/api/transcripts/process`
   - Request includes URL, prompt data, voice settings

3. **Request Handling** (Backend)
   - Flask route `@app.route("/api/transcripts/process")` receives request
   - Validates input data and extracts parameters
   - Calls `youtube_to_audio()` pipeline function

4. **Pipeline Execution** (Backend Processing)
   - **Fetcher Module**: Downloads transcript from YouTube
   - **AI Processor Module**: Enhances transcript with selected AI model
   - **TTS Module**: Generates audio using Kokoro TTS
   - **Storage**: Saves results to file system

5. **Response** (Backend → Frontend)
   - Returns processing status and metadata
   - Frontend updates UI with success/error state
   - User can monitor progress and download results

## Important Design Patterns

### 1. Pipeline Pattern (Backend)
The processing pipeline follows a clear sequence of operations:

```python
# Pipeline stages
def youtube_to_audio(url, config, json_data=None):
    # Stage 1: Fetch transcript
    transcript_result = fetch_transcript(url, config, json_data)
    
    # Stage 2: Process with AI
    processed_result = process_transcript(
        transcript_result['video_dir'], 
        config
    )
    
    # Stage 3: Generate audio
    audio_result = generate_audio_from_transcript(
        processed_result['video_dir'], 
        config.get('ai', {})
    )
    
    return audio_result
```

### 2. Provider Pattern (AI Integration)
Unified interface for multiple AI providers using LiteLLM:

```python
class TranscriptAIProcessor:
    def __init__(self, config):
        self.model = config.get("model", "gemini-2.0-flash-lite")
        self.temperature = config.get("temperature", 0.7)
        
    def process_text(self, text, system_prompt=None):
        # LiteLLM handles provider-specific implementations
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=self.temperature
        )
        return response.choices[0].message.content
```

### 3. Context Pattern (Frontend)
Feature-specific contexts for state management:

```javascript
// TranscriptContext provides state and operations
export function TranscriptProvider({ children }) {
  const [formState, setFormState] = useState({...});
  
  const handleProcessTranscript = async () => {
    // Business logic for processing
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

### 4. Service Layer Pattern (Frontend)
Centralized API communication:

```javascript
// Core API service with error handling
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
    apiRequest(() => api.post("/transcripts/process", data))
};
```

### 5. Configuration-Driven Architecture
YAML-based configuration for flexibility:

```yaml
# app/config/config.yaml
ai:
  model: claude-3-7-sonnet-20250219
  temperature: 0.7
  max_tokens: 8192

tts:
  voice_pack: bm_lewis
  speed: 0.8

chunked_processing:
  chunk_size: 25000
  max_output_length: 28000
```

## Component Interaction Patterns

### Frontend Component Communication
- **Parent-Child**: Props for data down, callbacks for events up
- **Sibling Components**: Shared context for state synchronization
- **Cross-Feature**: Global contexts (TranscriptProvider, ProjectProvider)
- **Server State**: TanStack Query for caching and synchronization

### Backend Module Communication
- **Sequential Processing**: Pipeline stages execute in order
- **Configuration Injection**: Config passed through processing chain
- **Error Propagation**: Exceptions bubble up with context
- **Logging**: Structured logging throughout pipeline

### External Service Integration
- **API Abstraction**: LiteLLM provides unified AI provider interface
- **Retry Logic**: Built-in retry mechanisms for API failures
- **Rate Limiting**: Respect provider rate limits
- **Error Handling**: Graceful degradation on service failures

This architecture provides a robust, scalable foundation that separates concerns while maintaining clear communication patterns between components.
