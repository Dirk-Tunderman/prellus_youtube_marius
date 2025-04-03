"""
Transcript AI Processor Module

This module processes raw transcripts using LLM APIs (via LiteLLM) to transform
them into more engaging narratives while preserving the core educational content.
It uses a specialized system prompt to guide the transformation process.

The module is part of the Transcript Processing Pipeline and operates on 
the raw transcripts stored by the Transcript Fetcher module.
"""

import os
import json
import logging
import time
import re
import google.generativeai as genai
from typing import Dict, Any, Optional, List, Union, Tuple
import math

import litellm
from litellm.exceptions import BadRequestError, AuthenticationError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)

# System prompt for transcript transformation
TRANSCRIPT_TRANSFORMATION_PROMPT = """
You are a specialized transcript transformation assistant that converts YouTube transcripts into slightly modified versions while preserving the core content, structure, and educational value.
TASK DESCRIPTION
Your task is to transform a raw transcript into a more engaging narrative format while maintaining:

The exact same subject matter and educational content
The same overall length
The same sequence of topics and structure
The same time allocation to each subject
The same factual information and key points

You should modify:

The wording and phrasing to create a storytelling style
The sentence structure to improve flow and engagement
Transitions between topics to feel more natural
Technical explanations to be more accessible (without losing accuracy)

INPUT FORMAT
The input will be a raw transcript from a YouTube video, which may contain:

Speaker labels (if present in the original transcript)
Timestamps (which should be preserved if present)
Filler words, repetitions, and speech disfluencies
Technical terminology and specialized language
Potentially disorganized structure due to natural speech patterns

OUTPUT GUIDELINES
Content Preservation
<preserve>
- All key facts, data points, statistics, and educational content
- The overall argument or narrative arc
- All major examples, case studies, and illustrations
- Technical accuracy of all explanations
- The relative time/emphasis given to each subtopic
</preserve>
Style Transformation
<transform>
- Convert lecture-style explanations into storytelling narratives
- Replace academic language with more conversational phrasing
- Improve transitions between topics for smoother flow
- Reduce redundancies and speech disfluencies
- Enhance clarity while maintaining all original information
- Add light narrative elements that support the content
</transform>
Structure
<structure>
- Maintain the same overall organization of topics
- Preserve the logical flow of the original
- Keep the same introduction and conclusion themes
- Retain the same progression of ideas
- Maintain the same proportion of time/content for each section
</structure>
IMPORTANT RULES

Do NOT add new factual information that wasn't in the original transcript
Do NOT remove any substantive content from the original
Do NOT change the meaning of any technical explanations
Do NOT significantly alter the overall length
Do NOT change the subject matter or primary focus
Do NOT contradict any statements from the original transcript
Do NOT add personal opinions or bias not present in the original

CRITICAL:
- Do not include any timestamps
- Do not include any special characters like * [] () or others



OUTPUT FORMAT
Your output should be a cohesive, flowing transcript that reads like a well-crafted narrative while teaching the exact same content. If the original included speaker labels or timestamps, maintain these in your transformed version.
"""

class TranscriptProcessorInterface:
    """
    Interface for transcript processors.
    Defines the common methods that all processors should implement.
    """
    
    def process_text(self, text: str, system_prompt: Optional[str] = None) -> str:
        """
        Process a text using LLM API.
        
        Args:
            text: The text to process
            system_prompt: Optional custom system prompt to use
            
        Returns:
            The processed text
        """
        raise NotImplementedError("Subclasses must implement process_text")


