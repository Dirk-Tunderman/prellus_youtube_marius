#!/usr/bin/env python3
"""
YouTube to Audio Pipeline Script - Enhanced for structured prompts

This script provides a seamless end-to-end pipeline from a YouTube URL to
audio generation. It handles:
1. Fetching the YouTube transcript
2. Processing the transcript with AI to enhance readability
3. Generating audio from the processed transcript using Kokoro TTS

Usage:
    python scripts/youtube_to_audio.py <youtube_url> [options]

Example:
    python scripts/youtube_to_audio.py https://www.youtube.com/watch?v=GBbUmiH23-0 --voice-pack af_bella
"""

# Load environment variables from .env file
import os
from dotenv import load_dotenv
import time

# Load .env file from the project root
load_dotenv()

import sys
import logging
import argparse
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Also try loading .env from project root if not already loaded
env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

# If GEMINI_API_KEY exists but GOOGLE_API_KEY doesn't, use GEMINI_API_KEY
if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ.get("GEMINI_API_KEY")

from src.transcript_pipeline.fetcher.fetch_and_store import fetch_transcript
from src.transcript_pipeline.processor.ai_processor import process_transcript
from src.transcript_pipeline.tts.tts_generator import generate_audio_from_transcript

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


def load_config(config_path="app/config/config.yaml"):
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.warning(f"Error loading configuration from {config_path}: {e}")
        return {}


