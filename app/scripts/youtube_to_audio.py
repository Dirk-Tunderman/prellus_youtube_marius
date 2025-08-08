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
from src.transcript_pipeline.processor.simple_processor import process_simple_transcript
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


def process_transcript_simple(video_dir: str, config: dict) -> dict:
    """
    Wrapper function to process transcript using simple processor.

    This maintains compatibility with the old process_transcript interface
    while using the new simplified processor.

    Args:
        video_dir: Path to the video directory
        config: Configuration dictionary

    Returns:
        Dictionary with processed_file and metadata for compatibility
    """
    import os
    import json

    # Load the raw transcript
    transcript_path = os.path.join(video_dir, "raw", "transcript.json")
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript not found at {transcript_path}")

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)

    # Extract transcript text
    if isinstance(transcript_data, list):
        transcript_text = " ".join([entry.get("text", "") for entry in transcript_data])
    else:
        transcript_text = transcript_data.get("text", "")

    # Create processed directory
    processed_dir = os.path.join(video_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # Process using simple processor
    processed_text = process_simple_transcript(
        transcript_text=transcript_text,
        config=config,
        output_dir=processed_dir,
        mock_mode=False
    )

    # Save processed transcript
    processed_file = os.path.join(processed_dir, "narrative_transcript.txt")
    with open(processed_file, "w", encoding="utf-8") as f:
        f.write(processed_text)

    # Create metadata for compatibility
    metadata = {
        "original_length": len(transcript_text),
        "processed_length": len(processed_text),
        "length_ratio": len(processed_text) / len(transcript_text) if len(transcript_text) > 0 else 0,
        "chunks_info": [],  # Simple processor doesn't use chunks
        "processing_method": "simple"
    }

    return {
        "processed_file": processed_file,
        "metadata": metadata
    }


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
        # Track processing time
        start_time = time.time()

        # === COMPLETE INPUT DATA LOGGING ===
        logger.info("=" * 80)
        logger.info("📋 COMPLETE INPUT DATA FOR PROCESSING")
        logger.info("=" * 80)
        logger.info(f"🔗 YouTube URL: {youtube_url}")
        logger.info(f"⚙️ Voice Pack: {voice_pack}")
        logger.info(f"⏭️ Skip TTS: {skip_tts}")
        
        if json_data:
            logger.info("📊 JSON Data Received:")
            logger.info(f"   ⏱️ Duration: {json_data.get('duration')} minutes")
            logger.info(f"   🗣️ Voice: {json_data.get('voice', 'not specified')}")
            logger.info(f"   🏃 Speed: {json_data.get('speed', 'not specified')}x")
            logger.info(f"   📝 Title: {json_data.get('title', 'not specified')}")
            
            # Log all other json_data fields
            other_fields = {k: v for k, v in json_data.items() if k not in ['duration', 'voice', 'speed', 'title', 'promptData']}
            if other_fields:
                logger.info("   📋 Other fields:")
                for key, value in other_fields.items():
                    logger.info(f"      - {key}: {value}")
        else:
            logger.info("📊 No JSON data provided")
        
        logger.info("=" * 80)

        # Check if we have structured prompt data
        if json_data and "promptData" in json_data:
            prompt_data = json_data.get("promptData", {})
            logger.info("📝 Structured Prompt Data:")
            for key, value in prompt_data.items():
                if value:
                    short_value = value[:100] + "..." if len(value) > 100 else value
                    logger.info(f"   - {key}: {short_value}")

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

        if json_data and json_data.get("duration"):
            duration_minutes = json_data.get("duration")
            speed_factor = json_data.get("speed", 1.0)  # Default to 1.0x if not specified
            
            # === IMPROVED LENGTH CALCULATION ===
            logger.info("🧮 LENGTH CALCULATION:")
            logger.info(f"   ⏱️ Requested duration: {duration_minutes} minutes")
            logger.info(f"   🏃 Speed factor: {speed_factor}x")
            
            # TTS reading speed (slower than human reading)
            base_tts_reading_speed = 180  # words per minute for TTS
            
            # Adjust for speed factor: slower speed = fewer characters needed for same time
            # At 0.8x speed, content plays 25% slower, so we need 25% fewer characters
            effective_reading_speed = base_tts_reading_speed / speed_factor
            
            # More accurate character count for TTS content
            avg_chars_per_word = 4.7  # Based on English language averages
            
            target_length = int(duration_minutes * effective_reading_speed * avg_chars_per_word)
            
            logger.info(f"   📚 Base TTS reading speed: {base_tts_reading_speed} WPM")
            logger.info(f"   ⚡ Effective reading speed: {effective_reading_speed:.1f} WPM")
            logger.info(f"   🔤 Average chars per word: {avg_chars_per_word}")
            logger.info(f"   🎯 Target length: {target_length} characters")
            
            # Show comparison with old calculation for reference
            old_calculation = int(duration_minutes * 239 * 5)
            logger.info(f"   📊 Old calculation would be: {old_calculation} characters")
            logger.info(f"   📉 New calculation is {target_length/old_calculation:.2f}x the old value")
        else:
            # Fallback for when no duration is specified
            target_length = original_length
            logger.info("⚠️ No duration specified, using original length")

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

        # Simple processor handles all scaling factors automatically
        logger.info(f"✨ Simple processor will handle scaling factor: {scaling_factor:.2f}x")
        if scaling_factor > 2.0:
            logger.info("   📈 High expansion - will use multiple generation rounds")
        elif scaling_factor < 0.5:
            logger.info("   📉 High compression - will generate concise content")
        else:
            logger.info("   ⚖️ Moderate scaling - will adjust content appropriately")

        # === PROCESSING PATH DECISION LOGGING ===
        logger.info("="*60)
        logger.info("🔍 PROCESSING PATH DECISION ANALYSIS")
        logger.info("="*60)
        
        # Check if custom instructions are present
        ai_config = processing_config.get("ai", {})
        has_custom_instructions = any([
            ai_config.get("prompt_role"),
            ai_config.get("prompt_script_structure"), 
            ai_config.get("prompt_tone_style"),
            ai_config.get("prompt_retention_flow"),
            ai_config.get("prompt_additional_instructions")
        ])
        
        logger.info(f"📝 Custom instructions present: {has_custom_instructions}")
        if has_custom_instructions:
            logger.info("🎯 RECREATION MODE should be activated")
            logger.info("   Expected behavior: Create entirely new content, ignore original subject")
            if ai_config.get("prompt_role"):
                logger.info(f"   Role: {ai_config.get('prompt_role')[:100]}...")
            if ai_config.get("prompt_script_structure"):
                logger.info(f"   Structure provided: {len(ai_config.get('prompt_script_structure', ''))} chars")
        else:
            logger.info("🔧 IMPROVEMENT MODE - no custom instructions")
        
        # New simplified processing approach
        expected_length = processing_config.get("ai", {}).get("length_in_chars", original_length)

        logger.info(f"🚀 NEW SIMPLIFIED PROCESSING APPROACH")
        logger.info(f"   Original length: {original_length:,} chars")
        logger.info(f"   Expected output: {expected_length:,} chars")
        logger.info(f"   Scaling factor: {expected_length / original_length:.2f}x")
        logger.info(f"   Method: Single unified processor with max token output")
        logger.info(f"   Features: Master document + continuation generation")

        logger.info("="*60)

        # Use the modified config for processing with simple processor
        processor_result = process_transcript_simple(video_dir, processing_config)

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

        # === PROCESSING RESULTS SUMMARY ===
        logger.info("🎉 PROCESSING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"📁 Output file: {processed_file}")
        logger.info(f"📊 RESULTS SUMMARY:")
        logger.info(f"   📜 Original transcript: {metadata.get('original_length', 0):,} characters")
        logger.info(f"   ✨ Processed transcript: {metadata.get('processed_length', 0):,} characters")

        # Calculate and log the length ratio
        original_length = metadata.get("original_length", 0)
        processed_length = metadata.get("processed_length", 0)
        length_ratio = processed_length / original_length if original_length > 0 else 0
        metadata["length_ratio"] = length_ratio

        # Enhanced target comparison
        if target_length:
            target_ratio = processed_length / target_length if target_length > 0 else 0
            metadata["target_ratio"] = target_ratio
            
            logger.info(f"   🎯 Target length: {target_length:,} characters")
            logger.info(f"   📏 Ratio to target: {target_ratio:.2f}x")
            
            # More detailed accuracy assessment
            if 0.8 <= target_ratio <= 1.2:
                logger.info("   ✅ TARGET ACHIEVED - Within 20% of requested length!")
            elif 0.5 <= target_ratio <= 1.5:
                logger.info("   ⚠️ CLOSE TO TARGET - Within 50% of requested length")
            elif target_ratio < 0.5:
                logger.warning(f"   ❌ TOO SHORT - Output is {target_ratio:.2f}x target length")
            else:
                logger.warning(f"   ❌ TOO LONG - Output is {target_ratio:.2f}x target length")
        
        logger.info(f"   📈 Ratio to original: {length_ratio:.2f}x")
        logger.info("=" * 80)

        # Verify that all chunks have been processed before starting TTS
        if "num_chunks" in metadata and metadata["num_chunks"] > 1:
            logger.info(
                f"All {metadata['num_chunks']} chunks have been processed and concatenated."
            )

        # 🚀 EARLY RETURN: Complete transcript processing and return before audio generation
        logger.info("🎉 TRANSCRIPT PROCESSING COMPLETE - RETURNING EARLY")
        logger.info("   Audio generation will be skipped for this version")
        logger.info("   Transcript is ready for use!")

        return {
            "status": "success",
            "message": "Transcript processing completed successfully",
            "transcript_file": processed_file,
            "metadata": metadata,
            "video_dir": video_dir,
            "processing_time": time.time() - start_time,
            "early_return": True,
            "audio_skipped": True
        }

        # Step 3: Generate audio ONLY after all chunks have been processed
        # NOTE: This code is now unreachable due to early return above
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

        # Log summary
        logger.info("\n" + "=" * 60)
        logger.info("YOUTUBE TO AUDIO PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        logger.info(f"\nYouTube URL: {args.youtube_url}")
        logger.info(f"Project directory: {result['video_dir']}")

        logger.info("\nOutput files:")
        logger.info(f"- Raw transcript: {result['transcript_file']}")
        logger.info(f"- Processed transcript: {result['processed_file']}")

        if not args.skip_tts:
            logger.info(f"- Audio file: {result['audio_file']}")
            logger.info(f"- Audio duration: {result['audio_duration']:.2f} seconds")

        logger.info("\nProcessing statistics:")
        logger.info(f"- Chunks processed: {result['chunks_processed']}")
        logger.info(f"- Original length: {result['original_length']} characters")
        logger.info(f"- Processed length: {result['processed_length']} characters")
        logger.info(f"- Length ratio: {result['length_ratio']:.2f}")
        logger.info(f"- Total processing time: {result['processing_time']:.2f} seconds")

        if "target_length" in result:
            logger.info(f"- Target length: {result['target_length']} characters")
            logger.info(f"- Ratio to target: {result['target_ratio']:.2f}")

        return 0

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