class GeminiProcessor(TranscriptProcessorInterface):
    """
    Processor that uses the Gemini API to process text.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Gemini processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize the model configuration
        self.model = config.get("model", "gemini-2.0-flash-lite")
        self.raw_model_name = self.model
        
        # Configure API key for Google GenerativeAI
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # Try to load from .env file if not in environment
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
                
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set for Gemini models")
        
        # Configure Google GenerativeAI
        genai.configure(api_key=api_key)
        self.logger.info(f"Using Google GenerativeAI with model: {self.model}")
        
        # Strip 'models/' prefix if it exists to get the model ID
        self.model_id = self.model
        if not self.model.startswith("models/"):
            self.model_id = f"models/{self.model}"
        
        self.logger.info(f"Using model ID: {self.model_id}")
        
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
    
    def process_text(self, text: str, system_prompt: Optional[str] = None) -> str:
        """
        Process a text using Gemini API.
        
        Args:
            text: The text to process
            system_prompt: Optional custom system prompt to use
            
        Returns:
            The processed text
        """
        try:
            logger.info(f"Processing text with Gemini model: {self.model}")
            
            # Check for mock mode
            if os.environ.get("MOCK_LLM_API") == "true":
                logger.info("Using mock LLM API mode")
                return f"Mock processed text: {text[:100]}..."
            
            # For Gemini, combine the system prompt and user text
            prompt = system_prompt or ""
            combined_prompt = f"{prompt}\n\n{text}"
            logger.info(f"Using combined prompt (total length: {len(combined_prompt)})")
            
            # Get the model
            model = genai.GenerativeModel(self.model_id)
            
            # Generate the response

            response = model.generate_content(
                combined_prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            # Extract the text from the response
            processed_text = response.text
            logger.info(f"Received response from Gemini. Length: {len(processed_text)}")
            return processed_text
            
        except Exception as e:
            logger.exception(f"Error processing text with Gemini: {e}")
            raise


class TranscriptAIProcessor(TranscriptProcessorInterface):
    """
    Class for processing transcripts using LLM APIs.
    
    This class transforms raw transcripts into more engaging narratives
    using LiteLLM to interact with various LLM providers (focusing on Gemini).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the transcript AI processor with configuration parameters.
        
        Args:
            config: Configuration parameters for the processor
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize the model configuration
        self.model = config.get("model", "gemini-2.0-flash-lite")
        self.raw_model_name = self.model
    
        # Configure API key for Google GenerativeAI if using Gemini models
        if "gemini" in self.model.lower():
            # Check for GOOGLE_API_KEY first, then GEMINI_API_KEY as fallback
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                # Try to load from .env file if not in environment
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.environ.get("GEMINI_API_KEY")
                
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set for Gemini models")
            
            # Configure Google GenerativeAI
            genai.configure(api_key=api_key)
            self.logger.info(f"Using Google GenerativeAI with model: {self.model}")
            
            # Strip 'models/' prefix if it exists to get the model ID
            self.model_id = self.model
            if not self.model.startswith("models/"):
                self.model_id = f"models/{self.model}"
            
            self.logger.info(f"Using model ID: {self.model_id}")
        
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
        self.logger.info(f"Initialized AI Processor with model: {self.model}")
        
        # Mock mode for testing
        self.mock_mode = os.environ.get("MOCK_LLM_API", "false").lower() == "true"
        if self.mock_mode:
            self.logger.info("Using mock LLM API response (MOCK_LLM_API=true)")
        
        # System prompt
        self.system_prompt = TRANSCRIPT_TRANSFORMATION_PROMPT
    
    def process_transcript(self, transcript_text: str) -> str:
        """
        Process a transcript using the LLM API.
        
        Args:
            transcript_text (str): Raw transcript text to process
            
        Returns:
            str: Processed transcript text
            
        Raises:
            Exception: If the API call fails
        """
        try:
            logger.info(f"Processing transcript with model: {self.model}")
            
            # Use the improved process_text method which properly handles system prompts
            processed_text = self.process_text(
                text=transcript_text,
                system_prompt=self.system_prompt
            )
            
            logger.info("Successfully processed transcript with LLM")
            return processed_text
            
        except Exception as e:
            logger.exception(f"Error processing transcript with LLM: {e}")
            raise
    
    def process_text(self, text: str, system_prompt: Optional[str] = None, model: Optional[str] = None) -> str:
        """
        Process a text using LLM API.
        
        Args:
            text: The text to process
            system_prompt: Optional custom system prompt to use
            model: Optional model override
            
        Returns:
            The processed text
        """
        # Use custom prompt if provided, otherwise use default
        prompt = system_prompt or self.system_prompt
        
        # Use custom model if provided, otherwise use default
        model_to_use = model or self.model
        raw_model_name = getattr(self, 'raw_model_name', model_to_use)
        
        try:
            logger.info(f"Processing text with model: {raw_model_name}")
            
            # Check for mock mode
            if os.environ.get("MOCK_LLM_API") == "true":
                logger.info("Using mock LLM API mode")
                return f"Mock processed text: {text[:100]}..."
            
            # Prepare messages for the API call
            if "gemini" in raw_model_name.lower():
                # For Gemini, combine the system prompt and user text
                combined_prompt = f"{prompt}\n\n{text}"
                logger.info(f"Using combined prompt with system instructions and text (total length: {len(combined_prompt)})")
                
                # Get the model
                model_id = f"models/{model_to_use}" if not model_to_use.startswith("models/") else model_to_use
                model = genai.GenerativeModel(model_id)
                
                # Generate the response
                response = model.generate_content(
                    combined_prompt,
                    generation_config={
                        "max_output_tokens": self.max_tokens,
                        "temperature": self.temperature
                    }
                )
                
                # Extract the text from the response
                processed_text = response.text
                logger.info(f"Received response from Google GenerativeAI. Length: {len(processed_text)}")
                return processed_text
            else:
                # For other models, use LiteLLM's chat format
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ]
                
                response = litellm.completion(
                    model=model_to_use,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                processed_text = response.choices[0].message.content
                logger.info(f"Received response from LiteLLM. Length: {len(processed_text)}")
                return processed_text
            
        except Exception as e:
            logger.exception(f"Error processing text with LLM: {e}")
            raise


class TranscriptProcessor:
    """
    Class for managing the transcript processing workflow.
    
    This class coordinates loading the raw transcript, processing it with the AI,
    and saving the processed transcript to the appropriate location.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transcript processor.
        
        Args:
            config (Dict[str, Any], optional): Configuration parameters.
        """
        self.config = config or {}
        ai_config = self.config.get("ai", {})
        self.ai_processor = TranscriptAIProcessor(ai_config)
        logger.info("Initialized TranscriptProcessor")
    
    def process_transcript_directory(self, video_dir: str) -> Dict[str, Any]:
        """
        Process all transcript files in a video directory.
        
        Args:
            video_dir (str): Path to the video directory
            
        Returns:
            Dict[str, Any]: Information about the processed files
            
        Raises:
            FileNotFoundError: If required files are not found
            Exception: If processing fails
        """
        try:
            # Verify directory structure
            raw_dir = os.path.join(video_dir, "raw")
            processed_dir = os.path.join(video_dir, "processed")
            
            if not os.path.exists(raw_dir):
                raise FileNotFoundError(f"Raw transcript directory not found: {raw_dir}")
            
            # Ensure processed directory exists
            os.makedirs(processed_dir, exist_ok=True)
            
            # Load the text transcript
            raw_text_path = os.path.join(raw_dir, "transcript.txt")
            if not os.path.exists(raw_text_path):
                raise FileNotFoundError(f"Raw text transcript not found: {raw_text_path}")
            
            with open(raw_text_path, 'r', encoding='utf-8') as f:
                raw_transcript_text = f.read()
            
            # Process the transcript
            logger.info(f"Processing transcript in directory: {video_dir}")
            processed_text = self.ai_processor.process_transcript(raw_transcript_text)
            
            # Save the processed transcript
            processed_text_path = os.path.join(processed_dir, "narrative_transcript.txt")
            with open(processed_text_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            # Also save a JSON version with metadata
            processed_json_path = os.path.join(processed_dir, "narrative_transcript.json")
            
            # Get metadata to include
            metadata = {}
            metadata_path = os.path.join(video_dir, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # Create the processed data structure
            processed_data = {
                "metadata": metadata,
                "processing_info": {
                    "model": self.ai_processor.raw_model_name,
                    "temperature": self.ai_processor.temperature,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "processed_transcript": processed_text
            }
            
            with open(processed_json_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2)
            
            logger.info(f"Successfully processed transcript. Results saved to {processed_dir}")
            
            return {
                "video_dir": video_dir,
                "processed_text_path": processed_text_path,
                "processed_json_path": processed_json_path,
                "processing_info": processed_data["processing_info"]
            }
            
        except Exception as e:
            logger.exception(f"Error processing transcript directory: {e}")
            raise


def process_transcript(video_dir: str, config: Optional[Dict[str, Any]] = None, mock_mode: bool = False) -> Dict[str, Any]:
    """
    Process a transcript from a video directory.
    
    This function reads a raw transcript from a video directory, processes it using
    the appropriate processor (standard or chunked), and saves the processed output.
    
    Args:
        video_dir: Path to the video directory
        config: Configuration parameters
        mock_mode: If True, use mock mode without making actual API calls
        
    Returns:
        A dictionary with metadata about the processing
    """
    config = config or {}

    # Set mock mode if requested
    if mock_mode:
        os.environ["MOCK_LLM_API"] = "true"

    # Read the raw transcript
    raw_transcript_path = os.path.join(video_dir, "raw", "transcript.txt")
    if not os.path.exists(raw_transcript_path):
        raise FileNotFoundError(f"Raw transcript not found at {raw_transcript_path}")
    
    with open(raw_transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    

    expected_transcript_length = config["ai"]["length_in_chars"]
    print(f"expected_transcript_length: {expected_transcript_length}")
    # Determine whether to use standard or chunked processing
    large_transcript_threshold = config.get("large_transcript_threshold", 15000)
    is_large_transcript = expected_transcript_length > large_transcript_threshold
    
    start_time = time.time()
    
    # Create processed directory if it doesn't exist
    processed_dir = os.path.join(video_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    if is_large_transcript:
        logger.info(f"Using chunked processor for large transcript ({len(transcript_text)} characters)")
        # Import here to avoid circular imports
        from .chunked_processor import process_large_transcript
        processed_transcript = process_large_transcript(
            transcript_text=transcript_text,
            config=config,
            mock_mode=mock_mode,
            output_dir=processed_dir
        )
    
        # Calculate the number of chunks based on chunk size
        chunk_size = config.get("chunk_size", 20000)
        num_chunks = math.ceil(len(transcript_text) / chunk_size)
        
        # Check if chunks_info.json was created by the chunked processor
        chunks_info_path = os.path.join(processed_dir, "chunks_info.json")
        if os.path.exists(chunks_info_path):
            with open(chunks_info_path, 'r', encoding='utf-8') as f:
                chunks_info = json.load(f)
            logger.info(f"Loaded chunks info from {chunks_info_path}")
        else:
            # Add chunk info to metadata (legacy fallback)
            chunks_info = []
            for i in range(num_chunks):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(transcript_text))
                chunk_len = end_idx - start_idx
                chunks_info.append({
                    "chunk_index": i,
                    "original_length": chunk_len,
                    "processed_length": len(processed_transcript) / num_chunks,  # Estimate
                    "start_char": start_idx,
                    "end_char": end_idx
                })
    else:
        logger.info(f"Using standard processor for transcript ({len(transcript_text)} characters)")
        # Initialize the processor
        processor = TranscriptAIProcessor(config.get("ai", {}))
        
        # Process the transcript
        processed_transcript = processor.process_text(transcript_text)
        
        # Initialize empty chunks_info for standard processing
        chunks_info = []
    
    processing_time = time.time() - start_time
    
    # Save the processed transcript
    output_path = os.path.join(processed_dir, "narrative_transcript.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed_transcript)
    
    # Create metadata
    metadata = {
        "processing_time_seconds": processing_time,
        "original_length": len(transcript_text),
        "processed_length": len(processed_transcript),
        "processing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "large_transcript": is_large_transcript,
        "processing_method": "chunked" if is_large_transcript else "standard",
        "mock_mode": mock_mode,
        "num_chunks": len(chunks_info) if is_large_transcript else 1,
        "chunks_info": chunks_info
    }
    
    # Save metadata
    metadata_path = os.path.join(processed_dir, "narrative_transcript.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Processed transcript saved to {output_path}")
    
    # Return both the metadata and the processed file path
    return {
        "metadata": metadata,
        "processed_file": output_path
    }