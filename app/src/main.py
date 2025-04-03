#!/usr/bin/env python3
"""
Transcript and Video Automation System - Main Entry Point

This module serves as the primary entry point for the Transcript and Video Automation
System, orchestrating the two completely independent pipelines:
1. Transcript Processing Pipeline: Extracts and processes YouTube video transcripts
2. Video Compilation Pipeline: Creates compiled videos from stock footage
3. Final Assembly: Combines audio from transcript with compiled video

The system requires minimal user intervention, needing only a YouTube URL as input for
the transcript pipeline, and produces a complete package of transcript, audio, and
complementary video footage.

Usage:
    python -m src.main [options] <youtube_url>

Example:
    python -m src.main https://www.youtube.com/watch?v=dQw4w9WgXcQ
"""

import os
import sys
import logging
import argparse
import yaml
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("transcript_video_automation.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def load_config(config_path="config.yaml"):
    """
    Load configuration from YAML file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        raise


def extract_video_id(youtube_url):
    """
    Extract video ID from YouTube URL.
    
    Args:
        youtube_url (str): YouTube video URL
        
    Returns:
        str: YouTube video ID
    """
    import re
    youtube_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
    if youtube_id_match:
        return youtube_id_match.group(1)
    return "unknown_id"


def process_video(youtube_url, config, output_dir=None, generate_audio=False):
    """
    Process a YouTube video through both pipelines and create final output.
    
    This function orchestrates the two independent pipelines and the final assembly:
    1. Transcript Processing Pipeline - Extracts transcript, processes it with AI, generates audio
    2. Video Compilation Pipeline - Scrapes and compiles stock footage
    3. Final Assembly - Combines the audio and video
    
    Args:
        youtube_url (str): YouTube video URL
        config (dict): System configuration
        output_dir (str, optional): Custom output directory
        generate_audio (bool): Whether to generate audio from the transcript
        
    Returns:
        str: Path to project directory
    """
    # Extract video ID
    video_id = extract_video_id(youtube_url)
    
    # Create project directory
    project_id = f"yt_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    project_dir = output_dir or os.path.join(config["general"]["output_directory"], project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    logger.info(f"Processing video: {youtube_url}")
    logger.info(f"Project directory: {project_dir}")
    
    # TODO: Implement Transcript Processing Pipeline
    
    # Generate audio from transcript if requested
    if generate_audio:
        try:
            from transcript_pipeline.tts.tts_generator import generate_audio_from_transcript
            
            logger.info("Generating audio from transcript...")
            audio_result = generate_audio_from_transcript(project_dir, config.get("tts", {}))
            logger.info(f"Audio generation complete: {audio_result['output_path']}")
            logger.info(f"Audio duration: {audio_result['audio_duration_seconds']:.2f} seconds")
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
    
    # TODO: Implement Video Compilation Pipeline
    
    # TODO: Implement Final Assembly
    
    logger.info(f"Processing completed. Project directory: {project_dir}")
    return project_dir


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Transcript and Video Automation System")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process a YouTube video")
    process_parser.add_argument("youtube_url", help="YouTube video URL to process")
    process_parser.add_argument("--output-dir", help="Custom output directory")
    process_parser.add_argument("--generate-audio", action="store_true", help="Generate audio from transcript")
    
    # Transcript-only command
    transcript_parser = subparsers.add_parser("transcript", help="Process transcript only")
    transcript_parser.add_argument("youtube_url", help="YouTube video URL to process")
    transcript_parser.add_argument("--output-dir", help="Custom output directory")
    transcript_parser.add_argument("--generate-audio", action="store_true", help="Generate audio from transcript")
    
    # Video-only command
    video_parser = subparsers.add_parser("video", help="Generate video only")
    video_parser.add_argument("--duration", type=int, default=10800, help="Target duration in seconds")
    video_parser.add_argument("--output-dir", help="Custom output directory")
    
    # TTS-only command
    tts_parser = subparsers.add_parser("tts", help="Generate audio from transcript")
    tts_parser.add_argument("--transcript-dir", required=True, help="Directory containing the transcript")
    tts_parser.add_argument("--language", default="e", help="Language code (e.g., 'e' for English)")
    tts_parser.add_argument("--voice", help="Voice to use")
    tts_parser.add_argument("--speed", type=float, default=1.0, help="Speech speed")
    
    return parser.parse_args()


def main():
    """
    Main function to orchestrate the automation workflow.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    logger.info("Starting Transcript and Video Automation System")
    
    try:
        # Parse arguments
        args = parse_arguments()
    
        # Load configuration
        config = load_config(args.config)
        
        # Set log level from configuration
        log_level = getattr(logging, config["general"]["log_level"].upper())
        logger.setLevel(log_level)
        
        # Process based on command
        if args.command == "process":
            process_video(args.youtube_url, config, args.output_dir, args.generate_audio)
        elif args.command == "transcript":
            # TODO: Implement transcript-only processing
            logger.info("Transcript-only processing not yet implemented")
            if args.generate_audio:
                logger.info("Audio generation requested but transcript processing not implemented yet")
        elif args.command == "video":
            # TODO: Implement video-only processing
            logger.info("Video-only processing not yet implemented")
        elif args.command == "tts":
            try:
                from transcript_pipeline.tts.tts_generator import generate_audio_from_transcript
                
                # Override TTS configuration with command-line arguments
                tts_config = config.get("tts", {}).copy()
                if args.language:
                    tts_config["language"] = args.language
                if args.voice:
                    tts_config["voice_pack"] = args.voice
                if args.speed:
                    tts_config["speed"] = args.speed
                
                # Generate audio
                logger.info(f"Generating audio from transcript in {args.transcript_dir}...")
                audio_result = generate_audio_from_transcript(args.transcript_dir, tts_config)
                logger.info(f"Audio generation complete: {audio_result['output_path']}")
                logger.info(f"Audio duration: {audio_result['audio_duration_seconds']:.2f} seconds")
            except Exception as e:
                logger.exception(f"Error generating audio: {str(e)}")
                return 1
        else:
            logger.error("No command specified")
            return 1
        
        logger.info("Transcript and Video Automation System completed successfully")
        return 0
    except Exception as e:
        logger.exception(f"Error in automation workflow: {e}")
        return 1




if __name__ == "__main__":
    sys.exit(main())