def youtube_to_audio(
    youtube_url: str,
    config: Dict[str, Any],
    voice_pack: Optional[str] = None,
    skip_tts: bool = False,
    json_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a YouTube URL to generate audio from its transcript.

    This function orchestrates the complete pipeline:
    1. Fetch transcript from YouTube
    2. Process the transcript with AI (with chunking for large transcripts)
    3. Generate audio from the processed transcript using Kokoro TTS

    Args:
        youtube_url: YouTube video URL
        config: Configuration dictionary
        voice_pack: Optional voice pack to override the default
        skip_tts: Whether to skip the TTS generation step
        json_data: Optional JSON data containing additional information (prompt, duration, etc.)

    Returns:
        Dictionary with information about the generated output
    """
    try:
        # Log json_data if provided
        if json_data:
            logger.info(
                f"Received additional data: duration={json_data.get('duration')}"
            )

            # Check if we have structured prompt data
            if "promptData" in json_data:
                prompt_data = json_data.get("promptData", {})
                logger.info("Received structured prompt data:")
                for key, value in prompt_data.items():
                    if value:
                        short_value = value[:50] + "..." if len(value) > 50 else value
                        logger.info(f"  - {key}: {short_value}")

        # Step 1: Fetch transcript
        logger.info(f"Step 1: Fetching transcript for {youtube_url}")
        transcript_result = fetch_transcript(
            youtube_url, config.get("transcript", {}), json_data
        )
        video_dir = transcript_result["video_dir"]
        logger.info(f"Transcript fetched and stored in {video_dir}")

        # Check transcript size for appropriate processing
        transcript_path = transcript_result.get("plain_text_path")
        if not transcript_path or not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript file not found at {transcript_path}")

        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()
            original_length = len(transcript_text)

        # Step 2: Process transcript with AI
        logger.info(f"Step 2: Processing transcript with AI")

        # Ensure large_transcript_threshold from config is used
        if "large_transcript_threshold" not in config:
            config["large_transcript_threshold"] = 20000

        # Calculate target length based on requested duration (if provided)
        target_length = None
        scaling_factor = 1.0

        # Convert duration minutes to character count
        reading_speed = 250  # words per minute
        avg_chars_per_word = 5  # characters per word
        target_length = int(
            json_data.get("duration") * reading_speed * avg_chars_per_word
        )

        # Calculate scaling factor
        scaling_factor = target_length / original_length if original_length > 0 else 1.0

        # Create a copy of the config
        processing_config = config.copy()
        if "ai" not in processing_config:
            processing_config["ai"] = {}

        # Remove the custom_prompt since we're using structured prompt fields
        if "custom_prompt" in processing_config["ai"]:
            del processing_config["ai"]["custom_prompt"]

        # Add structured prompt data if available
        if json_data.get("promptData"):
            prompt_data = json_data.get("promptData", {})

            # Store each component separately in the config
            processing_config["ai"]["prompt_role"] = prompt_data.get("yourRole", "")
            processing_config["ai"]["prompt_script_structure"] = prompt_data.get(
                "scriptStructure", ""
            )
            processing_config["ai"]["prompt_tone_style"] = prompt_data.get(
                "toneAndStyle", ""
            )
            processing_config["ai"]["prompt_retention_flow"] = prompt_data.get(
                "retentionAndFlow", ""
            )
            processing_config["ai"]["prompt_additional_instructions"] = prompt_data.get(
                "additionalInstructions", ""
            )

            # Also keep the full structure for reference
            processing_config["ai"]["prompt_structure"] = prompt_data

            # Save prompt structure to a file for reference
            prompt_structure_path = os.path.join(video_dir, "prompt_structure.json")
            with open(prompt_structure_path, "w", encoding="utf-8") as f:
                json.dump(prompt_data, f, indent=2)
            logger.info(f"Saved structured prompt data to {prompt_structure_path}")

            # Log the prompt components
            logger.info("Using structured prompt with components:")
            for key, value in prompt_data.items():
                if value:
                    short_value = value[:50] + "..." if len(value) > 50 else value
                    logger.info(f"  - {key}: {short_value}")

        # Add length parameters
        processing_config["ai"]["length"] = json_data.get("duration")
        processing_config["ai"]["length_in_chars"] = target_length

        # Log scaling information
        logger.info(f"Target duration: {json_data.get('duration')} minutes")
        logger.info(f"Original transcript length: {original_length} characters")
        logger.info(f"Target transcript length: {target_length} characters")
        logger.info(f"Scaling factor: {scaling_factor:.2f}x")

        # Force chunked processing for significant scaling factors, even for small transcripts
        significant_scaling = scaling_factor > 1.5 or scaling_factor < 0.7

        if significant_scaling:
            # Force chunked processing by temporarily modifying large_transcript_threshold
            original_threshold = processing_config.get(
                "large_transcript_threshold", 20000
            )
            processing_config["large_transcript_threshold"] = min(
                original_length - 1, original_threshold
            )
            logger.info(
                f"Forcing chunked processing due to significant scaling factor ({scaling_factor:.2f}x)"
            )

        # Use the modified config for processing
        processor_result = process_transcript(video_dir, processing_config)

        processed_file = processor_result.get("processed_file")
        metadata = processor_result.get("metadata", {})

        # Print detailed information about chunks
        chunks_info = metadata.get("chunks_info", [])
        if chunks_info:
            logger.info("=== Chunk Processing Details ===")
            logger.info(f"Total chunks processed: {len(chunks_info)}")
            for i, chunk_info in enumerate(chunks_info):
                original_len = chunk_info.get("original_length", 0)
                processed_len = chunk_info.get("processed_length", 0)
                target_len = chunk_info.get("target_length", processed_len)
                ratio = processed_len / original_len if original_len > 0 else 0
                logger.info(
                    f"Chunk {i+1}: Original: {original_len} chars, Target: {target_len} chars, Actual: {processed_len} chars, Ratio: {ratio:.2f}"
                )
        else:
            logger.info("=== Processing Details ===")
            logger.info("Processed as a single chunk (no chunking applied)")

        logger.info(
            f"Transcript processing complete. Concatenated result saved to {processed_file}"
        )
        logger.info(
            f"Original transcript: {metadata.get('original_length', 0)} characters"
        )
        logger.info(
            f"Processed transcript: {metadata.get('processed_length', 0)} characters"
        )

        # Calculate and log the length ratio
        original_length = metadata.get("original_length", 0)
        processed_length = metadata.get("processed_length", 0)
        length_ratio = processed_length / original_length if original_length > 0 else 0
        metadata["length_ratio"] = length_ratio

        # Also calculate ratio to target if target was specified
        if target_length:
            target_ratio = processed_length / target_length if target_length > 0 else 0
            metadata["target_ratio"] = target_ratio
            logger.info(f"Target length: {target_length} characters")
            logger.info(f"Ratio to target: {target_ratio:.2f}")

            # Warning if output is significantly different from target
            if target_ratio < 0.5:
                logger.warning(
                    f"Output is much shorter than requested ({target_ratio:.2f}x target length)"
                )
            elif target_ratio > 1.5:
                logger.warning(
                    f"Output is much longer than requested ({target_ratio:.2f}x target length)"
                )

        logger.info(f"Overall ratio to original: {length_ratio:.2f}")

        # Verify that all chunks have been processed before starting TTS
        if "num_chunks" in metadata and metadata["num_chunks"] > 1:
            logger.info(
                f"All {metadata['num_chunks']} chunks have been processed and concatenated."
            )

        # Step 3: Generate audio ONLY after all chunks have been processed
        if not skip_tts:
            logger.info(f"Step 3: Generating audio from fully processed transcript")

            # Override voice pack if specified
            tts_config = config.get("tts", {}).copy()
            if voice_pack:
                tts_config["voice_pack"] = voice_pack
                logger.info(f"Using custom voice pack: {voice_pack}")

            audio_result = generate_audio_from_transcript(video_dir, tts_config)
            audio_file = audio_result["output_path"]
            logger.info(f"Audio generated and saved to {audio_file}")

            # Check if audio duration matches requested duration (if specified)
            if json_data and json_data.get("duration"):
                requested_duration_seconds = (
                    json_data.get("duration") * 60
                )  # Convert minutes to seconds
                actual_duration_seconds = audio_result["audio_duration_seconds"]
                duration_ratio = (
                    actual_duration_seconds / requested_duration_seconds
                    if requested_duration_seconds > 0
                    else 0
                )
                logger.info(
                    f"Requested duration: {requested_duration_seconds:.2f} seconds"
                )
                logger.info(
                    f"Actual audio duration: {actual_duration_seconds:.2f} seconds"
                )
                logger.info(f"Duration ratio: {duration_ratio:.2f}")

                # Warning if audio duration is far off from requested duration
                if duration_ratio < 0.7 or duration_ratio > 1.3:
                    logger.warning(
                        f"Audio duration ({actual_duration_seconds:.2f}s) is significantly different from requested duration ({requested_duration_seconds:.2f}s)"
                    )
        else:
            logger.info("Skipping audio generation (--skip-tts flag was used)")
            audio_result = {
                "output_path": None,
                "audio_duration_seconds": 0,
                "processing_time_seconds": 0,
            }

        # Return summary of results
        result = {
            "video_dir": video_dir,
            "transcript_file": transcript_result["plain_text_path"],
            "processed_file": processed_file,
            "audio_file": audio_result["output_path"],
            "audio_duration": audio_result["audio_duration_seconds"],
            "processing_time": audio_result["processing_time_seconds"],
            "chunks_processed": metadata.get("num_chunks", 1),
            "original_length": metadata.get("original_length", 0),
            "processed_length": metadata.get("processed_length", 0),
            "length_ratio": length_ratio,
        }

        # Add target-related metrics if target was specified
        if target_length:
            result["target_length"] = target_length
            result["target_ratio"] = (
                processed_length / target_length if target_length > 0 else 0
            )
            result["requested_duration_minutes"] = json_data.get("duration")
            if not skip_tts:
                result["duration_ratio"] = (
                    audio_result["audio_duration_seconds"]
                    / (json_data.get("duration") * 60)
                    if json_data.get("duration") > 0
                    else 0
                )

        return result

    except Exception as e:
        logger.exception(f"Error in YouTube to audio pipeline: {e}")
        raise


def main():
    """Main function to parse arguments and run the pipeline."""
    parser = argparse.ArgumentParser(description="YouTube to Audio Pipeline")
    parser.add_argument("youtube_url", help="YouTube video URL to process")
    parser.add_argument(
        "--config",
        default="app/config/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--voice-pack",
        help="Voice pack to use (e.g., af_bella for American Female Bella)",
    )
    parser.add_argument(
        "--model",
        help="AI model to use for transcript processing (e.g., gemini-2.0-flash-lite)",
    )
    parser.add_argument(
        "--skip-tts",
        action="store_true",
        help="Skip TTS generation (process transcript only)",
    )
    parser.add_argument(
        "--prompt-id", help="ID of a saved prompt to use for processing"
    )
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args.config)

        # Override model if specified
        if args.model and "ai" in config:
            config["ai"]["model"] = args.model
            logger.info(f"Using custom AI model: {args.model}")

        # Load prompt if prompt ID is specified
        json_data = {}
        if args.prompt_id:
            # Path to prompts directory
            prompts_dir = os.path.join(project_root, "app/data/stored_prompts")
            prompt_file = os.path.join(prompts_dir, f"{args.prompt_id}.json")

            if os.path.exists(prompt_file):
                try:
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        prompt_data = json.load(f)

                    logger.info(
                        f"Loaded prompt: {prompt_data['meta_data']['prompt_name']}"
                    )

                    # Convert from storage format to processing format
                    prompt_structure = {
                        "yourRole": prompt_data["prompt"].get("Role", ""),
                        "scriptStructure": prompt_data["prompt"].get(
                            "Script_Structure", ""
                        ),
                        "toneAndStyle": prompt_data["prompt"].get("Tone_Style", ""),
                        "retentionAndFlow": prompt_data["prompt"].get(
                            "Retention_Flow", ""
                        ),
                        "additionalInstructions": prompt_data["prompt"].get(
                            "Additional_instructions", ""
                        ),
                    }

                    # Add prompt data to json_data
                    json_data["promptData"] = prompt_structure

                except Exception as e:
                    logger.error(f"Error loading prompt file {prompt_file}: {e}")
            else:
                logger.warning(f"Prompt file not found: {prompt_file}")

        # Run the pipeline
        logger.info(f"Starting YouTube to Audio pipeline for {args.youtube_url}")
        result = youtube_to_audio(
            args.youtube_url, config, args.voice_pack, args.skip_tts, json_data
        )

        # Print summary
        print("\n" + "=" * 60)
        print("YOUTUBE TO AUDIO PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print(f"\nYouTube URL: {args.youtube_url}")
        print(f"Project directory: {result['video_dir']}")

        print("\nOutput files:")
        print(f"- Raw transcript: {result['transcript_file']}")
        print(f"- Processed transcript: {result['processed_file']}")

        if not args.skip_tts:
            print(f"- Audio file: {result['audio_file']}")
            print(f"- Audio duration: {result['audio_duration']:.2f} seconds")

        print("\nProcessing statistics:")
        print(f"- Chunks processed: {result['chunks_processed']}")
        print(f"- Original length: {result['original_length']} characters")
        print(f"- Processed length: {result['processed_length']} characters")
        print(f"- Length ratio: {result['length_ratio']:.2f}")
        print(f"- Total processing time: {result['processing_time']:.2f} seconds")

        if "target_length" in result:
            print(f"- Target length: {result['target_length']} characters")
            print(f"- Ratio to target: {result['target_ratio']:.2f}")

        return 0

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\nError: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
