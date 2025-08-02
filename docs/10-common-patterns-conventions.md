# Common Patterns and Conventions

## Coding Standards

### Backend Python Standards

#### Code Style and Formatting
- **PEP 8 Compliance:** Follow Python PEP 8 style guide
- **Line Length:** Maximum 88 characters (Black formatter standard)
- **Indentation:** 4 spaces (no tabs)
- **Import Organization:** Standard library, third-party, local imports

#### Example Code Style:
```python
"""
Module docstring explaining the purpose and functionality.

This module handles YouTube transcript processing with AI enhancement.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import yaml
import litellm
from flask import Flask, request, jsonify

# Module-level constants
DEFAULT_MODEL = "gemini-2.0-flash-lite"
MAX_RETRIES = 3

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """
    Process YouTube transcripts using AI models.
    
    This class handles the complete pipeline from raw transcript
    to polished narrative output.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transcript processor.
        
        Args:
            config: Configuration dictionary with AI settings
        """
        self.config = config or {}
        self.model = self.config.get("model", DEFAULT_MODEL)
        self.temperature = self.config.get("temperature", 0.7)
        
        logger.info(f"Initialized processor with model: {self.model}")
    
    def process_transcript(self, text: str) -> str:
        """
        Process transcript text using AI model.
        
        Args:
            text: Raw transcript text to process
            
        Returns:
            Processed transcript text
            
        Raises:
            ProcessingError: If AI processing fails
        """
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=self.temperature
            )
            
            processed_text = response.choices[0].message.content
            logger.info(f"Successfully processed {len(text)} characters")
            
            return processed_text
            
        except Exception as e:
            logger.exception(f"Failed to process transcript: {e}")
            raise ProcessingError(f"AI processing failed: {e}") from e
```

### Frontend JavaScript/React Standards

#### Code Style and Formatting
- **ESLint Configuration:** Use provided ESLint rules
- **Prettier Integration:** Automatic code formatting
- **Component Naming:** PascalCase for components, camelCase for functions
- **File Extensions:** `.jsx` for React components, `.js` for utilities

#### Example Code Style:
```javascript
/**
 * TranscriptProcessor Component
 * 
 * Handles YouTube transcript processing with AI enhancement.
 * Provides form interface for URL input and prompt customization.
 */

import { useState, useCallback } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { transcriptService } from "@/core/services";

// Component constants
const DEFAULT_VOICE = "bm_lewis";
const DEFAULT_SPEED = 0.8;

export function TranscriptProcessor() {
  // State declarations with descriptive names
  const [url, setUrl] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [formData, setFormData] = useState({
    voice: DEFAULT_VOICE,
    speed: DEFAULT_SPEED,
    promptData: {
      yourRole: "",
      scriptStructure: "",
      toneAndStyle: "",
      retentionAndFlow: "",
      additionalInstructions: "",
    },
  });

  // Event handlers with useCallback for performance
  const handleSubmit = useCallback(async (event) => {
    event.preventDefault();
    
    if (!url.trim()) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    setIsProcessing(true);
    
    try {
      const requestData = {
        url: url.trim(),
        ...formData,
      };
      
      const result = await transcriptService.processTranscript(requestData);
      
      toast.success("Processing started successfully!");
      console.log("Processing result:", result);
      
    } catch (error) {
      console.error("Processing failed:", error);
      toast.error(`Processing failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  }, [url, formData]);

  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="url" className="block text-sm font-medium mb-2">
          YouTube URL
        </label>
        <Input
          id="url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://youtube.com/watch?v=..."
          disabled={isProcessing}
          required
        />
      </div>
      
      <Button 
        type="submit" 
        disabled={isProcessing}
        className="w-full"
      >
        {isProcessing ? "Processing..." : "Process Transcript"}
      </Button>
    </form>
  );
}
```

## Naming Conventions

### Backend Naming Conventions

#### Files and Directories
```python
# Snake_case for Python files
fetch_and_store.py
ai_processor.py
youtube_transcript.py

