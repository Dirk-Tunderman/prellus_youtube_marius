"""
Text-to-Speech Generator Module

This module provides functionality to convert processed transcripts into audio using
the Kokoro TTS engine, a lightweight but high-quality open-source text-to-speech model.

It handles text preprocessing, chunking long texts for efficient processing, and combining
the resulting audio segments into a cohesive output file.
"""

import os
import logging
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
import re

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

class TTSGenerator:
    """
    Text-to-Speech Generator using the Kokoro TTS engine.
    
    This class provides methods to convert text to speech using Kokoro,
    a lightweight but high-quality open-source TTS model.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TTS Generator with configuration.
        
        Args:
            config: Configuration dictionary for TTS settings
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default configuration values
        self.language_code = self.config.get("language", "b")  # Default language code (b for British English)
        self.voice = self.config.get("voice_pack", "bm_lewis")  # Default voice set to British Male George
        self.sample_rate = 24000  # Fixed sample rate for Kokoro
        self.output_format = self.config.get("output_format", "wav")
        self.max_chunk_length = self.config.get("max_chunk_length", 500)  # Max characters per chunk
        self.pause_between_chunks = self.config.get("pause_between_chunks", 0.7)  # Seconds
        self.speed = self.config.get("speed", 0.8)  # Speech speed set to 0.9
        
        # Check if kokoro command is available
        self._check_kokoro_available()
        
        # Language code map for reference (corrected)
        self.language_map = {
            "a": "American English",
            "b": "British English",
            "e": "Spanish",
            "f": "French",
            "h": "Hindi",
            "i": "Italian",
            "p": "Brazilian Portuguese",
            "j": "Japanese",
            "z": "Mandarin Chinese"
        }
        
        self.logger.info(f"Initialized Kokoro TTS generator with language: {self.language_map.get(self.language_code, self.language_code)} and voice: {self.voice}")
        self.logger.info(f"Using speech speed: {self.speed}x")
    
    def _check_kokoro_available(self):
        """Check if the kokoro command is available in the system path."""
        try:
            result = subprocess.run(['which', 'kokoro'], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning("Kokoro command not found in PATH. Make sure it's installed.")
            else:
                self.logger.info(f"Found kokoro at: {result.stdout.strip()}")
                
                # Check command syntax by running help
                try:
                    help_result = subprocess.run(['kokoro', '--help'], capture_output=True, text=True)
                    if "--voice" in help_result.stdout or "--voice" in help_result.stderr:
                        self.logger.info("Detected new Kokoro syntax using --voice")
                        self.use_new_syntax = True
                    else:
                        self.logger.info("Using legacy Kokoro syntax with -m flag")
                        self.use_new_syntax = False
                except Exception as e:
                    self.logger.warning(f"Could not determine Kokoro syntax version: {str(e)}")
                    self.use_new_syntax = False
        except Exception as e:
            self.logger.warning(f"Error checking for kokoro command: {str(e)}")
            self.use_new_syntax = False
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess the text to improve TTS quality.
        
        Args:
            text: Input text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Strip excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Add periods at the end of lines if missing
        text = re.sub(r'([a-zA-Z0-9])(?=\n)', r'\1.', text)
        
        # Replace common abbreviations (optional, can be expanded)
        text = re.sub(r'\be\.g\.\s', 'for example ', text)
        text = re.sub(r'\bi\.e\.\s', 'that is ', text)
        
        # Remove markdown or other special formatting if present
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        
        return text
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into manageable chunks for TTS processing.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        # Start by splitting on paragraph boundaries
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If paragraph is longer than max chunk size, split by sentences
            if len(paragraph) > self.max_chunk_length:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= self.max_chunk_length:
                        current_chunk += " " + sentence if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
            else:
                # If adding this paragraph exceeds max length, start a new chunk
                if len(current_chunk) + len(paragraph) + 1 <= self.max_chunk_length:
                    current_chunk += " " + paragraph if current_chunk else paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = paragraph
        
        # Don't forget to add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
            
        self.logger.info(f"Split text into {len(chunks)} chunks for processing")
        return chunks
    
    def generate_audio(self, text: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate audio from text and save to file.
        
        Args:
            text: Input text to convert to speech
            output_path: Path to save the audio file
            metadata: Optional metadata to include in output
            
        Returns:
            Dictionary with information about the generated audio
        """
        start_time = time.time()
        self.logger.info(f"Starting TTS generation for text ({len(text)} characters)")
        
        # Ensure the output directory exists
        print(f"Output path: {output_path}")
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Preprocess the text
        preprocessed_text = self.preprocess_text(text)
        
        # Split into manageable chunks
        chunks = self.chunk_text(preprocessed_text)
        self.logger.info(f"Processing {len(chunks)} text chunks")
        
        # Create a temporary directory for chunk audio files
        with tempfile.TemporaryDirectory() as temp_dir:
            chunk_files = []
            
            # Process each chunk and generate audio
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                self.logger.info(f"Chunk {i+1} first 200 chars: {chunk[:200]}")
                self.logger.info(f"Chunk {i+1} length: {len(chunk)} chars")
                # store chunks
                chunk_file = os.path.join(temp_dir, f"chunk_{i+1}.wav")
                
                try:
                    # Create a temporary text file for the chunk
                    chunk_text_file = os.path.join(temp_dir, f"chunk_{i+1}.txt")
                    with open(chunk_text_file, 'w', encoding='utf-8') as f:
                        f.write(chunk)
                    
                    # Build the kokoro command based on detected syntax
                    if hasattr(self, 'use_new_syntax') and self.use_new_syntax:
                        # New syntax with --voice and --speed
                        cmd = ['kokoro',
                              '--language', self.language_code,
                              '--input', chunk_text_file,
                              '--output', chunk_file]
                        
                        # Add voice if specified
                        if self.voice:
                            cmd.extend(['--voice', self.voice])
                        
                        # Add speed if not default
                        if self.speed != 1.0:
                            cmd.extend(['--speed', str(self.speed)])
                    else:
                        # Legacy syntax with -l, -i, -o, -m, -s flags
                        cmd = ['kokoro', 
                              '-l', self.language_code, 
                              '-i', chunk_text_file,
                              '-o', chunk_file]
                        
                        # Add voice if specified
                        if self.voice:
                            cmd.extend(['-m', self.voice])
                        
                        # Add speed if not default
                        if self.speed != 1.0:
                            cmd.extend(['-s', str(self.speed)])
                    
                    # Run the command
                    self.logger.debug(f"Running command: {' '.join(cmd)}")
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if process.returncode != 0:
                        self.logger.error(f"Error generating audio for chunk {i+1}: {process.stderr}")
                        # If command fails, try alternative syntax
                        if hasattr(self, 'use_new_syntax'):
                            self.use_new_syntax = not self.use_new_syntax
                            self.logger.info(f"Retrying with {'new' if self.use_new_syntax else 'legacy'} syntax")
                            
                            # Rebuild command with alternative syntax
                            if self.use_new_syntax:
                                cmd = ['kokoro',
                                      '--language', self.language_code,
                                      '--input', chunk_text_file,
                                      '--output', chunk_file]
                                if self.voice:
                                    cmd.extend(['--voice', self.voice])
                                if self.speed != 1.0:
                                    cmd.extend(['--speed', str(self.speed)])
                            else:
                                cmd = ['kokoro', 
                                      '-l', self.language_code, 
                                      '-i', chunk_text_file,
                                      '-o', chunk_file]
                                if self.voice:
                                    cmd.extend(['-m', self.voice])
                                if self.speed != 1.0:
                                    cmd.extend(['-s', str(self.speed)])
                            
                            # Try alternative syntax
                            self.logger.debug(f"Retrying with command: {' '.join(cmd)}")
                            process = subprocess.run(cmd, capture_output=True, text=True)
                            
                            if process.returncode != 0:
                                self.logger.error(f"Error with alternative syntax too: {process.stderr}")
                                continue
                        else:
                            continue
                    
                    if os.path.exists(chunk_file):
                        chunk_files.append(chunk_file)
                    else:
                        self.logger.warning(f"Output file {chunk_file} not created for chunk {i+1}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing chunk {i+1}: {str(e)}")
                    # Continue with other chunks if one fails
            
            # Combine all audio chunks
            if chunk_files:
                audio_segments = []
                
                for i, chunk_file in enumerate(chunk_files):
                    # Read the audio data
                    audio_data, sample_rate = sf.read(chunk_file)
                    audio_segments.append(audio_data)
                    
                    # Add a small pause between chunks
                    if i < len(chunk_files) - 1:
                        pause = np.zeros(int(self.pause_between_chunks * sample_rate))
                        audio_segments.append(pause)
                
                # Combine all audio segments
                combined_audio = np.concatenate(audio_segments)
                
                # Save the audio to file
                sf.write(output_path, combined_audio, self.sample_rate)
                
                processing_time = time.time() - start_time
                audio_duration = len(combined_audio) / self.sample_rate
                
                result = {
                    "output_path": output_path,
                    "text_length": len(text),
                    "audio_duration_seconds": audio_duration,
                    "processing_time_seconds": processing_time,
                    "sample_rate": self.sample_rate,
                    "chunks_processed": len(chunks),
                    "voice_used": self.voice,
                    "speed_factor": self.speed
                }
                
                # Save metadata if provided
                if metadata:
                    metadata_path = output_path.replace(f".{self.output_format}", "_metadata.json")
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        combined_metadata = {**metadata, **result}
                        json.dump(combined_metadata, f, indent=2)
                    result["metadata_path"] = metadata_path
                
                self.logger.info(f"TTS generation completed in {processing_time:.2f} seconds")
                self.logger.info(f"Generated audio duration: {audio_duration:.2f} seconds")
                self.logger.info(f"Audio saved to: {output_path}")
                
                return result
            else:
                raise ValueError("No audio was generated from the provided text")

