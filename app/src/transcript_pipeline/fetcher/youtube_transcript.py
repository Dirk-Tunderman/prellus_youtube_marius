"""
YouTube Transcript Fetcher Module

This module provides functionality for extracting transcripts from YouTube videos
using the youtube-transcript-api library. It handles fetching transcripts in various
languages and can fall back to auto-generated transcripts if needed.

The module is part of the Transcript Processing Pipeline and operates independently
from the Video Compilation Pipeline.
"""

import logging, re
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the YouTube Transcript API
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
)

logger = logging.getLogger(__name__)

class YouTubeTranscriptFetcher:
    """
    Class for fetching transcripts from YouTube videos.

    This class provides methods for extracting raw transcript data from YouTube videos,
    including handling different languages and auto-generated transcripts.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the YouTube transcript fetcher.

        Args:
            config (Dict[str, Any], optional): Configuration parameters for the fetcher.
                May include language preferences, fallback options, etc.
        """
        self.config = config or {}

        self.preferred_language = self.config.get("language", "en")
        self.fallback_to_auto = self.config.get("fallback_to_auto_generated", True)
        logger.info("Initialized YouTubeTranscriptFetcher")

    @staticmethod
    def extract_video_id(video_url: str) -> str:
        """
        Extract the video ID from a YouTube URL.

        Args:
            video_url (str): YouTube video URL

        Returns:
            str: YouTube video ID

        Raises:
            ValueError: If the URL doesn't contain a valid YouTube video ID
        """
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",  # Standard YouTube URLs
            r"(?:embed\/)([0-9A-Za-z_-]{11})",  # Embed URLs
            r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",  # Short URLs
        ]

        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)

        raise ValueError(f"Could not extract video ID from URL: {video_url}")

    def fetch_transcript(self, video_url: str) -> List[Dict[str, Any]]:
        """
        Fetch transcript from a YouTube video.

        Args:
            video_url (str): YouTube video URL or ID

        Returns:
            List[Dict[str, Any]]: List of transcript segments with text and timestamps

        Raises:
            ValueError: If no transcript could be found for the video
        """
        try:
            # Extract video ID if a URL was provided
            if "youtube.com" in video_url or "youtu.be" in video_url:
                video_id = self.extract_video_id(video_url)
            else:
                # Assume the input is already a video ID
                video_id = video_url

            logger.info(f"Fetching transcript for YouTube video: {video_id}")

            # Try to get transcript in preferred language
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[self.preferred_language]
                )
                logger.info(
                    f"Found transcript in preferred language: {self.preferred_language}"
                )
                return transcript
            except NoTranscriptFound:
                # If preferred language not found, try to list available transcripts
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

                # Try to get manually created transcript in any language
                try:
                    # Get first manually created transcript
                    transcript = (
                        transcript_list.find_manually_created_transcript().fetch()
                    )
                    lang = (
                        transcript_list.find_manually_created_transcript().language_code
                    )
                    logger.info(
                        f"Found manually created transcript in language: {lang}"
                    )
                    return transcript
                except NoTranscriptFound:
                    # If no manually created transcript, try auto-generated if allowed
                    if self.fallback_to_auto:
                        try:
                            # Get first auto-generated transcript
                            transcript = (
                                transcript_list.find_generated_transcript().fetch()
                            )
                            lang = (
                                transcript_list.find_generated_transcript().language_code
                            )
                            logger.info(
                                f"Found auto-generated transcript in language: {lang}"
                            )
                            return transcript
                        except NoTranscriptFound:
                            pass

            # If we get here, no transcript was found
            raise ValueError(f"No transcript found for video: {video_id}")

        except TranscriptsDisabled:
            logger.error(f"Transcripts are disabled for video: {video_id}")
            raise ValueError(f"Transcripts are disabled for video: {video_id}")
        except Exception as e:
            logger.exception(f"Error fetching transcript: {e}")
            raise

    def fetch_transcript_with_metadata(self, video_url: str) -> Dict[str, Any]:
        """
        Fetch transcript and video metadata from a YouTube video.

        This method fetches the transcript segments, cleans them by removing
        non-speech elements enclosed in square brackets (e.g., "[Music]",
        "[Applause]"), and adds video metadata before returning the combined data.

        Args:
            video_url (str): YouTube video URL or ID

        Returns:
            Dict[str, Any]: Dictionary containing cleaned transcript data and metadata
        """
        # Get the raw transcript
        transcript = self.fetch_transcript(video_url)

        # Clean the transcript segments by removing text in square brackets
        cleaned_transcript = []
        for segment in transcript:
            segment_copy = (
                segment.copy()
            )  # Create a copy to avoid modifying the original

            # Remove text enclosed in square brackets
            cleaned_text = re.sub(r"\[.*?\]", "", segment["text"])
            # Remove any extra whitespace that might result
            cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

            # Update the segment with cleaned text
            segment_copy["text"] = cleaned_text

            # Only add segments that still have text after cleaning
            if cleaned_text:
                cleaned_transcript.append(segment_copy)

        # Extract video ID
        video_id = (
            self.extract_video_id(video_url)
            if "youtube.com" in video_url or "youtu.be" in video_url
            else video_url
        )

        # TODO: Fetch additional metadata (title, channel, etc.) using a library like pytube
        
        # Format current date for frontend display
        current_datetime = datetime.now()
        day = current_datetime.day
        # Add comma after the day
        formatted_date = current_datetime.strftime(f"%B {day}, %Y %H:%M")

        return {
            "metadata": {
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "fetch_date": current_datetime.isoformat(),
                "date": formatted_date,
                "timestamp": {
                    "start": (
                        cleaned_transcript[0]["start"] if cleaned_transcript else 0
                    ),
                    "end": (
                        cleaned_transcript[-1]["start"]
                        + cleaned_transcript[-1]["duration"]
                        if cleaned_transcript
                        else 0
                    ),
                },
            },
            "transcript": cleaned_transcript,
        }