# Descriptive directory names
transcript_pipeline/
stored_prompts/
```

#### Variables and Functions
```python
# Snake_case for variables and functions
def process_transcript(video_dir: str) -> Dict[str, Any]:
    transcript_text = load_transcript_text(video_dir)
    processed_result = enhance_with_ai(transcript_text)
    return processed_result

# UPPER_CASE for constants
DEFAULT_MODEL = "gemini-2.0-flash-lite"
MAX_CHUNK_SIZE = 25000
PROMPT_STORAGE_DIR = "app/data/stored_prompts"
```

#### Classes
```python
# PascalCase for classes
class TranscriptProcessor:
    pass

class YouTubeTranscriptFetcher:
    pass

class TTSGenerator:
    pass
```

### Frontend Naming Conventions

#### Components and Files
```javascript
// PascalCase for React components
TranscriptPage.jsx
PromptEditor.jsx
VoiceSelector.jsx

// camelCase for utilities and services
api.js
transcriptService.js
utils.js
```

#### Variables and Functions
```javascript
// camelCase for variables and functions
const handleProcessTranscript = async () => { };
const isProcessing = useState(false);
const formData = { };

// PascalCase for component names
const TranscriptForm = () => { };

// UPPER_SNAKE_CASE for constants
const DEFAULT_VOICE = "bm_lewis";
const API_BASE_URL = "http://localhost:5001/api";
```

## Error Handling Approaches

### Backend Error Handling

#### Structured Exception Handling
```python
class ProcessingError(Exception):
    """Custom exception for processing errors."""
    pass

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

def process_transcript(video_dir: str) -> Dict[str, Any]:
    """Process transcript with comprehensive error handling."""
    try:
        # Validate input
        if not os.path.exists(video_dir):
            raise ProcessingError(f"Video directory not found: {video_dir}")
        
        # Load configuration
        config = load_config()
        if not config.get("ai", {}).get("model"):
            raise ConfigurationError("AI model not configured")
        
        # Process transcript
        result = ai_processor.process(transcript_text)
        
        logger.info(f"Successfully processed transcript in {video_dir}")
        return result
        
    except ProcessingError as e:
        logger.error(f"Processing error: {e}")
        raise
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing transcript: {e}")
        raise ProcessingError(f"Processing failed: {e}") from e
```

#### API Error Responses
```python
@app.route("/api/transcripts/process", methods=["POST"])
def process_transcript():
    try:
        data = request.json
        
        # Validate required fields
        if not data.get("url"):
            return jsonify({"error": "YouTube URL is required"}), 400
        
        # Process request
        result = youtube_to_audio(data["url"], config, json_data=data)
        
        return jsonify({
            "success": True,
            "id": "transcript_123",
            "status": "processing"
        })
        
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400
    except ProcessingError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.exception(f"Unexpected API error: {e}")
        return jsonify({"error": "Internal server error"}), 500
