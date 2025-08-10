"""
Transcript Fetcher and Storage Module

This module provides functionality for fetching YouTube transcripts and
storing them in an organized directory structure. It creates a dedicated
directory for each YouTube video and saves the raw transcript data.

This module builds on the YouTubeTranscriptFetcher to handle the transcript
extraction and adds proper storage management.
"""

import os
import json
import logging
import shutil
import re
from datetime import datetime
from typing import Dict, Any, Optional

from src.core.fetcher.youtube_transcript import YouTubeTranscriptFetcher

logger = logging.getLogger(__name__)


class TranscriptManager:
    """
    Class for managing transcript fetching and storage.
    
    This class provides methods for fetching transcripts from YouTube videos and
    storing them in an organized directory structure for further processing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transcript manager.
        
        Args:
            config (Dict[str, Any], optional): Configuration parameters.
        """
        self.config = config or {}
        self.base_dir = self.config.get("base_directory", "data")
        self.transcripts_dir = os.path.join(self.base_dir, "transcripts")
        
        # Initialize the transcript fetcher
        youtube_config = self.config.get("youtube", {})
        self.fetcher = YouTubeTranscriptFetcher(youtube_config)
        
        logger.info("Initialized TranscriptManager")
    
    def setup_video_directory(self, video_id: str) -> str:
        """
        Set up a directory structure for a specific video.
        
        Creates the following structure:
        data/
          transcripts/
            {video_id}_{timestamp}/
              raw/
              processed/
              audio/
              final/
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            str: Path to the created video directory
        """
        # Create a timestamped directory name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_dir_name = f"{video_id}_{timestamp}"
        video_dir = os.path.join(self.transcripts_dir, video_dir_name)
        
        # Create the main directory and subdirectories
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(os.path.join(video_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(video_dir, "processed"), exist_ok=True)
        os.makedirs(os.path.join(video_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(video_dir, "final"), exist_ok=True)
        
        logger.info(f"Created directory structure for video: {video_dir}")
        return video_dir
    
    def fetch_and_store_transcript(self, youtube_url: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch transcript from YouTube and store it in the appropriate directory.
        
        Args:
            youtube_url (str): YouTube video URL
            json_data (Dict[str, Any], optional): Additional data including title
                
        Returns:
            Dict[str, Any]: Information about the fetched and stored transcript,
                including paths to the created files and directories
        """
        try:
            # Fetch the transcript with metadata
            logger.info(f"Fetching transcript for: {youtube_url}")
            transcript_data = self.fetcher.fetch_transcript_with_metadata(youtube_url)
            
            # Extract video ID
            video_id = transcript_data["metadata"]["video_id"]
            
            # Set up the directory structure
            video_dir = self.setup_video_directory(video_id)
            
            # Save the raw transcript data
            raw_transcript_path = os.path.join(video_dir, "raw", "transcript.json")
            with open(raw_transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2)
            
            # Save plain text version for convenience
            plain_text = self._transcript_to_plain_text(transcript_data["transcript"])
            plain_text_path = os.path.join(video_dir, "raw", "transcript.txt")
            with open(plain_text_path, 'w', encoding='utf-8') as f:
                f.write(plain_text)
            
            # Extract metadata and add title if provided
            metadata = transcript_data["metadata"].copy()
            if json_data and "title" in json_data:
                metadata["title"] = json_data["title"]
                logger.info(f"Added title to metadata: {json_data['title']}")
            
            # Save metadata separately
            metadata_path = os.path.join(video_dir, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Transcript successfully stored at: {raw_transcript_path}")
            
            return {
                "video_id": video_id,
                "video_dir": video_dir,
                "raw_transcript_path": raw_transcript_path,
                "plain_text_path": plain_text_path,
                "metadata_path": metadata_path,
                "transcript_data": transcript_data
            }
            
        except Exception as e:
            logger.exception(f"Error fetching and storing transcript: {e}")
            raise
    
    def _transcript_to_plain_text(self, transcript: list) -> str:
        """
        Convert transcript segments to plain text.
        
        This method processes the raw transcript segments to create a clean
        plain text version. It removes non-speech elements enclosed in square 
        brackets (e.g., "[Music]", "[Applause]") and joins the segments with 
        newlines.
        
        Args:
            transcript (list): List of transcript segments
            
        Returns:
            str: Plain text version of the transcript with non-speech elements removed
        """
        # Process each segment to remove content in square brackets
        clean_segments = []
        for segment in transcript:
            # Remove text enclosed in square brackets using regex
            cleaned_text = re.sub(r'\[.*?\]', '', segment["text"])
            # Remove any extra whitespace that might result
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            # Only add non-empty segments
            if cleaned_text:
                clean_segments.append(cleaned_text)
                
        return "\n\n".join(clean_segments)
    
    def clean_up_failed_directory(self, video_dir: str) -> None:
        """
        Clean up a directory structure in case of failure.
        
        Args:
            video_dir (str): Path to the video directory to clean up
        """
        try:
            if os.path.exists(video_dir):
                shutil.rmtree(video_dir)
                logger.info(f"Cleaned up directory: {video_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up directory {video_dir}: {e}")


def fetch_transcript(youtube_url: str, config: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to fetch and store a transcript.
    
    Args:
        youtube_url (str): YouTube video URL
        config (Dict[str, Any], optional): Configuration parameters
        json_data (Dict[str, Any], optional): Additional data including title
        
    Returns:
        Dict[str, Any]: Information about the fetched and stored transcript
    """
    manager = TranscriptManager(config)
    return manager.fetch_and_store_transcript(youtube_url, json_data)