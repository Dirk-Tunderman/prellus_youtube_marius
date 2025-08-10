"""
Transcript Storage Management

This module handles the storage structure and file management for transcripts.
It ensures consistent storage patterns and maintains the exact directory structure
that the system expects.

Storage Structure:
data/transcripts/{video_id}_{timestamp}/
├── raw/
│   ├── transcript.json     # Raw transcript data
│   └── transcript.txt      # Plain text version
├── processed/
│   ├── narrative_transcript.txt    # Final processed transcript
│   ├── master_document.txt         # Master document (from simple processor)
│   └── response_*.txt              # Individual responses (from simple processor)
└── metadata.json          # Video metadata
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TranscriptStorage:
    """Manages transcript storage structure and file operations."""
    
    def __init__(self, base_dir: str = "data/transcripts"):
        """
        Initialize transcript storage manager.
        
        Args:
            base_dir: Base directory for transcript storage
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def create_video_directory(self, video_id: str, timestamp: Optional[str] = None) -> str:
        """
        Create directory structure for a video.
        
        Args:
            video_id: YouTube video ID
            timestamp: Optional timestamp, will generate if not provided
            
        Returns:
            Path to the created video directory
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        video_dir = os.path.join(self.base_dir, f"{video_id}_{timestamp}")
        
        # Create directory structure
        os.makedirs(os.path.join(video_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(video_dir, "processed"), exist_ok=True)
        
        logger.info(f"Created video directory: {video_dir}")
        return video_dir
    
    def save_raw_transcript(self, video_dir: str, transcript_data: Any, plain_text: str) -> Dict[str, str]:
        """
        Save raw transcript data.
        
        Args:
            video_dir: Video directory path
            transcript_data: Raw transcript data (list or dict)
            plain_text: Plain text version of transcript
            
        Returns:
            Dictionary with paths to saved files
        """
        raw_dir = os.path.join(video_dir, "raw")
        
        # Save JSON data
        json_path = os.path.join(raw_dir, "transcript.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        # Save plain text
        txt_path = os.path.join(raw_dir, "transcript.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(plain_text)
        
        logger.info(f"Saved raw transcript: {json_path}, {txt_path}")
        
        return {
            "json_path": json_path,
            "plain_text_path": txt_path
        }
    
    def save_processed_transcript(self, video_dir: str, processed_text: str) -> str:
        """
        Save processed transcript.
        
        Args:
            video_dir: Video directory path
            processed_text: Processed transcript text
            
        Returns:
            Path to saved processed transcript
        """
        processed_dir = os.path.join(video_dir, "processed")
        processed_path = os.path.join(processed_dir, "narrative_transcript.txt")
        
        with open(processed_path, "w", encoding="utf-8") as f:
            f.write(processed_text)
        
        logger.info(f"Saved processed transcript: {processed_path}")
        return processed_path
    
    def save_master_document(self, video_dir: str, master_document: str) -> str:
        """
        Save master document.
        
        Args:
            video_dir: Video directory path
            master_document: Master document text
            
        Returns:
            Path to saved master document
        """
        processed_dir = os.path.join(video_dir, "processed")
        master_path = os.path.join(processed_dir, "master_document.txt")
        
        with open(master_path, "w", encoding="utf-8") as f:
            f.write(master_document)
        
        logger.info(f"Saved master document: {master_path}")
        return master_path
    
    def save_response(self, video_dir: str, response_num: int, response_text: str) -> str:
        """
        Save individual response.
        
        Args:
            video_dir: Video directory path
            response_num: Response number
            response_text: Response text
            
        Returns:
            Path to saved response
        """
        processed_dir = os.path.join(video_dir, "processed")
        response_path = os.path.join(processed_dir, f"response_{response_num}.txt")
        
        with open(response_path, "w", encoding="utf-8") as f:
            f.write(response_text)
        
        logger.info(f"Saved response {response_num}: {response_path}")
        return response_path
    
    def save_metadata(self, video_dir: str, metadata: Dict[str, Any]) -> str:
        """
        Save video metadata.
        
        Args:
            video_dir: Video directory path
            metadata: Metadata dictionary
            
        Returns:
            Path to saved metadata file
        """
        metadata_path = os.path.join(video_dir, "metadata.json")
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata: {metadata_path}")
        return metadata_path
    
    def load_raw_transcript(self, video_dir: str) -> Dict[str, Any]:
        """
        Load raw transcript data.
        
        Args:
            video_dir: Video directory path
            
        Returns:
            Dictionary with transcript data and text
        """
        json_path = os.path.join(video_dir, "raw", "transcript.json")
        txt_path = os.path.join(video_dir, "raw", "transcript.txt")
        
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Raw transcript not found: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)
        
        plain_text = ""
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                plain_text = f.read()
        
        return {
            "data": transcript_data,
            "text": plain_text,
            "json_path": json_path,
            "txt_path": txt_path
        }
    
    def get_video_directories(self) -> list[str]:
        """
        Get list of all video directories.
        
        Returns:
            List of video directory paths
        """
        if not os.path.exists(self.base_dir):
            return []
        
        directories = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path):
                directories.append(item_path)
        
        return sorted(directories)
    
    def cleanup_old_directories(self, keep_count: int = 10) -> int:
        """
        Clean up old video directories, keeping only the most recent ones.
        
        Args:
            keep_count: Number of directories to keep
            
        Returns:
            Number of directories removed
        """
        directories = self.get_video_directories()
        
        if len(directories) <= keep_count:
            return 0
        
        # Sort by modification time (newest first)
        directories.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Remove old directories
        removed_count = 0
        for old_dir in directories[keep_count:]:
            try:
                import shutil
                shutil.rmtree(old_dir)
                logger.info(f"Removed old directory: {old_dir}")
                removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove directory {old_dir}: {e}")
        
        return removed_count