```

### Frontend Error Handling

#### API Error Handling
```javascript
// Centralized API error handling
export const apiRequest = async (requestFn) => {
  try {
    console.log("[API] Making API request...");
    const response = await requestFn();
    console.log("[API] Request successful:", response.config.url);
    return response.data;
  } catch (error) {
    console.error("[API] Request failed:", error);
    
    // Extract meaningful error message
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        "An unexpected error occurred";
    
    // Show user-friendly error notification
    toast.error(`API Error: ${errorMessage}`);
    
    // Re-throw for component-level handling
    throw new Error(errorMessage);
  }
};
```

#### Component Error Handling
```javascript
const TranscriptProcessor = () => {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleProcessTranscript = async () => {
    setError(null);
    setIsLoading(true);
    
    try {
      // Validate input
      if (!url.trim()) {
        throw new Error("Please enter a YouTube URL");
      }
      
      if (!isValidYouTubeUrl(url)) {
        throw new Error("Please enter a valid YouTube URL");
      }
      
      // Make API request
      const result = await transcriptService.processTranscript(formData);
      
      // Handle success
      toast.success("Processing started successfully!");
      
    } catch (error) {
      console.error("Processing failed:", error);
      setError(error.message);
      toast.error(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Error display in UI
  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-md bg-red-50">
        <p className="text-red-800">{error}</p>
        <Button 
          onClick={() => setError(null)} 
          variant="outline" 
          size="sm" 
          className="mt-2"
        >
          Try Again
        </Button>
      </div>
    );
  }

  return (
    // Component JSX
  );
};
```

## Logging Practices

### Backend Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("youtube_to_audio.log"),
    ],
)

logger = logging.getLogger(__name__)

def process_transcript(video_dir: str) -> Dict[str, Any]:
    """Process transcript with comprehensive logging."""
    logger.info(f"Starting transcript processing for: {video_dir}")
    
    try:
        # Log processing steps
        logger.debug(f"Loading transcript from: {video_dir}")
        transcript_text = load_transcript_text(video_dir)
        logger.info(f"Loaded transcript: {len(transcript_text)} characters")
        
        logger.debug(f"Processing with AI model: {self.model}")
        processed_text = ai_processor.process(transcript_text)
        logger.info(f"AI processing complete: {len(processed_text)} characters")
        
        logger.info(f"Transcript processing completed successfully")
        return {"processed_text": processed_text}
        
    except Exception as e:
        logger.exception(f"Transcript processing failed: {e}")
        raise
```

### Frontend Logging
```javascript
// Console logging with consistent format
const logger = {
  info: (message, data = null) => {
    console.log(`[INFO] ${message}`, data || '');
  },
  
  error: (message, error = null) => {
    console.error(`[ERROR] ${message}`, error || '');
  },
  
  debug: (message, data = null) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[DEBUG] ${message}`, data || '');
    }
  }
};

// Usage in components
const handleProcessTranscript = async () => {
  logger.info("Starting transcript processing", { url, voice, speed });
  
  try {
    const result = await transcriptService.processTranscript(formData);
    logger.info("Processing request successful", result);
  } catch (error) {
    logger.error("Processing request failed", error);
    throw error;
  }
};
```

## Testing Strategies

### Backend Testing Approach
- **Unit Testing:** Test individual functions and classes
- **Integration Testing:** Test API endpoints and pipeline components
- **Mock Testing:** Use mock mode for AI API calls during development
- **Manual Testing:** Direct API testing with curl and Postman

### Frontend Testing Approach
- **Component Testing:** Test React components in isolation
- **Integration Testing:** Test user flows and API integration
- **Manual Testing:** Browser-based testing with React DevTools
- **Accessibility Testing:** Ensure WCAG compliance

### Example Test Patterns
```python
# Backend test example
def test_process_transcript_success():
    """Test successful transcript processing."""
    # Arrange
    video_dir = "test_data/sample_video"
    config = {"ai": {"model": "mock-model"}}
    
    # Act
    result = process_transcript(video_dir, config, mock_mode=True)
    
    # Assert
    assert result["success"] is True
    assert "processed_text" in result
    assert len(result["processed_text"]) > 0
```

```javascript
// Frontend test example (conceptual)
describe('TranscriptProcessor', () => {
  test('should handle form submission successfully', async () => {
    // Arrange
    const mockProcessTranscript = jest.fn().mockResolvedValue({ success: true });
    
    // Act
    render(<TranscriptProcessor />);
    fireEvent.change(screen.getByLabelText('YouTube URL'), {
      target: { value: 'https://youtube.com/watch?v=test' }
    });
    fireEvent.click(screen.getByText('Process Transcript'));
    
    // Assert
    await waitFor(() => {
      expect(mockProcessTranscript).toHaveBeenCalledWith({
        url: 'https://youtube.com/watch?v=test',
        // ... other form data
      });
    });
  });
});
```

These patterns and conventions ensure consistency, maintainability, and reliability across the entire codebase.