def generate_audio_from_transcript(transcript_dir: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate audio from a processed transcript.
    
    Args:
        transcript_dir: Directory containing the transcript
        config: Configuration dictionary
        
    Returns:
        Dictionary with information about the generated audio
    """
    start_time = time.time()
    
    # Ensure audio directory exists
    audio_dir = os.path.join(transcript_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    #print the config
    print(f"config: {config}")
    # Path to processed transcript
    processed_dir = os.path.join(transcript_dir, "processed")
    if not os.path.exists(processed_dir):
        raise FileNotFoundError(f"Processed directory not found: {processed_dir}")
    
    # Look for narrative transcript file (the final concatenated file)
    transcript_path = os.path.join(processed_dir, "narrative_transcript.txt")
    
    # Check if the main transcript file exists
    if not os.path.exists(transcript_path):
        logger.warning(f"Standard narrative transcript not found at {transcript_path}")
        logger.warning("Looking for alternative processed transcript files...")
        
        # Look for alternative files
        alternate_files = [
            "narrative_transcript.json",
            "processed_transcript.txt",
            "processed_transcript.json"
        ]
        for alt_file in alternate_files:
            alt_path = os.path.join(processed_dir, alt_file)
            if os.path.exists(alt_path):
                transcript_path = alt_path
                logger.info(f"Using alternative transcript file: {transcript_path}")
                break
    
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"No processed transcript found in {processed_dir}")
    
    # Check if this is the final concatenated file
    metadata_path = os.path.join(processed_dir, "narrative_transcript_metadata.json")
    is_multi_chunk = False
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                if metadata.get("num_chunks", 1) > 1:
                    is_multi_chunk = True
                    logger.info(f"TTS processing a concatenated transcript from {metadata.get('num_chunks')} chunks")
        except Exception as e:
            logger.warning(f"Could not read metadata file: {e}")
    
    # Read the transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    # Log that we're working with the final transcript
    logger.info(f"Generating audio from {'multi-chunk concatenated' if is_multi_chunk else 'single'} transcript ({len(transcript_text)} characters)")
    
    # Prepare output path
    output_filename = f"audio_{Path(transcript_path).stem}.wav"
    output_path = os.path.join(audio_dir, output_filename)
    
    # Generate metadata
    metadata = {
        "source_transcript": transcript_path,
        "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tts_engine": "Kokoro TTS",
        "transcript_dir": transcript_dir,
        "is_multi_chunk_transcript": is_multi_chunk
    }
    
    # Load metadata from the transcript if available
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                transcript_metadata = json.load(f)
            metadata["transcript_metadata"] = transcript_metadata
        except Exception as e:
            logger.warning(f"Error loading transcript metadata: {str(e)}")
    
    # Set default TTS configuration if none provided
    if not config:
        config = {}
    
    # Set bm_george voice at 0.9 speed if not specified
    if "tts" not in config:
        config["tts"] = {}
    
    tts_config = config.get("tts", {})
    if "voice_pack" not in tts_config:
        tts_config["voice_pack"] = "bm_lewis"
    if "speed" not in tts_config:
        tts_config["speed"] = 0.8
    if "language" not in tts_config:
        tts_config["language"] = "b"  # British English
    
    # Initialize TTS generator and generate audio
    logger.info("TTS generation starting ONLY after all transcript chunks have been processed and concatenated")
    logger.info(f"Using voice: {tts_config.get('voice_pack')} at speed: {tts_config.get('speed')}x")
    tts_generator = TTSGenerator(tts_config)
    result = tts_generator.generate_audio(transcript_text, output_path, metadata)
    
    return result

# If run directly as a script
if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("tts_generator.log")
        ]
    )
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate audio from processed transcript")
    parser.add_argument("--transcript-dir", required=True, help="Directory containing the transcript")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--voice", default="bm_lewis", help="Voice to use (default: bm_lewis)")
    parser.add_argument("--speed", type=float, default=0.8, help="Speech speed (default: 0.8)")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    else:
        # Create minimal config with voice and speed
        config = {
            "tts": {
                "voice_pack": args.voice,
                "speed": args.speed,
                "language": "b"  # British English for bm_george
            }
        }
    
    # Generate audio
    try:
        result = generate_audio_from_transcript(args.transcript_dir, config)
        print(f"\nAudio generation completed:")
        print(f"  Output: {result['output_path']}")
        print(f"  Voice: {result.get('voice_used', 'bm_lewis')}")
        print(f"  Speed: {result.get('speed_factor', 0.8)}x")
        print(f"  Duration: {result['audio_duration_seconds']:.2f} seconds")
        print(f"  Processing time: {result['processing_time_seconds']:.2f} seconds")
    except Exception as e:
        logger.exception(f"Error generating audio: {str(e)}")
        sys.exit(1)