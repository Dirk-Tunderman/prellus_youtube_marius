"""
Simple Transcript Processor - New Simplified Mechanism

This processor implements a streamlined approach:
1. Create master document with user instructions + original transcript
2. Generate content using max token output (180K chars OpenAI, 360K Anthropic)
3. Continue generation when more content is needed
4. Handle input window limits intelligently
"""

import os
import json
import time
import math
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from .litellm_processing import process_llm
from ..conversion import get_conversion_config

logger = logging.getLogger(__name__)

# ============================================================================
# Data Structures for Enhanced Section Tracking
# ============================================================================

@dataclass
class SectionBoundary:
    """Represents a single section within the document with precise boundaries."""
    section_id: str  # e.g., "1.1", "2.3"
    title: str
    start_char: int
    end_char: int
    target_chars: int
    content_type: str  # "introduction", "main_content", "transition", "conclusion"
    key_points: List[str] = field(default_factory=list)
    user_instructions: str = ""
    response_num: int = 0  # Which response will generate this section

@dataclass
class ResponseSection:
    """Groups sections that belong to a single LLM response."""
    response_num: int
    title: str
    sections: List[SectionBoundary]
    total_target_chars: int
    start_char: int
    end_char: int
    completion_status: str = "pending"  # "pending", "in_progress", "completed"
    actual_chars_generated: int = 0

@dataclass
class MasterDocumentStructure:
    """Complete document structure with all sections and response planning."""
    total_target_chars: int
    total_duration_minutes: float
    total_responses_needed: int
    response_sections: List[ResponseSection]
    user_structure_mapping: Dict[str, str] = field(default_factory=dict)
    section_index: Dict[str, SectionBoundary] = field(default_factory=dict)
    model_name: str = ""
    model_char_limit: int = 0
    
    def get_section_by_id(self, section_id: str) -> Optional[SectionBoundary]:
        """Get a section by its ID."""
        return self.section_index.get(section_id)
    
    def get_current_section(self, char_position: int) -> Optional[SectionBoundary]:
        """Find which section a character position falls within."""
        for section_id, section in self.section_index.items():
            if section.start_char <= char_position < section.end_char:
                return section
        return None
    
    def get_sections_for_response(self, response_num: int) -> List[SectionBoundary]:
        """Get all sections for a specific response number."""
        for response_section in self.response_sections:
            if response_section.response_num == response_num:
                return response_section.sections
        return []

class CharacterBoundaryManager:
    """Manages precise character counting and section boundaries."""
    
    def __init__(self, structure: MasterDocumentStructure):
        self.structure = structure
        self.section_progress = {}
        
    def update_progress(self, content: str) -> Dict[str, Any]:
        """Update progress tracking for all sections."""
        total_chars = len(content)
        
        progress_report = {
            "total_chars": total_chars,
            "total_target": self.structure.total_target_chars,
            "overall_percentage": (total_chars / self.structure.total_target_chars * 100),
            "sections_completed": [],
            "current_section": None,
            "sections_in_progress": [],
            "sections_pending": []
        }
        
        for section_id, section in self.structure.section_index.items():
            if total_chars >= section.end_char:
                progress_report["sections_completed"].append({
                    "id": section_id,
                    "title": section.title,
                    "chars": section.target_chars
                })
            elif total_chars >= section.start_char:
                chars_in_section = total_chars - section.start_char
                progress_report["current_section"] = section_id
                progress_report["sections_in_progress"].append({
                    "id": section_id,
                    "title": section.title,
                    "progress": chars_in_section,
                    "target": section.target_chars,
                    "percentage": (chars_in_section / section.target_chars * 100)
                })
            else:
                progress_report["sections_pending"].append({
                    "id": section_id,
                    "title": section.title
                })
        
        return progress_report
    
    def get_next_target(self, current_chars: int) -> Tuple[Optional[str], int]:
        """Get the next section and how many characters to generate."""
        sorted_sections = sorted(self.structure.section_index.values(), 
                               key=lambda s: s.start_char)
        
        for section in sorted_sections:
            if current_chars < section.end_char:
                remaining = section.end_char - max(current_chars, section.start_char)
                return section.section_id, remaining
        
        return None, 0
    
    def get_section_context(self, section_id: str, current_chars: int) -> Dict[str, Any]:
        """Get detailed context for a specific section."""
        section = self.structure.get_section_by_id(section_id)
        if not section:
            return {}
        
        chars_in_section = max(0, current_chars - section.start_char)
        
        return {
            "section_id": section_id,
            "title": section.title,
            "content_type": section.content_type,
            "key_points": section.key_points,
            "user_instructions": section.user_instructions,
            "start_char": section.start_char,
            "end_char": section.end_char,
            "target_chars": section.target_chars,
            "chars_generated": chars_in_section,
            "chars_remaining": section.target_chars - chars_in_section,
            "percentage_complete": (chars_in_section / section.target_chars * 100) if section.target_chars > 0 else 0
        }

# Constants for character/time conversion  
# Character conversion constants are now centralized in config.yaml
# Access via conversion module for easy modification

# Model-specific limits (characters AND tokens)
# IMPORTANT: We track both characters and actual API token limits
MODEL_LIMITS = {
    # OpenAI Models - GPT-5 Series (August 2025)
    "gpt-5": {"max_input": 1600000, "max_output": 128000 * 4, "max_output_tokens": 128000},
    "gpt-5-mini": {"max_input": 1600000, "max_output": 128000 * 4, "max_output_tokens": 128000},
    "gpt-5-nano": {"max_input": 1600000, "max_output": 128000 * 4, "max_output_tokens": 128000},
    "gpt-5-chat": {"max_input": 1600000, "max_output": 128000 * 4, "max_output_tokens": 128000},
    
    # OpenAI Models - GPT-4 Series
    "gpt-4o": {"max_input": 500000, "max_output": 16384 * 4, "max_output_tokens": 16384},
    "gpt-4o-mini": {"max_input": 500000, "max_output": 16384 * 4, "max_output_tokens": 16384},
    "gpt-4-turbo": {"max_input": 500000, "max_output": 4096 * 4, "max_output_tokens": 4096},
    "gpt-4": {"max_input": 30000, "max_output": 4096 * 4, "max_output_tokens": 4096},
    "gpt-3.5-turbo": {"max_input": 60000, "max_output": 4096 * 4, "max_output_tokens": 4096},

    # Anthropic Models - ACTUAL limit is 64,000 tokens (not 65,536)
    "claude-4-opus-20250514": {"max_input": 800000, "max_output": 64000 * 4, "max_output_tokens": 64000},
    "claude-4-sonnet-20250514": {"max_input": 800000, "max_output": 64000 * 4, "max_output_tokens": 64000},
    "claude-3-5-sonnet-20241022": {"max_input": 800000, "max_output": 64000 * 4, "max_output_tokens": 64000},
    "claude-3-5-haiku-20241022": {"max_input": 800000, "max_output": 64000 * 4, "max_output_tokens": 64000},
    "claude-3-7-sonnet-20250219": {"max_input": 800000, "max_output": 64000 * 4, "max_output_tokens": 64000},

    # Gemini Models - Very high token limits
    "gemini-2.5-pro-preview-06-05": {"max_input": 4000000, "max_output": 65536 * 4, "max_output_tokens": 65536},
    "gemini-2.0-flash-lite": {"max_input": 4000000, "max_output": 32768 * 4, "max_output_tokens": 32768},
    "gemini-1.5-pro": {"max_input": 4000000, "max_output": 32768 * 4, "max_output_tokens": 32768},
    "gemini-1.5-flash": {"max_input": 4000000, "max_output": 32768 * 4, "max_output_tokens": 32768},

    # Default fallback
    "default": {"max_input": 100000, "max_output": 16384 * 4, "max_output_tokens": 16384}
}


class SimpleTranscriptProcessor:
    """
    Simplified transcript processor using max token output approach.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the simple processor."""
        self.config = config
        self.ai_config = config.get("ai", {})
        self.model = self.ai_config.get("model", "claude-3-7-sonnet-20250219")
        
        # Get model limits
        self.model_limits = MODEL_LIMITS.get(self.model, MODEL_LIMITS["default"])
        logger.info(f"Initialized SimpleTranscriptProcessor with model: {self.model}")
        logger.info(f"Model limits - Input: {self.model_limits['max_input']:,} chars, Output: {self.model_limits['max_output']:,} chars")
    
    # ========================================================================
    # Helper Functions for Time Conversion and Section Management
    # ========================================================================
    
    def _convert_time_to_characters(self, time_str: str, speed: float = 1.0) -> int:
        """
        Convert time-based instructions to character counts.
        
        Args:
            time_str: Time string like "10 minutes", "1.5 hours", etc.
            speed: Playback speed (0.8 = slower, 1.0 = normal, 1.25 = faster)
            
        Returns:
            Number of characters for that duration
        """
        # Extract number and unit from time string
        pattern = r'(\d+(?:\.\d+)?)\s*(min(?:ute)?s?|hour?s?|hr?s?)'
        match = re.match(pattern, time_str.strip(), re.IGNORECASE)
        
        if not match:
            logger.warning(f"Could not parse time string: {time_str}")
            return 0
        
        value = float(match.group(1))
        unit = match.group(2).lower()
        
        # Convert to minutes
        if 'hour' in unit or unit.startswith('h'):
            minutes = value * 60
        else:
            minutes = value
        
        # Calculate characters based on reading speed
        # Slower speed = more content needed for same duration
        effective_reading_speed = (200 / speed)  # words per minute (base 200 WPM)
        chars_per_minute = effective_reading_speed * 5  # 5 chars per word including space
        
        return int(minutes * chars_per_minute)
    
    def _parse_time_based_instructions(self, instructions: str, total_chars: int) -> List[Dict[str, Any]]:
        """
        Parse user instructions containing time-based segments.
        
        Args:
            instructions: User instructions potentially containing time references
            total_chars: Total characters available
            
        Returns:
            List of parsed segments with character allocations
        """
        segments = []
        
        # Pattern for time ranges like "0-10 minutes" or "10 to 25 minutes"
        range_pattern = r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*min(?:ute)?s?\s*(?:about|on|covering|discussing)?\s*([^,\.\n]+)'
        
        # Pattern for duration like "first 10 minutes" or "next 15 minutes"
        duration_pattern = r'(?:first|next|last|then)?\s*(\d+(?:\.\d+)?)\s*min(?:ute)?s?\s*(?:about|on|covering|discussing)?\s*([^,\.\n]+)'
        
        current_position = 0
        speed = self.ai_config.get("speed", 1.0)
        
        # Find all time-based instructions
        for match in re.finditer(range_pattern, instructions):
            start_min = float(match.group(1))
            end_min = float(match.group(2))
            topic = match.group(3).strip()
            
            start_chars = self._convert_time_to_characters(f"{start_min} minutes", speed)
            end_chars = self._convert_time_to_characters(f"{end_min} minutes", speed)
            
            segments.append({
                "start_min": start_min,
                "end_min": end_min,
                "start_char": start_chars,
                "end_char": end_chars,
                "duration_chars": end_chars - start_chars,
                "topic": topic,
                "type": "time_range"
            })
            current_position = end_chars
        
        # Also handle single duration mentions
        if not segments:  # Only if we didn't find range patterns
            for match in re.finditer(duration_pattern, instructions):
                duration_min = float(match.group(1))
                topic = match.group(2).strip()
                
                duration_chars = self._convert_time_to_characters(f"{duration_min} minutes", speed)
                
                segments.append({
                    "start_min": get_conversion_config().chars_to_minutes(current_position, 1.0 / speed) if current_position else 0,
                    "end_min": get_conversion_config().chars_to_minutes(current_position + duration_chars, 1.0 / speed),
                    "start_char": current_position,
                    "end_char": current_position + duration_chars,
                    "duration_chars": duration_chars,
                    "topic": topic,
                    "type": "duration"
                })
                current_position += duration_chars
        
        # Log what we parsed
        if segments:
            logger.info("📊 Parsed time-based instructions:")
            for seg in segments:
                logger.info(f"   {seg['start_min']:.1f}-{seg['end_min']:.1f} min: {seg['topic'][:50]}... ({seg['duration_chars']:,} chars)")
        
        return segments
    
    def _calculate_section_boundaries(
        self, 
        target_length: int, 
        user_instructions: Dict[str, str],
        response_plan: Dict[str, Any]
    ) -> List[SectionBoundary]:
        """
        Calculate precise section boundaries based on user instructions and response plan.
        
        Args:
            target_length: Total target character count
            user_instructions: Extracted user instructions
            response_plan: Response planning with character allocations
            
        Returns:
            List of SectionBoundary objects with precise character ranges
        """
        sections = []
        
        # Check if user provided time-based structure
        script_structure = user_instructions.get("script_structure", "")
        time_segments = self._parse_time_based_instructions(script_structure, target_length)
        
        if time_segments:
            # Create sections from time-based instructions
            for idx, segment in enumerate(time_segments):
                response_num = self._determine_response_for_position(
                    segment['start_char'], response_plan
                )
                
                section = SectionBoundary(
                    section_id=f"{response_num}.{idx + 1}",
                    title=segment['topic'],
                    start_char=segment['start_char'],
                    end_char=segment['end_char'],
                    target_chars=segment['duration_chars'],
                    content_type=self._determine_content_type(idx, len(time_segments)),
                    key_points=[segment['topic']],
                    user_instructions=f"Cover this topic from {segment['start_min']:.1f} to {segment['end_min']:.1f} minutes",
                    response_num=response_num
                )
                sections.append(section)
        else:
            # Create default sections based on response plan
            for response_info in response_plan['response_plan']:
                response_num = response_info['response_num']
                start_char = sum(r['target_chars'] for r in response_plan['response_plan'][:response_num-1])
                end_char = start_char + response_info['target_chars']
                
                # Create 2-3 sections per response for better granularity
                sections_per_response = 3 if response_info['target_chars'] > 30000 else 2
                chars_per_section = response_info['target_chars'] // sections_per_response
                
                for section_idx in range(sections_per_response):
                    section_start = start_char + (section_idx * chars_per_section)
                    section_end = section_start + chars_per_section
                    if section_idx == sections_per_response - 1:
                        section_end = end_char  # Last section takes remaining chars
                    
                    section = SectionBoundary(
                        section_id=f"{response_num}.{section_idx + 1}",
                        title=f"Section {response_num}.{section_idx + 1}",
                        start_char=section_start,
                        end_char=section_end,
                        target_chars=section_end - section_start,
                        content_type=self._determine_content_type_for_position(
                            section_start, target_length
                        ),
                        key_points=[],
                        user_instructions="",
                        response_num=response_num
                    )
                    sections.append(section)
        
        return sections
    
    def _determine_response_for_position(self, char_position: int, response_plan: Dict[str, Any]) -> int:
        """Determine which response number a character position falls into."""
        cumulative_chars = 0
        for response_info in response_plan['response_plan']:
            cumulative_chars += response_info['target_chars']
            if char_position < cumulative_chars:
                return response_info['response_num']
        return response_plan['response_plan'][-1]['response_num']
    
    def _determine_content_type(self, index: int, total: int) -> str:
        """Determine content type based on position in sequence."""
        if index == 0:
            return "introduction"
        elif index == total - 1:
            return "conclusion"
        elif index == total - 2:
            return "transition"
        else:
            return "main_content"
    
    def _determine_content_type_for_position(self, char_position: int, total_chars: int) -> str:
        """Determine content type based on character position."""
        position_ratio = char_position / total_chars
        
        if position_ratio < 0.15:
            return "introduction"
        elif position_ratio > 0.85:
            return "conclusion"
        elif 0.4 < position_ratio < 0.45 or 0.7 < position_ratio < 0.75:
            return "transition"
        else:
            return "main_content"
    
    def _parse_structured_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        """
        Parse the structured outline from master document.
        
        Args:
            outline_text: The generated outline text
            
        Returns:
            List of parsed sections with details
        """
        sections = []
        
        # Pattern for section lines: SECTION_X.Y | start-end chars | topics
        section_pattern = r'SECTION_(\d+\.\d+)\s*\|\s*(\d+)-(\d+)\s*chars?\s*\|\s*([^\n]+)'
        
        for match in re.finditer(section_pattern, outline_text):
            section_id = match.group(1)
            start_char = int(match.group(2))
            end_char = int(match.group(3))
            topics = match.group(4).strip()
            
            sections.append({
                'id': section_id,
                'start': start_char,
                'end': end_char,
                'chars': end_char - start_char,
                'topics': topics,
                'response_num': int(section_id.split('.')[0])
            })
        
        return sections
    
    def _validate_outline_structure(self, outline: str, target_length: int) -> Tuple[bool, str]:
        """
        Basic validation that the outline isn't empty.
        
        Args:
            outline: Generated outline text
            target_length: Target character count
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic sanity checks only
        if not outline or len(outline.strip()) < 50:
            return False, "Outline is empty or too short"
        
        # Check if it contains some basic structure indicators
        if "SECTION" not in outline.upper() and "RESPONSE" not in outline.upper():
            return False, "Outline appears to lack basic structure"
        
        return True, "Valid"
    
    def _extract_response_titles(self, master_document: str) -> Dict[int, str]:
        """Extract meaningful response titles from master document."""
        titles = {}
        
        # Pattern to match response titles: Response 1: [Title]
        import re
        pattern = r'Response (\d+):\s*([^\[\n]+?)(?:\s*\[|$)'
        
        matches = re.findall(pattern, master_document)
        for match in matches:
            response_num = int(match[0])
            title = match[1].strip()
            # Clean up the title
            title = title.replace('[', '').replace(']', '').strip()
            titles[response_num] = title
        
        # Log what we found
        if titles:
            logger.info("📋 Extracted response titles:")
            for num, title in titles.items():
                logger.info(f"   Response {num}: {title}")
        else:
            logger.warning("⚠️ No response titles found in master document")
            # Create default titles
            for i in range(1, 10):  # Up to 10 responses
                titles[i] = f"Content Part {i}"
        
        return titles
    
    def process(
        self,
        transcript_text: str,
        output_dir: Optional[str] = None,
        mock_mode: bool = False
    ) -> str:
        """
        Process transcript using the simplified mechanism.
        
        Args:
            transcript_text: Original transcript text
            output_dir: Directory to save intermediate files
            mock_mode: Whether to use mock mode
            
        Returns:
            Processed transcript text
        """
        logger.info("🚀 Starting Simple Transcript Processing")
        
        # Calculate target length
        target_length = self._calculate_target_length(transcript_text)
        logger.info(f"📏 Target length: {target_length:,} characters")
        
        # Step 1: Create master document with response planning
        logger.info("📋 Step 1: Creating master document with response planning...")
        master_document, structure = self._create_master_document(transcript_text, target_length)
        
        if output_dir:
            # Save master document text
            master_doc_path = os.path.join(output_dir, "master_document.txt")
            with open(master_doc_path, "w", encoding="utf-8") as f:
                f.write(master_document)
            logger.info(f"💾 Saved master document to {master_doc_path}")
            
            # Save structured data as JSON
            structure_path = os.path.join(output_dir, "document_structure.json")
            structure_dict = {
                "total_target_chars": structure.total_target_chars,
                "total_duration_minutes": structure.total_duration_minutes,
                "total_responses_needed": structure.total_responses_needed,
                "model_name": structure.model_name,
                "model_char_limit": structure.model_char_limit,
                "sections": [
                    {
                        "id": section.section_id,
                        "title": section.title,
                        "start_char": section.start_char,
                        "end_char": section.end_char,
                        "target_chars": section.target_chars,
                        "content_type": section.content_type,
                        "response_num": section.response_num
                    }
                    for section in structure.section_index.values()
                ]
            }
            with open(structure_path, "w", encoding="utf-8") as f:
                json.dump(structure_dict, f, indent=2)
            logger.info(f"💾 Saved document structure to {structure_path}")
        
        # Step 2: Generate content using response-aware approach with structure
        logger.info("✨ Step 2: Generating content with response planning...")
        processed_transcript = self._generate_content_with_structure(
            transcript_text, master_document, structure, output_dir
        )
        
        logger.info(f"🎉 Processing complete! Generated {len(processed_transcript):,} characters")
        return processed_transcript
    
    def _calculate_target_length(self, transcript_text: str) -> int:
        """Calculate target length based on user input or default scaling."""
        # Check if user specified duration (minutes)
        duration_minutes = self.ai_config.get("length")
        if duration_minutes:
            # Convert minutes to characters using centralized conversion config
            target_length = get_conversion_config().minutes_to_chars(duration_minutes, 1.0)
            logger.info(f"📊 Target from duration: {duration_minutes} min → {target_length:,} chars (using {get_conversion_config().chars_per_minute} chars/min)")
            return target_length
        
        # Check if user specified character count directly
        target_chars = self.ai_config.get("length_in_chars")
        if target_chars:
            logger.info(f"📊 Target from config: {target_chars:,} chars")
            return target_chars
        
        # Default: same length as original
        original_length = len(transcript_text)
        logger.info(f"📊 Target (default): {original_length:,} chars (same as original)")
        return original_length
    
    def _create_master_document(self, transcript_text: str, target_length: int) -> tuple[str, MasterDocumentStructure]:
        """Create master document with structured data and validation."""
        logger.info("🎯 Creating master document with response planning...")

        # First, create response plan based on model capacity
        response_plan = self._create_response_plan(target_length)

        # Get user instructions
        user_instructions = self._extract_user_instructions()

        # Create master document prompt with response planning
        master_prompt = self._build_master_document_prompt(
            transcript_text, target_length, user_instructions, response_plan
        )
        
        # Generate master document with enhanced error handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Dynamic token allocation based on response count - scale with complexity
                base_tokens = 2000
                tokens_per_response = 1500
                master_doc_tokens = base_tokens + (response_plan['responses_needed'] * tokens_per_response)
                
                logger.info(f"📋 Master outline generation (attempt {attempt + 1}/{max_retries})")
                logger.info(f"   Max tokens: {master_doc_tokens} (scaled for {response_plan['responses_needed']} responses)")

                master_document = process_llm(
                    context="Create the concise outline as specified.",
                    system_prompt=master_prompt,
                    model=self.model,
                    max_tokens=master_doc_tokens,
                    temperature=0.3,  # Lower temperature for structured output
                    max_retries=5
                )
                
                # Validate the outline
                is_valid, error_msg = self._validate_outline_structure(master_document, target_length)
                
                if is_valid:
                    logger.info(f"✅ Master outline validated: {len(master_document):,} chars")
                    break
                else:
                    logger.warning(f"❌ Outline validation failed: {error_msg}")
                    if attempt < max_retries - 1:
                        logger.info("🔄 Regenerating with stricter constraints...")
                        # Add validation error to prompt for next attempt
                        master_prompt = master_prompt.replace(
                            "Generate the CONCISE OUTLINE now.",
                            f"PREVIOUS ATTEMPT FAILED: {error_msg}\n\nGenerate a CORRECTED CONCISE OUTLINE now."
                        )
                    else:
                        logger.warning("⚠️ Using outline despite validation issues")
                        
            except Exception as e:
                if "overloaded" in str(e).lower() and attempt == 0:
                    logger.warning("⚠️ Primary model overloaded, attempting fallback...")
                    
                    # Try fallback models
                    fallback_models = self.ai_config.get("fallback_models", ["gemini-2.0-flash-lite"])
                    fallback_enabled = self.ai_config.get("fallback_enabled", True)
                    
                    if fallback_enabled and fallback_models:
                        for fallback_model in fallback_models:
                            try:
                                logger.info(f"🔄 Trying fallback model: {fallback_model}")
                                master_document = process_llm(
                                    context="Create the concise outline as specified.",
                                    system_prompt=master_prompt,
                                    model=fallback_model,
                                    max_tokens=2000,
                                    temperature=0.3,
                                    max_retries=3
                                )
                                logger.info(f"✅ Fallback model {fallback_model} succeeded!")
                                break
                            except Exception as fallback_error:
                                logger.warning(f"❌ Fallback model {fallback_model} also failed: {fallback_error}")
                                continue
                        else:
                            # All fallbacks failed
                            logger.error("🚨 All models are currently overloaded")
                            raise Exception("All AI models are currently overloaded - please try again later") from e
                    else:
                        raise Exception("Primary model overloaded - please try again later") from e
                else:
                    raise e
        
        # Extract response titles from master document
        response_titles = self._extract_response_titles(master_document)
        
        # Create structured data from the outline
        structure = self._create_structured_data(
            master_document, target_length, user_instructions, response_plan, response_titles
        )
        
        # Log structure summary
        logger.info(f"📊 Master Document Structure Created:")
        logger.info(f"   Total sections: {len(structure.section_index)}")
        logger.info(f"   Responses needed: {structure.total_responses_needed}")
        logger.info(f"   Target length: {structure.total_target_chars:,} chars")
        logger.info(f"   Duration: {structure.total_duration_minutes:.1f} minutes")
        
        return master_document, structure
    
    def _create_structured_data(
        self, 
        master_document: str, 
        target_length: int,
        user_instructions: Dict[str, str],
        response_plan: Dict[str, Any],
        response_titles: Dict[int, str]
    ) -> MasterDocumentStructure:
        """Create structured data from master document outline."""
        
        # Parse sections from the outline
        parsed_sections = self._parse_structured_outline(master_document)
        
        # Calculate section boundaries
        section_boundaries = self._calculate_section_boundaries(
            target_length, user_instructions, response_plan
        )
        
        # If we parsed sections from outline, update boundaries with topics
        if parsed_sections:
            for parsed in parsed_sections:
                for boundary in section_boundaries:
                    if boundary.section_id == parsed['id']:
                        boundary.title = parsed.get('topics', boundary.title)
                        break
        
        # Create response sections
        response_sections = []
        for resp_info in response_plan['response_plan']:
            resp_num = resp_info['response_num']
            resp_sections = [s for s in section_boundaries if s.response_num == resp_num]
            
            if resp_sections:
                start_char = min(s.start_char for s in resp_sections)
                end_char = max(s.end_char for s in resp_sections)
                
                response_title = response_titles.get(resp_num, f"Content Part {resp_num}")
                response_sections.append(ResponseSection(
                    response_num=resp_num,
                    title=response_title,
                    sections=resp_sections,
                    total_target_chars=resp_info['target_chars'],
                    start_char=start_char,
                    end_char=end_char
                ))
        
        # Create section index
        section_index = {s.section_id: s for s in section_boundaries}
        
        # Create the structure
        structure = MasterDocumentStructure(
            total_target_chars=target_length,
            total_duration_minutes=get_conversion_config().chars_to_minutes(target_length),
            total_responses_needed=response_plan['responses_needed'],
            response_sections=response_sections,
            user_structure_mapping={},
            section_index=section_index,
            model_name=self.model,
            model_char_limit=self.model_limits.get("max_output", 65536)
        )
        
        return structure
    
    def _extract_user_instructions(self) -> Dict[str, str]:
        """Extract all user instructions from config."""
        instructions = {}

        # Extract all prompt components
        instructions["role"] = self.ai_config.get("prompt_role", "You are an expert writer tasked with processing transcript content.")
        instructions["script_structure"] = self.ai_config.get("prompt_script_structure", "")
        instructions["tone_style"] = self.ai_config.get("prompt_tone_style", "")
        instructions["retention_flow"] = self.ai_config.get("prompt_retention_flow", "")
        instructions["additional_instructions"] = self.ai_config.get("prompt_additional_instructions", "")

        # Log what we found
        has_custom = any(v and v != "You are an expert writer tasked with processing transcript content." for v in instructions.values())
        if has_custom:
            logger.info("🎨 Custom user instructions detected:")
            for key, value in instructions.items():
                if value and value != "You are an expert writer tasked with processing transcript content.":
                    logger.info(f"   - {key}: {len(value)} chars")
        else:
            logger.info("📝 Using default instructions (no custom user input)")

        return instructions

    def _parse_section_specific_requirements(self, user_instructions: Dict[str, str]) -> Dict[str, Any]:
        """
        Parse user instructions to extract section-specific requirements.
        Simple keyword-based parsing - no complex automatic detection.
        """
        section_reqs = {
            "intro_requirements": [],
            "outro_requirements": [],
            "content_specific": {},
            "literal_content": [],
            "general_requirements": {}
        }

        # Combine all instruction text for parsing
        all_text = ""
        for key, value in user_instructions.items():
            if value:
                all_text += f"{key}: {value}\n"

        # Simple keyword matching for intro requirements
        intro_keywords = ["intro", "introduction", "opening", "start", "begin", "hook", "opener", "lead-in", "beginning"]
        outro_keywords = ["outro", "conclusion", "ending", "close", "final", "last", "wrap", "summary", "call to action", "cta", "finish"]

        # Parse line by line for section-specific requirements
        lines = all_text.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if not line_lower:
                continue

            # Check for intro-specific requirements
            if any(keyword in line_lower for keyword in intro_keywords):
                section_reqs["intro_requirements"].append(line.strip())

            # Check for outro-specific requirements
            elif any(keyword in line_lower for keyword in outro_keywords):
                section_reqs["outro_requirements"].append(line.strip())

            # Extract literal content (content in quotes)
            import re
            quoted_content = re.findall(r'"([^"]*)"', line)
            for quote in quoted_content:
                if quote.strip():
                    section_reqs["literal_content"].append(quote.strip())

            # Extract content-specific requirements (mentions of specific topics/parts)
            content_keywords = ["part", "chapter", "section", "topic", "about", "cover", "discuss", "mention", "include"]
            if any(keyword in line_lower for keyword in content_keywords):
                # Simple extraction - store the line for later use
                section_reqs["content_specific"][len(section_reqs["content_specific"]) + 1] = line.strip()

        # Store general requirements
        section_reqs["general_requirements"] = {
            "role": user_instructions.get("role", ""),
            "tone_style": user_instructions.get("tone_style", ""),
            "retention_flow": user_instructions.get("retention_flow", ""),
            "script_structure": user_instructions.get("script_structure", ""),
            "additional_instructions": user_instructions.get("additional_instructions", "")
        }

        # Log what we found
        if section_reqs["intro_requirements"] or section_reqs["outro_requirements"] or section_reqs["literal_content"]:
            logger.info("🎯 Section-specific requirements detected:")
            if section_reqs["intro_requirements"]:
                logger.info(f"   🎬 Intro requirements: {len(section_reqs['intro_requirements'])} found")
            if section_reqs["outro_requirements"]:
                logger.info(f"   🎭 Outro requirements: {len(section_reqs['outro_requirements'])} found")
            if section_reqs["literal_content"]:
                logger.info(f"   📝 Literal content: {len(section_reqs['literal_content'])} phrases found")
            if section_reqs["content_specific"]:
                logger.info(f"   📖 Content-specific: {len(section_reqs['content_specific'])} requirements found")

        return section_reqs

    def _format_section_requirements_for_prompt(
        self,
        section_reqs: Dict[str, Any],
        current_section: str = "general",
        response_num: int = 1,
        is_final_response: bool = False
    ) -> str:
        """
        Format section-specific requirements into a prominent prompt section.

        Args:
            section_reqs: Section requirements from _parse_section_specific_requirements
            current_section: Current section being generated (intro, main, outro)
            response_num: Current response number
            is_final_response: Whether this is the final response

        Returns:
            Formatted string for inclusion in prompts
        """
        # Determine section type
        if response_num == 1:
            section_type = "INTRO"
        elif is_final_response:
            section_type = "OUTRO"
        else:
            section_type = f"PART {response_num - 1}"

        prompt_section = f"""
🚨🚨🚨 ABSOLUTE COMPLIANCE WITH USER INSTRUCTIONS REQUIRED 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⚡ **CRITICAL**: You MUST follow these user instructions exactly. Any deviation is unacceptable.
⚡ **AWARENESS**: You are creating {section_type} - pay special attention to requirements for this section.
⚡ **LITERAL COMPLIANCE**: When user specifies exact content, include it exactly as requested.

═══════════════════════════════════════════════════════════════

📍 **CURRENT SECTION CONTEXT:**
- You are creating: {section_type}
- Section purpose: {"Opening/hook content" if response_num == 1 else "Closing/conclusion content" if is_final_response else "Main content development"}
- Special attention needed for: {"Intro-specific requirements" if response_num == 1 else "Outro-specific requirements" if is_final_response else "Content-specific requirements"}

"""

        # Add section-specific requirements
        if response_num == 1 and section_reqs["intro_requirements"]:
            prompt_section += """🎬 **INTRO-SPECIFIC REQUIREMENTS (MANDATORY FOR THIS SECTION):**\n"""
            for req in section_reqs["intro_requirements"]:
                prompt_section += f"   ⚡ {req}\n"
            prompt_section += "\n"

        if is_final_response and section_reqs["outro_requirements"]:
            prompt_section += """🎭 **OUTRO-SPECIFIC REQUIREMENTS (MANDATORY FOR THIS SECTION):**\n"""
            for req in section_reqs["outro_requirements"]:
                prompt_section += f"   ⚡ {req}\n"
            prompt_section += "\n"

        # Add content-specific requirements
        if section_reqs["content_specific"]:
            prompt_section += f"""📖 **CONTENT-SPECIFIC REQUIREMENTS FOR {section_type}:**\n"""
            for req_num, req in section_reqs["content_specific"].items():
                prompt_section += f"   📋 {req}\n"
            prompt_section += "\n"

        # Add literal content requirements
        if section_reqs["literal_content"]:
            prompt_section += """⚡ **LITERAL REQUIREMENTS (MUST INCLUDE EXACTLY):**\n"""
            for literal in section_reqs["literal_content"]:
                prompt_section += f"""   🚨 "{literal}"\n"""
            prompt_section += "\n"

        # Add general requirements with emphasis
        prompt_section += """🔍 **USER INSTRUCTION ANALYSIS FOR THIS SECTION:**

📋 **GENERAL REQUIREMENTS (Apply to all sections):**\n"""

        if section_reqs["general_requirements"]["role"]:
            prompt_section += f"""   🎯 Role: {section_reqs["general_requirements"]["role"]}\n"""
        if section_reqs["general_requirements"]["tone_style"]:
            prompt_section += f"""   🎭 Tone & Style: {section_reqs["general_requirements"]["tone_style"]}\n"""
        if section_reqs["general_requirements"]["retention_flow"]:
            prompt_section += f"""   🔄 Retention & Flow: {section_reqs["general_requirements"]["retention_flow"]}\n"""

        prompt_section += "\n"

        # Add reminders for other sections (awareness)
        if not response_num == 1 and section_reqs["intro_requirements"]:
            prompt_section += """🎬 **REMEMBER - INTRO REQUIREMENTS (for reference):**\n"""
            for req in section_reqs["intro_requirements"]:
                prompt_section += f"   📝 {req}\n"
            prompt_section += "\n"

        if not is_final_response and section_reqs["outro_requirements"]:
            prompt_section += """🎭 **REMEMBER - OUTRO REQUIREMENTS (for reference):**\n"""
            for req in section_reqs["outro_requirements"]:
                prompt_section += f"   📝 {req}\n"
            prompt_section += "\n"

        prompt_section += """🚨 **CRITICAL REMINDERS FOR THIS SECTION:**
- You MUST follow user instructions exactly
- Pay special attention to requirements for """ + section_type + """
- Include any literal content specified for this section
- Maintain the exact tone and style requested by user

🔄 **ANTI-REPETITION GUIDANCE - CRITICAL FOR QUALITY:**
- This is part of a COMPLETE STORY/TRANSCRIPT - avoid repetitive content
- If a literal quote/phrase was already used in previous content, DO NOT repeat it again
- If a concept/topic was already covered, build upon it rather than repeating it
- Create a COHESIVE WHOLE that flows naturally from start to finish
- Each section should ADD NEW VALUE, not rehash previous content
- Only repeat content if the user EXPLICITLY requests repetition

═══════════════════════════════════════════════════════════════

"""

        return prompt_section
    
    def _extract_style_profile(self, user_instructions: Dict[str, str]) -> Dict[str, str]:
        """
        Extract and structure detailed style/tone profile from user instructions.
        Creates a comprehensive voice DNA for consistent application across all generations.
        """
        # Extract core elements
        role = user_instructions.get("role", "")
        tone_style = user_instructions.get("tone_style", "")
        script_structure = user_instructions.get("script_structure", "")
        additional = user_instructions.get("additional_instructions", "")
        
        # Create structured style profile
        style_profile = {}
        
        # NARRATIVE VOICE
        if role:
            style_profile["narrative_voice"] = f"You MUST embody this exact role throughout: {role}"
        else:
            style_profile["narrative_voice"] = "Professional, knowledgeable narrator"
        
        # TONE REQUIREMENTS
        if tone_style:
            # Extract specific tone words
            tone_words = []
            if "authoritative" in tone_style.lower():
                tone_words.append("authoritative and confident")
            if "empathetic" in tone_style.lower():
                tone_words.append("empathetic and understanding")
            if "grounded" in tone_style.lower():
                tone_words.append("grounded and realistic")
            if "engaging" in tone_style.lower():
                tone_words.append("engaging and captivating")
            if "professional" in tone_style.lower():
                tone_words.append("professional and polished")
            
            style_profile["tone_requirements"] = f"MANDATORY TONE: {', '.join(tone_words) if tone_words else 'As specified'} - {tone_style}"
        else:
            style_profile["tone_requirements"] = "Professional, engaging narrative tone"
        
        # WRITING STYLE DNA
        style_dna = []
        if "blend" in tone_style.lower() and "fiction" in tone_style.lower():
            style_dna.append("Blend fictional storytelling with real-world urgency")
        if "immersive" in script_structure.lower() or "sensory" in script_structure.lower():
            style_dna.append("Use vivid, immersive sensory details")
        if "punchy" in tone_style.lower() or "rhythmic" in tone_style.lower():
            style_dna.append("Alternate between punchy statements and longer reflective lines")
        if "repetition" in tone_style.lower():
            style_dna.append("Use deliberate repetition for emphasis")
        
        style_profile["writing_style_dna"] = "; ".join(style_dna) if style_dna else "Natural, flowing narrative style"
        
        # STRUCTURAL REQUIREMENTS
        if script_structure:
            # Extract key structural elements
            structure_elements = []
            if "intro" in script_structure.lower() or "opening" in script_structure.lower():
                structure_elements.append("Strong opening that hooks the audience")
            if "sections" in script_structure.lower() or "chapters" in script_structure.lower():
                structure_elements.append("Clear sectional progression")
            if "conclusion" in script_structure.lower() or "wrap" in script_structure.lower():
                structure_elements.append("Satisfying conclusion")
            
            style_profile["structural_requirements"] = f"FOLLOW USER STRUCTURE: {'; '.join(structure_elements)}"
        else:
            style_profile["structural_requirements"] = "Natural narrative progression"
        
        # ADDITIONAL SACRED REQUIREMENTS
        if additional:
            style_profile["sacred_additions"] = f"ABSOLUTE REQUIREMENTS: {additional}"
        
        return style_profile

    def _create_response_plan(self, target_length: int) -> dict:
        """Calculate how many responses needed based on model capacity."""

        # Special handling for models with observed real-world limits
        if self.model.startswith("gpt-5"):
            chars_per_response = get_conversion_config().gpt5_chars_per_response
            logger.info(f"🤖 GPT-5 detected: Using fixed {chars_per_response:,} chars per response limit")
        elif self.model.startswith("claude"):
            chars_per_response = get_conversion_config().claude_chars_per_response
            logger.info(f"🧠 Claude detected: Using fixed {chars_per_response:,} chars per response limit (safety measure)")
        else:
            # Standard calculation for all other models (75% safety margin)
            max_tokens = self.model_limits.get("max_output_tokens", 16384)
            safe_tokens = int(max_tokens * 0.75)
            chars_per_response = safe_tokens * 4
            logger.info(f"📊 Standard model: {chars_per_response:,} chars per response (75% of {max_tokens:,} tokens)")

        # Calculate response breakdown
        needed_responses = math.ceil(target_length / chars_per_response)

        response_plan = []
        remaining_chars = target_length

        for i in range(needed_responses):
            if i < needed_responses - 1:
                # Full response
                response_chars = chars_per_response
            else:
                # Final response - remaining amount
                response_chars = remaining_chars

            response_plan.append({
                "response_num": i + 1,
                "target_chars": response_chars,
                "percentage_of_total": (response_chars / target_length) * 100
            })

            remaining_chars -= response_chars

        logger.info(f"📊 Response Plan: {needed_responses} responses needed")
        for plan in response_plan:
            logger.info(f"   Response {plan['response_num']}: {plan['target_chars']:,} chars ({plan['percentage_of_total']:.1f}%)")

        return {
            "total_target": target_length,
            "responses_needed": needed_responses,
            "chars_per_full_response": chars_per_response,
            "response_plan": response_plan
        }

    def _build_master_document_prompt(
        self, transcript_text: str, target_length: int, user_instructions: Dict[str, str], response_plan: dict
    ) -> str:
        """Build CONCISE master document prompt - outline only, no content."""

        # Parse section-specific requirements
        section_reqs = self._parse_section_specific_requirements(user_instructions)

        # Parse time-based instructions if present
        script_structure = user_instructions.get("script_structure", "")
        time_segments = self._parse_time_based_instructions(script_structure, target_length) if script_structure else []
        
        # Prepare time conversion notes if needed
        time_conversion_note = ""
        if time_segments:
            time_conversion_note = "\n## TIME-BASED INSTRUCTIONS CONVERTED TO CHARACTERS:\n"
            for seg in time_segments:
                time_conversion_note += f"- {seg['start_min']:.1f}-{seg['end_min']:.1f} min → [{seg['start_char']:,}-{seg['end_char']:,}] chars: {seg['topic']}\n"
        
        # Build response allocation string
        response_allocation = ""
        for i, plan in enumerate(response_plan["response_plan"]):
            start_char = sum(p['target_chars'] for p in response_plan["response_plan"][:i])
            end_char = start_char + plan['target_chars']
            response_allocation += f"Response {plan['response_num']}: [{start_char:,}-{end_char:,}] chars\n"
        
        # Get model info
        model_char_limit = self.model_limits.get("max_output", 65536)
        
        # Extract detailed style profile
        style_profile = self._extract_style_profile(user_instructions)
        
        # Build additional requirements section if present
        additional_requirements = ""
        if 'sacred_additions' in style_profile:
            additional_requirements = f"\n🚨 **ADDITIONAL SACRED REQUIREMENTS:**\n{style_profile['sacred_additions']}\n"
        
        prompt = f"""🔥🔥🔥 HOLY USER INSTRUCTIONS - ABSOLUTE SUPREME PRIORITY 🔥🔥🔥

**THESE USER INSTRUCTIONS ARE SACRED AND MUST BE FOLLOWED ABSOLUTELY:**

🎯 **NARRATIVE VOICE (MANDATORY):**
{style_profile['narrative_voice']}

🎭 **TONE REQUIREMENTS (NON-NEGOTIABLE):**
{style_profile['tone_requirements']}

✍️ **WRITING STYLE DNA (CRITICAL):**
{style_profile['writing_style_dna']}

📋 **STRUCTURAL REQUIREMENTS (SACRED):**
{style_profile['structural_requirements']}
{additional_requirements}
🔥 **USER-DEFINED SCRIPT STRUCTURE (HOLY BLUEPRINT):**
{script_structure if script_structure else 'Create appropriate structure based on content'}
{time_conversion_note}

📋 **MASTER DOCUMENT SECTION ANALYSIS:**

🎬 **INTRO SECTION PLAN:**"""

        # Add intro requirements
        if section_reqs["intro_requirements"]:
            prompt += "\n- Requirements from user:\n"
            for req in section_reqs["intro_requirements"]:
                prompt += f"  ⚡ {req}\n"
        else:
            prompt += "\n- Requirements from user: Create engaging opening based on content\n"

        # Add literal content for intro
        intro_literals = [lit for lit in section_reqs["literal_content"] if any(word in lit.lower() for word in ["intro", "opening", "start", "begin", "hook"])]
        if intro_literals:
            prompt += "- Must include literal content:\n"
            for literal in intro_literals:
                prompt += f"""  🚨 "{literal}"\n"""

        prompt += f"""
📖 **MAIN CONTENT SECTIONS:**"""

        # Add content-specific requirements
        if section_reqs["content_specific"]:
            for req_num, req in section_reqs["content_specific"].items():
                prompt += f"\n- Section {req_num}: {req}"
        else:
            prompt += "\n- Develop main content based on transcript material"

        prompt += f"""

🎭 **OUTRO SECTION PLAN:**"""

        # Add outro requirements
        if section_reqs["outro_requirements"]:
            prompt += "\n- Requirements from user:\n"
            for req in section_reqs["outro_requirements"]:
                prompt += f"  ⚡ {req}\n"
        else:
            prompt += "\n- Requirements from user: Create satisfying conclusion based on content\n"

        # Add literal content for outro
        outro_literals = [lit for lit in section_reqs["literal_content"] if any(word in lit.lower() for word in ["outro", "conclusion", "ending", "close", "final"])]
        if outro_literals:
            prompt += "- Must include literal content:\n"
            for literal in outro_literals:
                prompt += f"""  🚨 "{literal}"\n"""

        # Add all literal content that doesn't fit intro/outro
        general_literals = [lit for lit in section_reqs["literal_content"]
                          if not any(word in lit.lower() for word in ["intro", "opening", "start", "begin", "hook", "outro", "conclusion", "ending", "close", "final"])]
        if general_literals:
            prompt += f"""

⚡ **LITERAL CONTENT TO INCLUDE THROUGHOUT:**"""
            for literal in general_literals:
                prompt += f"""
- "{literal}" (exact phrase required)"""

        prompt += f"""

═══════════════════════════════════════════════════════════════

# PROJECT SPECIFICATIONS (Secondary to user instructions above)

🎯 **PRIMARY TARGET - DURATION:**
The final transcript should be approximately **{get_conversion_config().chars_to_minutes(target_length):.0f} minutes** long when read aloud at normal speaking pace.

📊 **LENGTH SPECIFICATIONS:**
- Target Duration: more or less {get_conversion_config().chars_to_minutes(target_length):.0f} minutes of speech
- Target Length: approximately {target_length:,} characters
- Word Count: around {target_length // 5:,} words
- Model: {self.model} (can output roughly {model_char_limit:,} chars per response)
- Responses Planned: {response_plan['responses_needed']} response{"s" if response_plan['responses_needed'] > 1 else ""}

**YOU ARE A CONTENT STRUCTURE PLANNER - CREATE DETAILED OUTLINE THAT FOLLOWS THE HOLY USER INSTRUCTIONS ABOVE**

# SOURCE MATERIAL
[First 8000 chars of transcript for context]
{transcript_text[:8000]}{"..." if len(transcript_text) > 8000 else ""}

# REQUIRED OUTPUT FORMAT

## RESPONSE TITLES
"""
        
        # Generate meaningful response titles
        for i, plan in enumerate(response_plan["response_plan"]):
            prompt += f"""Response {plan['response_num']}: [Create meaningful title - NOT "Response {plan['response_num']}" but descriptive like "Crisis Preparedness Fundamentals"]""" + "\n"
        
        prompt += f"""
## MASTER OUTLINE

"""
        
        # Add response-specific sections with duration emphasis
        for i, plan in enumerate(response_plan["response_plan"]):
            start_char = sum(p['target_chars'] for p in response_plan["response_plan"][:i])
            end_char = start_char + plan['target_chars']
            
            # Calculate duration for this response
            response_minutes = get_conversion_config().chars_to_minutes(plan['target_chars'])
            response_words = plan['target_chars'] // 5
            
            prompt += f"""### Response {plan['response_num']}: [Response Title] 
**Duration:** approximately {response_minutes:.0f} minutes when read aloud
**Length:** more or less {plan['target_chars']:,} characters (around {response_words:,} words)
"""
            
            # Create 2-3 sections per response
            sections_count = 3 if plan['target_chars'] > 30000 else 2
            chars_per_section = plan['target_chars'] // sections_count
            
            for section_idx in range(sections_count):
                section_chars = chars_per_section
                if section_idx == sections_count - 1:
                    # Last section gets any remainder
                    section_chars = plan['target_chars'] - (chars_per_section * (sections_count - 1))
                
                section_minutes = get_conversion_config().chars_to_minutes(section_chars)
                section_words = section_chars // 5
                
                prompt += f"SECTION_{plan['response_num']}.{section_idx + 1} | Duration: roughly {section_minutes:.0f} minutes | Length: around {section_chars:,} chars (approximately {section_words:,} words) | [Brief topic description]\n"
        
        prompt += """

## DETAILED SECTION GUIDANCE
Provide 2-3 sentences for each section explaining:
- What specific topics/content should be covered
- What tone and approach to use
- What key points to emphasize
- What to avoid or de-emphasize

"""
        
        # Add detailed section guidance placeholders
        for i, plan in enumerate(response_plan["response_plan"]):
            sections_count = 3 if plan['target_chars'] > 30000 else 2
            for section_idx in range(sections_count):
                prompt += f"""SECTION_{plan['response_num']}.{section_idx + 1}: 
- Content Focus: [What topics should this section cover? Be specific about the main themes and points]
- Approach: [What tone, style, and approach should be used? How should the content be presented?]
- Key Elements: [What are the most important points to emphasize? What should readers/listeners take away?]

"""
        
        prompt += """## TRANSITION GUIDANCE
Explain how each section flows into the next:

"""
        
        # Add transition guidance
        for i, plan in enumerate(response_plan["response_plan"]):
            sections_count = 3 if plan['target_chars'] > 30000 else 2
            for section_idx in range(sections_count - 1):
                prompt += f"SECTION_{plan['response_num']}.{section_idx + 1} → SECTION_{plan['response_num']}.{section_idx + 2}: [How should this transition work?]\n"
            
            if i < len(response_plan["response_plan"]) - 1:
                prompt += f"Response {plan['response_num']} → Response {i + 2}: [How should the response transition work?]\n"
        
        prompt += """

# REQUIREMENTS:
1. Use rounded character counts (nearest 1,000) for clarity
2. Include both character and word estimates
3. Provide detailed section guidance (2-3 sentences each)
4. Create meaningful response titles
5. Give specific content direction based on user requirements
6. Consider the user's role, tone, and additional instructions
7. Make sections substantial enough to provide clear direction

Generate the DETAILED OUTLINE now with comprehensive guidance."""
        
        return prompt

    def _generate_content(
        self,
        transcript_text: str,
        master_document: str,
        response_plan: dict,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate content using response-aware approach with dynamic catch-up system."""

        generated_content = ""
        target_length = response_plan["total_target"]
        total_responses_planned = response_plan["responses_needed"]

        for response_info in response_plan["response_plan"]:
            response_num = response_info["response_num"]
            target_chars = response_info["target_chars"]
            is_final_response = (response_num == total_responses_planned)

            logger.info(f"🔄 Generating Response {response_num}/{total_responses_planned}")
            logger.info(f"   Target: {target_chars:,} characters")
            logger.info(f"   Progress: {len(generated_content):,}/{target_length:,} characters")
            if is_final_response:
                logger.info(f"   🎬 FINAL RESPONSE - Story conclusion required")

            # Build response-specific prompt
            generation_prompt = self._build_response_prompt(
                transcript_text, master_document, generated_content,
                response_num, response_plan, target_chars
            )

            # Check input window limits and trim if necessary
            generation_prompt = self._ensure_input_fits(generation_prompt)

            # Generate content for this response
            min_chars = int(target_chars * 0.85)
            max_chars = int(target_chars * 1.15)
            # Calculate tokens for this request
            tokens_requested = self._chars_to_tokens(target_chars)

            logger.info(f"🎯 EXPLICIT LENGTH REQUEST:")
            logger.info(f"   Target: {target_chars:,} characters")
            logger.info(f"   Acceptable range: {min_chars:,} - {max_chars:,} characters")
            logger.info(f"   Progress so far: {len(generated_content):,} characters")
            logger.info(f"   Tokens requested: {tokens_requested:,} tokens")
            try:
                new_content = process_llm(
                    context="Generate the content as specified in the system prompt.",
                    system_prompt=generation_prompt,
                    model=self.model,
                    max_tokens=self._chars_to_tokens(target_chars),
                    temperature=0.7
                )
            except Exception as e:
                if "overloaded" in str(e).lower():
                    logger.warning(f"⚠️ API overloaded, waiting 10 seconds and reducing request size...")
                    time.sleep(10)
                    # Reduce request size by half and try again
                    reduced_target = target_chars // 2
                    logger.info(f"🔄 Retrying with reduced size: {reduced_target:,} characters...")
                    new_content = process_llm(
                        context="Generate the content as specified in the system prompt.",
                        system_prompt=generation_prompt,
                        model=self.model,
                        max_tokens=self._chars_to_tokens(reduced_target),
                        temperature=0.7
                    )
                else:
                    raise e

            generated_content += new_content
            actual_chars = len(new_content)
            precision = actual_chars / target_chars
            min_chars = int(target_chars * 0.85)
            max_chars = int(target_chars * 1.15)

            # Check if within acceptable range
            in_range = min_chars <= actual_chars <= max_chars

            logger.info(f"✅ Response {response_num} complete:")
            logger.info(f"   Generated: {actual_chars:,} characters")
            logger.info(f"   Target: {target_chars:,} characters")
            logger.info(f"   Acceptable range: {min_chars:,} - {max_chars:,}")
            logger.info(f"   Precision: {precision:.2f}x ({'+' if precision > 1 else ''}{(precision-1)*100:.1f}%)")
            if in_range:
                logger.info(f"   ✅ TARGET HIT - Within acceptable range!")
            else:
                logger.warning(f"   ❌ TARGET MISSED - Outside acceptable range!")
                if actual_chars < min_chars:
                    logger.warning(f"   📉 TOO SHORT by {min_chars - actual_chars:,} characters")
                else:
                    logger.warning(f"   📈 TOO LONG by {actual_chars - max_chars:,} characters")

            # Save intermediate results
            if output_dir:
                response_path = os.path.join(output_dir, f"response_{response_num}.txt")
                with open(response_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"💾 Saved response {response_num} to {response_path}")

            # DYNAMIC CATCH-UP SYSTEM: Check if we need to add more content
            generated_content = self._handle_catch_up_if_needed(
                generated_content, target_chars, response_num, is_final_response,
                transcript_text, master_document, output_dir
            )

            # Add delay between responses
            if response_num < response_plan["responses_needed"]:
                logger.info(f"⏱️ Waiting 2 seconds before next response...")
                time.sleep(2)

        # Final summary
        final_precision = len(generated_content) / target_length
        logger.info(f"🎉 All responses complete!")
        logger.info(f"   Final length: {len(generated_content):,} characters")
        logger.info(f"   Target length: {target_length:,} characters")
        logger.info(f"   Overall precision: {final_precision:.2f}x ({'+' if final_precision > 1 else ''}{(final_precision-1)*100:.1f}%)")

        return generated_content
    
    def _generate_content_with_structure(
        self,
        transcript_text: str,
        master_document: str,
        structure: MasterDocumentStructure,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate content using structured approach with section tracking."""
        
        generated_content = ""
        boundary_manager = CharacterBoundaryManager(structure)
        
        logger.info(f"🏗️ Starting structured content generation:")
        logger.info(f"   Total sections: {len(structure.section_index)}")
        logger.info(f"   Target length: {structure.total_target_chars:,} chars")
        
        for response_section in structure.response_sections:
            response_num = response_section.response_num
            target_chars = response_section.total_target_chars
            is_final_response = (response_num == structure.total_responses_needed)
            
            logger.info(f"🔄 Generating Response {response_num}/{structure.total_responses_needed}: {response_section.title}")
            logger.info(f"   Target: {target_chars:,} characters")
            logger.info(f"   Sections: {[s.section_id for s in response_section.sections]}")
            
            # Update progress before generation
            progress = boundary_manager.update_progress(generated_content)
            logger.info(f"   Progress: {progress['total_chars']:,}/{structure.total_target_chars:,} chars ({progress['overall_percentage']:.1f}%)")
            
            # Build section-aware prompt
            generation_prompt = self._build_response_prompt_with_sections(
                transcript_text, master_document, generated_content,
                response_section, boundary_manager
            )
            
            # Check input window limits
            generation_prompt = self._ensure_input_fits(generation_prompt)
            
            # Generate content for this response
            min_chars = int(target_chars * 0.85)
            max_chars = int(target_chars * 1.15)
            tokens_requested = self._chars_to_tokens(target_chars)
            
            logger.info(f"🎯 Section-Aware Generation:")
            logger.info(f"   Target: {target_chars:,} characters")
            logger.info(f"   Acceptable range: {min_chars:,} - {max_chars:,} characters")
            logger.info(f"   Tokens requested: {tokens_requested:,} tokens")
            
            try:
                new_content = process_llm(
                    context="Generate the content with section awareness as specified.",
                    system_prompt=generation_prompt,
                    model=self.model,
                    max_tokens=self._chars_to_tokens(target_chars),
                    temperature=0.7
                )
            except Exception as e:
                if "overloaded" in str(e).lower():
                    logger.warning(f"⚠️ API overloaded, waiting and reducing request...")
                    time.sleep(10)
                    # Reduce request and try again
                    reduced_target = target_chars // 2
                    new_content = process_llm(
                        context="Generate the content with section awareness as specified.",
                        system_prompt=generation_prompt,
                        model=self.model,
                        max_tokens=self._chars_to_tokens(reduced_target),
                        temperature=0.7
                    )
                else:
                    raise e
                    
            generated_content += new_content
            actual_chars = len(new_content)
            precision = actual_chars / target_chars
            
            # Simple length control: too long -> shorten, too short -> extend
            min_acceptable_chars = int(target_chars * 0.85)  # 15% under is too short
            max_acceptable_chars = int(target_chars * 1.15)  # 15% over is too long
            
            if actual_chars > max_acceptable_chars:
                # TOO LONG: Direct shortening approach
                logger.warning(f"   📈 TOO LONG: {actual_chars:,} chars exceeds target ({target_chars:,})")
                reduction_percentage = int(((actual_chars - target_chars) / actual_chars) * 100)
                logger.info(f"   🔄 Shortening content by ~{reduction_percentage}%...")
                
                # Extract user instructions for shortening prompt
                user_instructions = self._extract_user_instructions()
                
                # Calculate flexible range for shortening
                min_target = int(target_chars * 0.85)  # 15% flexibility below
                max_target = int(target_chars * 1.15)  # 15% flexibility above
                
                # Improved collaborative shortening prompt 
                shorten_prompt = f"""🚨 **CRITICAL TTS OUTPUT INSTRUCTIONS - IMMEDIATE FAILURE IF ANY FORMATTING FOUND** 🚨

You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Any formatting violations will result in IMMEDIATE FAILURE.

**🚨 ABSOLUTE REQUIREMENTS - NON-NEGOTIABLE:**
- Output ONLY pure narrative text - no headers, sections, or formatting
- NEVER use bullet points (- like this) or numbered lists (1. like this) 
- NEVER use markdown headers (# ## ###) or any HTML/markdown formatting
- NEVER use **bold**, *italics*, or formatting markers of any kind
- Write as continuous flowing speech - not document structure
- Spell out ALL numbers as words: "3" → "three", "2025" → "two thousand twenty five"
- Convert ALL symbols to words: "%" → "percent", "&" → "and", "@" → "at"
- Expand abbreviations: "Dr." → "Doctor", "vs." → "versus", "etc." → "et cetera"
- NO stage directions: no *laughs*, [pause], (sighs), ::thinking::
- Keep sentences under 25 words for natural speech flow

**WRONG EXAMPLES:**
- "Here are the key steps: - Get inside - Stay low - Wait for help"
- "## Important Points" 
- "You need to: 1. Do this 2. Do that"
- "Follow these steps:"

**RIGHT EXAMPLES:**
- "Here are the key steps you need to follow. First, get inside the nearest building immediately. Next, stay low to avoid any debris. Finally, wait for official help to arrive."

🚨 **THIS IS SPEECH CONTENT, NOT DOCUMENT CONTENT** 🚨

🔥🔥🔥 **USER STYLE SANCTITY - ABSOLUTE HOLY REQUIREMENTS** 🔥🔥🔥

**THESE USER INSTRUCTIONS ARE SACRED - YOU MUST EMBODY THEM COMPLETELY:**

🎯 **MANDATORY NARRATIVE VOICE:**
{user_instructions['role']}

🎭 **NON-NEGOTIABLE TONE & STYLE:**
{user_instructions['tone_style']}

🚨 **SACRED ADDITIONAL REQUIREMENTS:**
{user_instructions['additional_instructions'] if user_instructions['additional_instructions'] else 'None specified'}

**⚡ EVERY WORD YOU WRITE MUST REFLECT THESE USER INSTRUCTIONS ⚡**

═══════════════════════════════════════════════════════════════

**YOUR COLLABORATIVE TASK: INTELLIGENT CONTENT CONDENSING**

Let's work together to create a more concise version of the following content. The goal is to capture all the essential meaning while making it more streamlined for speech.

📊 **CURRENT STATUS:**
- Current length: approximately {actual_chars:,} characters
- Current duration: more or less {get_conversion_config().chars_to_minutes(actual_chars):.0f} minutes when read aloud
- Current word count: around {actual_chars // 5:,} words

🎯 **DESIRED OUTPUT:**
- Target duration: approximately {get_conversion_config().chars_to_minutes(target_chars):.0f} minutes of speech
- Target length: more or less {target_chars:,} characters
- Target word count: around {target_chars // 5:,} words
- Reduction needed: roughly {reduction_percentage}% shorter

**ACCEPTABLE RANGE:** Between {min_target:,} and {max_target:,} characters

Your condensing approach should:
- Preserve the exact same writing style and narrative voice
- Maintain the same story flow and emotional tone  
- Keep all key points and main concepts intact
- Ensure natural speech patterns for TTS delivery
- Remove redundancy while preserving meaning
- Tighten explanations without losing clarity

Techniques that work well:
- Combine related sentences for smoother flow
- Remove transitional phrases where meaning stays clear
- Replace longer phrases with concise equivalents
- Eliminate unnecessary qualifiers and filler words
- Consolidate repetitive explanations

Content to condense:
{new_content}

Please create your condensed version that falls within the target range while maintaining all the essential elements:"""

                # Retry mechanism for shortening with original content
                original_content_to_shorten = new_content  # Store original for all retries
                shortened_success = False
                shortening_attempts = []  # Track all attempts for best selection
                
                for attempt in range(1, 4):  # Up to 3 attempts
                    try:
                        logger.info(f"   🔄 Shortening attempt {attempt}/3...")
                        
                        # Use original content for all attempts, not previous failures
                        attempt_prompt = shorten_prompt.replace("{new_content}", original_content_to_shorten)
                        
                        shortened_content = process_llm(
                            context=f"Shorten content to target length (attempt {attempt})",
                            system_prompt=attempt_prompt,
                            model=self.model,
                            max_tokens=self._chars_to_tokens(target_chars),
                            temperature=0.7
                        )
                        
                        shortened_chars = len(shortened_content)
                        
                        # Store this attempt for potential best selection
                        shortening_attempts.append({
                            'attempt': attempt,
                            'content': shortened_content,
                            'chars': shortened_chars,
                            'distance_from_target': abs(shortened_chars - target_chars)
                        })
                        
                        # Check if result is within acceptable range
                        if min_target <= shortened_chars <= max_target:
                            # Success! Use this result
                            generated_content = generated_content[:-len(new_content)] + shortened_content
                            new_content = shortened_content
                            actual_chars = shortened_chars
                            precision = actual_chars / target_chars
                            shortened_success = True
                            
                            logger.info(f"   ✅ Shortened successfully on attempt {attempt}: {actual_chars:,} characters")
                            break
                        else:
                            logger.warning(f"   📏 Attempt {attempt} result ({shortened_chars:,} chars) outside target range ({min_target:,}-{max_target:,})")
                            
                            # Widen range for next attempt if needed
                            if attempt < 3:
                                flexibility = 0.15 + (attempt * 0.05)  # 15%, 20%, 25%
                                min_target = int(target_chars * (1 - flexibility))
                                max_target = int(target_chars * (1 + flexibility))
                                logger.info(f"   🔄 Widening range for next attempt: {min_target:,}-{max_target:,}")
                        
                    except Exception as e:
                        logger.warning(f"   ⚠️ Shortening attempt {attempt} failed: {e}")
                
                if not shortened_success:
                    if shortening_attempts:
                        # Select the attempt closest to target
                        best_attempt = min(shortening_attempts, key=lambda x: x['distance_from_target'])
                        logger.info(f"   🎯 All attempts outside range, selecting best attempt {best_attempt['attempt']}: {best_attempt['chars']:,} chars")
                        logger.info(f"      Distance from target ({target_chars:,}): {best_attempt['distance_from_target']:,} chars")
                        
                        # Use the best attempt
                        generated_content = generated_content[:-len(new_content)] + best_attempt['content']
                        new_content = best_attempt['content']
                        actual_chars = best_attempt['chars']
                        precision = actual_chars / target_chars
                    else:
                        logger.warning(f"   ❌ All shortening attempts failed, keeping original: {len(new_content):,} chars")
            
            elif actual_chars < min_acceptable_chars:
                # TOO SHORT: Whole-content rewriting approach (no concatenation)
                expansion_percentage = int(((target_chars - actual_chars) / actual_chars) * 100)
                logger.warning(f"   📉 TOO SHORT: {actual_chars:,} chars below target ({target_chars:,})")
                logger.info(f"   🔄 Expanding content by ~{expansion_percentage}% through rewriting...")
                
                # Extract user instructions for expansion prompt
                user_instructions = self._extract_user_instructions()
                
                # Calculate flexible range for expansion
                min_target = int(target_chars * 0.85)  # 15% flexibility below
                max_target = int(target_chars * 1.15)  # 15% flexibility above
                
                # Improved collaborative expansion prompt
                expand_prompt = f"""🚨 **CRITICAL TTS OUTPUT INSTRUCTIONS - IMMEDIATE FAILURE IF ANY FORMATTING FOUND** 🚨

You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Any formatting violations will result in IMMEDIATE FAILURE.

**🚨 ABSOLUTE REQUIREMENTS - NON-NEGOTIABLE:**
- Output ONLY pure narrative text - no headers, sections, or formatting
- NEVER use bullet points (- like this) or numbered lists (1. like this) 
- NEVER use markdown headers (# ## ###) or any HTML/markdown formatting
- NEVER use **bold**, *italics*, or formatting markers of any kind
- Write as continuous flowing speech - not document structure
- Spell out ALL numbers as words: "3" → "three", "2025" → "two thousand twenty five"
- Convert ALL symbols to words: "%" → "percent", "&" → "and", "@" → "at"
- Expand abbreviations: "Dr." → "Doctor", "vs." → "versus", "etc." → "et cetera"
- NO stage directions: no *laughs*, [pause], (sighs), ::thinking::
- Keep sentences under 25 words for natural speech flow

**WRONG EXAMPLES:**
- "Here are the key steps: - Get inside - Stay low - Wait for help"
- "## Important Points" 
- "You need to: 1. Do this 2. Do that"
- "Follow these steps:"

**RIGHT EXAMPLES:**
- "Here are the key steps you need to follow. First, get inside the nearest building immediately. Next, stay low to avoid any debris. Finally, wait for official help to arrive."

🚨 **THIS IS SPEECH CONTENT, NOT DOCUMENT CONTENT** 🚨

🔥🔥🔥 **USER STYLE SANCTITY - ABSOLUTE HOLY REQUIREMENTS** 🔥🔥🔥

**THESE USER INSTRUCTIONS ARE SACRED - YOU MUST EMBODY THEM COMPLETELY:**

🎯 **MANDATORY NARRATIVE VOICE:**
{user_instructions['role']}

🎭 **NON-NEGOTIABLE TONE & STYLE:**
{user_instructions['tone_style']}

🚨 **SACRED ADDITIONAL REQUIREMENTS:**
{user_instructions['additional_instructions'] if user_instructions['additional_instructions'] else 'None specified'}

**⚡ EVERY WORD YOU WRITE MUST REFLECT THESE USER INSTRUCTIONS ⚡**

═══════════════════════════════════════════════════════════════

**YOUR CREATIVE TASK: NATURAL CONTENT ENRICHMENT**

Let's collaborate to develop this content into a fuller, more comprehensive version. We want to add depth and detail while maintaining the authentic voice and natural flow.

📊 **CURRENT STATUS:**
- Current length: approximately {actual_chars:,} characters
- Current duration: more or less {get_conversion_config().chars_to_minutes(actual_chars):.0f} minutes when read aloud
- Current word count: around {actual_chars // 5:,} words

🎯 **DESIRED OUTPUT:**
- Target duration: approximately {get_conversion_config().chars_to_minutes(target_chars):.0f} minutes of speech
- Target length: more or less {target_chars:,} characters  
- Target word count: around {target_chars // 5:,} words
- Expansion needed: roughly {expansion_percentage}% increase in content

**ACCEPTABLE RANGE:** Between {min_target:,} and {max_target:,} characters

Your enrichment approach should:
- Maintain the exact same writing style and narrative voice
- Preserve the original story flow and emotional tone  
- Keep the same topic focus and all existing key points
- Ensure natural speech patterns remain smooth and engaging
- Add value through meaningful content, not just padding

Effective expansion techniques:
- Develop existing points with relevant examples or anecdotes
- Add natural transitions that enhance flow between ideas
- Include descriptive elements that paint clearer mental pictures
- Provide additional context that deepens understanding
- Expand on implications and connections between concepts
- Add supporting details that make abstract ideas more concrete

Content to enrich and develop:
{new_content}

Please create your enriched version that falls within the target range while preserving the authentic voice and adding genuine value:"""

                # Retry mechanism for expansion with original content
                original_content_to_expand = new_content  # Store original for all retries
                expansion_success = False
                expansion_attempts = []  # Track all attempts for best selection
                
                for attempt in range(1, 4):  # Up to 3 attempts
                    try:
                        logger.info(f"   🔄 Expansion attempt {attempt}/3...")
                        
                        # Use original content for all attempts, not previous failures
                        attempt_prompt = expand_prompt.replace("{new_content}", original_content_to_expand)
                        
                        expanded_content = process_llm(
                            context=f"Expand content to target length (attempt {attempt})",
                            system_prompt=attempt_prompt,
                            model=self.model,
                            max_tokens=self._chars_to_tokens(int(target_chars * 1.2)),  # Give some buffer
                            temperature=0.7
                        )
                        
                        expanded_chars = len(expanded_content)
                        
                        # Store this attempt for potential best selection
                        expansion_attempts.append({
                            'attempt': attempt,
                            'content': expanded_content,
                            'chars': expanded_chars,
                            'distance_from_target': abs(expanded_chars - target_chars)
                        })
                        
                        # Check if result is within acceptable range
                        if min_target <= expanded_chars <= max_target:
                            # Success! Use this result
                            generated_content = generated_content[:-len(new_content)] + expanded_content
                            new_content = expanded_content
                            actual_chars = expanded_chars
                            precision = actual_chars / target_chars
                            expansion_success = True
                            
                            logger.info(f"   ✅ Expanded successfully on attempt {attempt}: {actual_chars:,} characters")
                            break
                        else:
                            logger.warning(f"   📏 Attempt {attempt} result ({expanded_chars:,} chars) outside target range ({min_target:,}-{max_target:,})")
                            
                            # Widen range for next attempt if needed
                            if attempt < 3:
                                flexibility = 0.15 + (attempt * 0.05)  # 15%, 20%, 25%
                                min_target = int(target_chars * (1 - flexibility))
                                max_target = int(target_chars * (1 + flexibility))
                                logger.info(f"   🔄 Widening range for next attempt: {min_target:,}-{max_target:,}")
                        
                    except Exception as e:
                        logger.warning(f"   ⚠️ Expansion attempt {attempt} failed: {e}")
                
                if not expansion_success:
                    if expansion_attempts:
                        # Select the attempt closest to target
                        best_attempt = min(expansion_attempts, key=lambda x: x['distance_from_target'])
                        logger.info(f"   🎯 All attempts outside range, selecting best attempt {best_attempt['attempt']}: {best_attempt['chars']:,} chars")
                        logger.info(f"      Distance from target ({target_chars:,}): {best_attempt['distance_from_target']:,} chars")
                        
                        # Use the best attempt
                        generated_content = generated_content[:-len(new_content)] + best_attempt['content']
                        new_content = best_attempt['content']
                        actual_chars = best_attempt['chars']
                        precision = actual_chars / target_chars
                    else:
                        logger.warning(f"   ❌ All expansion attempts failed, keeping original: {len(new_content):,} chars")
            
            else:
                logger.info(f"   ✅ Length acceptable: {actual_chars:,} characters (within range)")
                precision = actual_chars / target_chars
            
            # Update response section status
            response_section.actual_chars_generated = actual_chars
            response_section.completion_status = "completed"
            
            logger.info(f"✅ Response {response_num} complete:")
            logger.info(f"   Generated: {actual_chars:,} characters")
            logger.info(f"   Target: {target_chars:,} characters")
            logger.info(f"   Precision: {precision:.2f}x ({'+' if precision > 1 else ''}{(precision-1)*100:.1f}%)")
            
            # Update progress after generation
            progress = boundary_manager.update_progress(generated_content)
            if progress['current_section']:
                current_section = structure.get_section_by_id(progress['current_section'])
                logger.info(f"   Current section: {current_section.section_id} - {current_section.title}")
            
            # Save intermediate results with section tracking and meaningful names
            if output_dir:
                # Create filename from title without response prefix
                safe_title = "".join(c for c in response_section.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title.replace(' ', '_').lower()[:50]  # Limit length
                
                response_path = os.path.join(output_dir, f"{safe_title}.txt")
                with open(response_path, "w", encoding="utf-8") as f:
                    f.write(new_content)  # Save pure content without markdown headers
                
                # Save progress report
                progress_path = os.path.join(output_dir, f"progress_after_response_{response_num}.json")
                progress_with_title = {**progress, "response_title": response_section.title}
                with open(progress_path, "w", encoding="utf-8") as f:
                    json.dump(progress_with_title, f, indent=2)
                    
                logger.info(f"💾 Saved '{response_section.title}' and progress to {output_dir}")
                
            # Simple length control already handled above - no complex catch-up needed
            
            # Brief pause between responses
            if response_num < structure.total_responses_needed:
                time.sleep(2)
        
        # Final summary with section completion
        final_progress = boundary_manager.update_progress(generated_content)
        final_precision = len(generated_content) / structure.total_target_chars
        
        logger.info(f"🎉 Structured generation complete!")
        logger.info(f"   Final length: {len(generated_content):,} characters")
        logger.info(f"   Target length: {structure.total_target_chars:,} characters")
        logger.info(f"   Overall precision: {final_precision:.2f}x ({'+' if final_precision > 1 else ''}{(final_precision-1)*100:.1f}%)")
        logger.info(f"   Sections completed: {len(final_progress['sections_completed'])}")
        logger.info(f"   Sections in progress: {len(final_progress['sections_in_progress'])}")
        
        return generated_content
    
    def _build_response_prompt_with_sections(
        self,
        transcript_text: str,
        master_document: str,
        previous_content: str,
        response_section: ResponseSection,
        boundary_manager: CharacterBoundaryManager
    ) -> str:
        """Build response prompt with section awareness."""

        user_instructions = self._extract_user_instructions()
        response_num = response_section.response_num
        target_chars = response_section.total_target_chars
        is_final_response = response_section.response_num == len(boundary_manager.structure.response_sections)

        # Parse section-specific requirements and format for prompt
        section_reqs = self._parse_section_specific_requirements(user_instructions)
        section_requirements = self._format_section_requirements_for_prompt(
            section_reqs, "section-aware", response_num, is_final_response
        )
        
        # Get current section context
        current_chars = len(previous_content)
        current_section = boundary_manager.structure.get_current_section(current_chars)
        
        # Build section context
        section_context = ""
        for section in response_section.sections:
            section_context += f"SECTION {section.section_id}: {section.title} ({section.start_char:,}-{section.end_char:,} chars)\n"
            section_context += f"  Type: {section.content_type}\n"
            if section.key_points:
                section_context += f"  Key Points: {', '.join(section.key_points)}\n"
            if section.user_instructions:
                section_context += f"  Instructions: {section.user_instructions}\n"
        
        prompt = f"""{section_requirements}

# RESPONSE {response_num} GENERATION - SECTION-AWARE

🚨 **CRITICAL TTS OUTPUT INSTRUCTIONS - IMMEDIATE DISQUALIFICATION IF VIOLATED** 🚨

You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Any formatting violations will result in IMMEDIATE FAILURE.

**🚨 ABSOLUTE REQUIREMENTS - NON-NEGOTIABLE:**
- Output ONLY pure narrative text - no headers, sections, or formatting
- NEVER use bullet points (- like this) or numbered lists (1. like this)
- NEVER use markdown headers (# ## ###) or any HTML/markdown formatting
- NEVER use **bold**, *italics*, or formatting markers of any kind
- Write as continuous flowing speech - not document structure
- Spell out ALL numbers as words: "3" → "three", "2025" → "two thousand twenty five"
- Convert ALL symbols to words: "%" → "percent", "&" → "and", "@" → "at"
- Expand abbreviations: "Dr." → "Doctor", "vs." → "versus", "etc." → "et cetera"
- NO stage directions: no *laughs*, [pause], (sighs), ::thinking::
- Keep sentences under 25 words for natural speech flow

**WRONG:** "Here are the key steps: - Get inside - Stay low - Wait for help"
**RIGHT:** "Here are the key steps. First, get inside the nearest building immediately. Next, stay low to avoid any debris. Finally, wait for official help to arrive."

🚨 **THIS IS SPEECH CONTENT, NOT DOCUMENT CONTENT** 🚨

🔥🔥🔥 **USER STYLE SANCTITY - ABSOLUTE HOLY REQUIREMENTS** 🔥🔥🔥

**THESE USER INSTRUCTIONS ARE SACRED - YOU MUST EMBODY THEM COMPLETELY:**

🎯 **MANDATORY NARRATIVE VOICE:**
{user_instructions['role']}

🎭 **NON-NEGOTIABLE TONE & STYLE:**
{user_instructions['tone_style']}

🚨 **SACRED ADDITIONAL REQUIREMENTS:**
{user_instructions['additional_instructions'] if user_instructions['additional_instructions'] else 'None specified'}

**⚡ EVERY WORD YOU WRITE MUST REFLECT THESE USER INSTRUCTIONS ⚡**

═══════════════════════════════════════════════════════════════

## SECTION CONTEXT
You are generating Response {response_num} which covers these sections:

{section_context}

## PROGRESS STATUS
- Current Response: {response_num}/{len(boundary_manager.structure.response_sections)}
- Target This Response: {target_chars:,} characters
- Generated So Far: {len(previous_content):,} characters
- Overall Target: {boundary_manager.structure.total_target_chars:,} characters
- Current Position: Character {current_chars:,}

## CURRENT SECTION
"""
        
        if current_section:
            section_ctx = boundary_manager.get_section_context(current_section.section_id, current_chars)
            prompt += f"""You are currently in: {section_ctx['title']} (ID: {section_ctx['section_id']})
- Section Type: {section_ctx['content_type']}
- Section Progress: {section_ctx['chars_generated']:,} / {section_ctx['target_chars']:,} chars ({section_ctx['percentage_complete']:.1f}%)
- Remaining in Section: {section_ctx['chars_remaining']:,} characters
"""
            if section_ctx['key_points']:
                prompt += f"- Key Points to Cover: {', '.join(section_ctx['key_points'])}\n"
        
        prompt += f"""
## MASTER DOCUMENT STRUCTURE
{master_document[:2000]}{"..." if len(master_document) > 2000 else ""}

## USER INSTRUCTIONS (MAINTAIN THROUGHOUT)
**Role:** {user_instructions['role']}
**Tone & Style:** {user_instructions['tone_style'] or "Professional, engaging narrative style"}
**Additional:** {user_instructions['additional_instructions'] or "None specified"}

## CONTEXT
{"This is the FIRST response - begin the narrative" if response_num == 1 else f"Previous content (last 2000 chars): ...{previous_content[-2000:]}"}

🔄 **CRITICAL ANTI-REPETITION GUIDANCE:**
- This is Response {response_num} - part of a COMPLETE STORY with seamless flow
- Review previous content to avoid repetition of concepts, quotes, or ideas
- If something was already covered, BUILD UPON IT rather than repeating it
- Each response should ADD NEW VALUE and ADVANCE THE NARRATIVE
- Only repeat content if user explicitly requests repetition or emphasis

## YOUR TASK
Generate Response {response_num} content following the section structure above.

🚨 **REMINDER: FOLLOW TTS INSTRUCTIONS ABOVE - NO FORMATTING, PURE NARRATIVE SPEECH** 🚨

**🎯 LENGTH REQUIREMENT (CRITICAL - NON-NEGOTIABLE):**

🚨 **ABSOLUTE MINIMUM: {target_chars:,} CHARACTERS** 🚨
🚨 **YOU MUST OUTPUT AT LEAST {target_chars:,} CHARACTERS** 🚨

- **TARGET: {target_chars:,} characters**
- **MINIMUM REQUIRED: {target_chars:,} characters (NOT NEGOTIABLE)**
- **PREFERRED RANGE: {target_chars:,} to {int(target_chars * 1.15):,} characters**
- **MAXIMUM ACCEPTABLE: {int(target_chars * 1.2):,} characters**

**SECTION REQUIREMENTS:**
- Cover all sections listed above in the specified character ranges
- Maintain section boundaries and transitions
- {"Complete the narrative - this is the final response" if is_final_response else "Prepare content for continuation in the next response"}
- Follow TTS formatting rules above

**🚨 GENERATE RESPONSE {response_num} NOW - MINIMUM {target_chars:,} CHARACTERS REQUIRED** 🚨

🚨 **FINAL REMINDER: NO BULLET POINTS, NO HEADERS, NO FORMATTING - PURE SPEECH NARRATIVE ONLY** 🚨
"""
        
        return prompt
    
    def _build_shortened_response_prompt(
        self,
        transcript_text: str,
        master_document: str,
        previous_content: str,
        response_section: ResponseSection,
        boundary_manager: CharacterBoundaryManager,
        reduction_percentage: int
    ) -> str:
        """Build a prompt specifically for generating shorter content."""

        user_instructions = self._extract_user_instructions()
        response_num = response_section.response_num
        target_chars = response_section.total_target_chars
        is_final_response = response_section.response_num == len(boundary_manager.structure.response_sections)

        # Parse section-specific requirements and format for prompt
        section_reqs = self._parse_section_specific_requirements(user_instructions)
        section_requirements = self._format_section_requirements_for_prompt(
            section_reqs, "shortening", response_num, is_final_response
        )
        
        # Get current section context
        current_chars = len(previous_content)
        current_section = boundary_manager.structure.get_current_section(current_chars)
        
        prompt = f"""{section_requirements}

# SHORTENED RESPONSE {response_num} GENERATION - OVERFLOW CORRECTION

## CRITICAL SITUATION
The previous generation was TOO LONG and exceeded acceptable limits.
You must generate content that is approximately {reduction_percentage}% SHORTER than typical.

## SHORTENED LENGTH REQUIREMENT
🚨 **GENERATE APPROXIMATELY {target_chars:,} CHARACTERS (NOT MORE)** 🚨
🚨 **BE CONCISE - PREVIOUS ATTEMPT WAS TOO VERBOSE** 🚨

- **Target: {target_chars:,} characters (STRICT LIMIT)**
- **Maximum: {int(target_chars * 1.1):,} characters**
- **Approach: More concise, less verbose, tighter writing**

## SECTION CONTEXT
You are generating: {response_section.title}

Sections to cover:
"""
        
        for section in response_section.sections:
            prompt += f"- {section.section_id}: {section.title} (~{section.target_chars:,} chars)\n"
        
        prompt += f"""
## SHORTENING STRATEGY
To achieve the required length reduction:
1. **Be more concise** - eliminate unnecessary words and phrases
2. **Focus on essentials** - prioritize key points over detailed explanations
3. **Reduce examples** - fewer but more impactful illustrations
4. **Tighten transitions** - shorter bridges between concepts
5. **Streamline descriptions** - more direct, less elaborate language
6. **Avoid repetition** - don't repeat concepts already covered in previous content
7. **Build cohesively** - ensure this shortened content flows naturally with the overall story

## USER REQUIREMENTS (MAINTAIN)
Role: {user_instructions['role']}
Tone: {user_instructions['tone_style']}

## MASTER DOCUMENT GUIDANCE
{master_document[:1500]}{"..." if len(master_document) > 1500 else ""}

## PREVIOUS CONTENT
{previous_content[-2000:] if len(previous_content) > 2000 else previous_content}

## TTS FORMATTING (STILL REQUIRED)
- Output ONLY spoken words, no stage directions
- Spell out numbers as words
- Convert symbols to words
- No markdown or formatting

## YOUR TASK
Generate the {response_section.title} content with approximately {reduction_percentage}% LESS text than usual.

🚨 **CRITICAL: GENERATE ~{target_chars:,} CHARACTERS - BE CONCISE AND FOCUSED** 🚨

Focus on quality over quantity. Make every word count.
"""
        
        return prompt
    
    def _handle_catch_up_with_sections(
        self,
        generated_content: str,
        target_chars: int,
        response_section: ResponseSection,
        boundary_manager: CharacterBoundaryManager,
        is_final_response: bool,
        output_dir: Optional[str] = None
    ) -> str:
        """Handle catch-up with section awareness."""
        
        # Get actual chars from this response
        previous_length = len(generated_content) - len(generated_content.split('\n\n')[-1])  
        if previous_length > 0:
            last_response_content = generated_content[previous_length:]
        else:
            last_response_content = generated_content
            
        actual_chars = len(last_response_content)
        min_chars = int(target_chars * 0.85)
        
        if actual_chars >= min_chars:
            logger.info(f"   ✅ No section-aware catch-up needed")
            return generated_content
        
        # Calculate deficit
        deficit = min_chars - actual_chars
        logger.warning(f"   📉 SECTION-AWARE DEFICIT: {deficit:,} characters short")
        
        # Determine current section for catch-up
        current_chars = len(generated_content)
        current_section = boundary_manager.structure.get_current_section(current_chars)
        
        if current_section:
            section_ctx = boundary_manager.get_section_context(current_section.section_id, current_chars)
            logger.info(f"   🎯 Catch-up in section: {section_ctx['title']} (ID: {section_ctx['section_id']})")
            
            # Generate section-aware catch-up
            catch_up_content = self._generate_section_aware_catch_up(
                generated_content, deficit, current_section, section_ctx, is_final_response
            )
            
            final_content = generated_content + catch_up_content
            logger.info(f"   📊 Section-aware catch-up complete: {len(catch_up_content):,} chars added")
            
            # Save catch-up details if output directory provided
            if output_dir:
                catch_up_path = os.path.join(output_dir, f"catchup_response_{response_section.response_num}_section_{current_section.section_id}.txt")
                with open(catch_up_path, "w", encoding="utf-8") as f:
                    f.write(catch_up_content)
                logger.info(f"   💾 Saved section-aware catch-up to {catch_up_path}")
            
            return final_content
        else:
            logger.warning(f"   ⚠️ No current section found for catch-up")
            return generated_content
    
    def _generate_section_aware_catch_up(
        self,
        generated_content: str,
        deficit: int,
        current_section: SectionBoundary,
        section_ctx: Dict[str, Any],
        is_final_response: bool
    ) -> str:
        """Generate catch-up content that's aware of the current section."""
        
        user_instructions = self._extract_user_instructions()
        recent_content = generated_content[-1000:] if len(generated_content) > 1000 else generated_content
        
        prompt = f"""# SECTION-AWARE CATCH-UP GENERATION

🚨 **CRITICAL TTS OUTPUT INSTRUCTIONS - IMMEDIATE DISQUALIFICATION IF VIOLATED** 🚨

You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Any formatting violations will result in IMMEDIATE FAILURE.

**🚨 ABSOLUTE REQUIREMENTS - NON-NEGOTIABLE:**
- Output ONLY pure narrative text - no headers, sections, or formatting
- NEVER use bullet points (- like this) or numbered lists (1. like this)
- NEVER use markdown headers (# ## ###) or any HTML/markdown formatting
- NEVER use **bold**, *italics*, or formatting markers of any kind
- Write as continuous flowing speech - not document structure
- Spell out ALL numbers as words: "3" → "three", "2025" → "two thousand twenty five"
- Convert ALL symbols to words: "%" → "percent", "&" → "and", "@" → "at"
- Expand abbreviations: "Dr." → "Doctor", "vs." → "versus", "etc." → "et cetera"
- NO stage directions: no *laughs*, [pause], (sighs), ::thinking::
- Keep sentences under 25 words for natural speech flow

🚨 **THIS IS SPEECH CONTENT, NOT DOCUMENT CONTENT** 🚨

## SECTION CONTEXT
- Current Section: {current_section.title} (ID: {current_section.section_id})
- Section Type: {current_section.content_type}
- Section Range: {current_section.start_char:,} to {current_section.end_char:,} characters
- Section Progress: {section_ctx['chars_generated']:,} / {section_ctx['target_chars']:,} characters ({section_ctx['percentage_complete']:.1f}%)
- Remaining in Section: {section_ctx['chars_remaining']:,} characters

## SECTION REQUIREMENTS
- Key Points: {', '.join(current_section.key_points) if current_section.key_points else 'Continue current topic'}
- User Instructions: {current_section.user_instructions or 'Follow general tone and style'}
- Content Type: {current_section.content_type}

## YOUR ROLE
{user_instructions['role']}

## RECENT CONTENT (for seamless continuation)
{recent_content}

## YOUR TASK - SECTION-AWARE CATCH-UP
Continue the content within the {current_section.title} section.

**🎯 LENGTH REQUIREMENT (CRITICAL):**
🚨 **ABSOLUTE MINIMUM: {deficit:,} CHARACTERS** 🚨
🚨 **YOU MUST OUTPUT AT LEAST {deficit:,} CHARACTERS** 🚨

**CRITICAL SECTION-AWARE RULES:**
1. **STAY IN SECTION** - You are extending the {current_section.title} section only
2. **CONTINUE SEAMLESSLY** - Pick up exactly where the previous content ended
3. **MAINTAIN SECTION FOCUS** - Stay on topic for this section: {current_section.content_type}
4. **SECTION BOUNDARIES** - {"This is NOT the final section - avoid concluding" if not is_final_response else "You may conclude if this naturally completes the section"}
5. **NO REPETITION** - Don't repeat what was already covered
6. **NATURAL FLOW** - Content should feel like a natural continuation

🚨 **GENERATE {deficit:,} CHARACTERS OF SECTION-AWARE CATCH-UP NOW** 🚨
"""
        
        try:
            catch_up_content = process_llm(
                context="Generate section-aware catch-up content as specified.",
                system_prompt=prompt,
                model=self.model,
                max_tokens=self._chars_to_tokens(deficit),
                temperature=0.7
            )
            
            return catch_up_content
            
        except Exception as e:
            logger.error(f"Section-aware catch-up failed: {e}")
            return ""

    def _handle_catch_up_if_needed(
        self,
        generated_content: str,
        target_chars: int,
        response_num: int,
        is_final_response: bool,
        transcript_text: str,
        master_document: str,
        output_dir: Optional[str] = None
    ) -> str:
        """Handle dynamic catch-up system after each response."""

        # Get the content from the last response
        last_response_start = len(generated_content) - len(generated_content.split('\n\n')[-1])
        last_response_content = generated_content[last_response_start:]
        actual_chars = len(last_response_content)

        # Calculate acceptable range
        min_chars = int(target_chars * 0.85)
        max_chars = int(target_chars * 1.15)

        # Check if within acceptable range
        if min_chars <= actual_chars <= max_chars:
            logger.info(f"   ✅ No catch-up needed - within acceptable range")
            return generated_content

        # Calculate deficit/excess
        if actual_chars < min_chars:
            deficit = min_chars - actual_chars
            logger.warning(f"   📉 DEFICIT DETECTED: {deficit:,} characters short")

            # Special handling for final response
            if is_final_response:
                logger.info(f"   🎬 Final response - checking if deficit is manageable")
                if deficit <= target_chars * 0.3:  # If deficit is < 30% of target
                    logger.info(f"   ✅ Small deficit ({deficit:,} chars) - letting final response handle it")
                    return generated_content
                else:
                    logger.warning(f"   ⚠️ Large deficit ({deficit:,} chars) - need catch-up before finale")

            # Generate catch-up content
            return self._generate_catch_up_content(
                generated_content, deficit, response_num, is_final_response, output_dir
            )

        elif actual_chars > max_chars:
            excess = actual_chars - max_chars
            logger.warning(f"   📈 EXCESS DETECTED: {excess:,} characters over target")
            logger.info(f"   ℹ️ Excess content will be kept (better too much than too little)")
            return generated_content

        return generated_content

    def _generate_catch_up_content(
        self,
        generated_content: str,
        deficit: int,
        response_num: int,
        is_final_response: bool,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate catch-up content to fill deficit."""

        catch_up_id = f"{response_num}A"
        logger.info(f"🔄 Generating Catch-up {catch_up_id}")
        logger.info(f"   Target: {deficit:,} characters (filling deficit)")

        # Build catch-up prompt
        catch_up_prompt = self._build_catch_up_prompt(generated_content, deficit, is_final_response)

        # Ensure prompt fits input window
        catch_up_prompt = self._ensure_input_fits(catch_up_prompt)

        # Generate catch-up content
        try:
            catch_up_content = process_llm(
                context="Generate the catch-up content as specified in the system prompt.",
                system_prompt=catch_up_prompt,
                model=self.model,
                max_tokens=self._chars_to_tokens(deficit),
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"❌ Catch-up generation failed: {e}")
            logger.info(f"   Continuing without catch-up...")
            return generated_content

        # Log catch-up results
        catch_up_chars = len(catch_up_content)
        catch_up_precision = catch_up_chars / deficit

        logger.info(f"✅ Catch-up {catch_up_id} complete:")
        logger.info(f"   Generated: {catch_up_chars:,} characters")
        logger.info(f"   Target: {deficit:,} characters")
        logger.info(f"   Precision: {catch_up_precision:.2f}x ({'+' if catch_up_precision > 1 else ''}{(catch_up_precision-1)*100:.1f}%)")

        # Save catch-up content
        if output_dir:
            catch_up_path = os.path.join(output_dir, f"response_{catch_up_id}.txt")
            with open(catch_up_path, "w", encoding="utf-8") as f:
                f.write(catch_up_content)
            logger.info(f"💾 Saved catch-up {catch_up_id} to {catch_up_path}")

        # Combine content
        combined_content = generated_content + catch_up_content
        logger.info(f"   📊 Total after catch-up: {len(combined_content):,} characters")

        return combined_content

    def _build_catch_up_prompt(
        self,
        generated_content: str,
        deficit: int,
        is_final_response: bool
    ) -> str:
        """Build prompt for catch-up content generation."""

        # Get user instructions
        user_instructions = self._extract_user_instructions()

        # Parse section-specific requirements and format for prompt
        section_reqs = self._parse_section_specific_requirements(user_instructions)
        # For catch-up, we don't know exact response number, so use general approach
        section_requirements = self._format_section_requirements_for_prompt(
            section_reqs, "catch-up", 1, is_final_response
        )

        # Get context from recent content (last 3000 characters)
        context_chars = min(3000, len(generated_content))
        recent_content = generated_content[-context_chars:] if context_chars > 0 else ""

        # Calculate acceptable range for catch-up
        min_chars = int(deficit * 0.85)
        max_chars = int(deficit * 1.15)

        prompt = f"""{section_requirements}

# CATCH-UP CONTENT GENERATION

🚨 **CRITICAL TTS OUTPUT INSTRUCTIONS - IMMEDIATE DISQUALIFICATION IF VIOLATED** 🚨

You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Any formatting violations will result in IMMEDIATE FAILURE.

**🚨 ABSOLUTE REQUIREMENTS - NON-NEGOTIABLE:**
- Output ONLY pure narrative text - no headers, sections, or formatting
- NEVER use bullet points (- like this) or numbered lists (1. like this)
- NEVER use markdown headers (# ## ###) or any HTML/markdown formatting
- NEVER use **bold**, *italics*, or formatting markers of any kind
- Write as continuous flowing speech - not document structure
- Spell out ALL numbers as words: "3" → "three", "2025" → "two thousand twenty five"
- Convert ALL symbols to words: "%" → "percent", "&" → "and", "@" → "at"
- Expand abbreviations: "Dr." → "Doctor", "vs." → "versus", "etc." → "et cetera"
- NO stage directions: no *laughs*, [pause], (sighs), ::thinking::
- Keep sentences under 25 words for natural speech flow

🚨 **THIS IS SPEECH CONTENT, NOT DOCUMENT CONTENT** 🚨

## YOUR ROLE
{user_instructions['role']}

## RECENT CONTENT (for context)
{recent_content}

## YOUR TASK - CATCH-UP EXTENSION
You need to CONTINUE the story/content seamlessly from where it left off.

**🎯 LENGTH REQUIREMENT (CRITICAL - NON-NEGOTIABLE):**

🚨 **ABSOLUTE MINIMUM: {deficit:,} CHARACTERS** 🚨
🚨 **YOU MUST OUTPUT AT LEAST {deficit:,} CHARACTERS** 🚨
🚨 **ANYTHING UNDER {deficit:,} CHARACTERS IS COMPLETELY UNACCEPTABLE** 🚨

- **TARGET: {deficit:,} characters**
- **MINIMUM REQUIRED: {deficit:,} characters (NOT NEGOTIABLE)**
- **PREFERRED RANGE: {deficit:,} to {max_chars:,} characters**
- **MAXIMUM ACCEPTABLE: {int(deficit * 1.2):,} characters**

🔥 **CRITICAL CATCH-UP INSTRUCTIONS:** 🔥
- Your catch-up response MUST be AT LEAST {deficit:,} characters long
- This is filling a deficit - you CANNOT write less than {deficit:,} characters
- Count characters as you write - this is MANDATORY

**CRITICAL CATCH-UP RULES:**
1. **CONTINUE SEAMLESSLY** - Pick up exactly where the previous content ended
2. **MAINTAIN TONE & STYLE** - Follow user's specified style: {user_instructions.get('tone_style', 'Professional, engaging')}
3. **ADD SUBSTANTIAL CONTENT** - This is not filler, add meaningful content
4. **DO NOT CONCLUDE** - {"This is NOT the ending - leave room for proper conclusion" if not is_final_response else "You may conclude if this completes the story naturally"}
5. **NO REPETITION** - Don't repeat concepts, quotes, or ideas already covered
6. **BUILD UPON PREVIOUS** - Expand on existing content rather than rehashing it
7. **NATURAL FLOW** - Content should feel like a natural continuation

**🔍 MANDATORY CATCH-UP VERIFICATION:**
1. Count the EXACT number of characters in your catch-up response
2. Is it AT LEAST {deficit:,} characters? If NO, ADD MORE CONTENT IMMEDIATELY
3. Is it between {deficit:,} and {int(deficit * 1.2):,} characters? If NO, adjust
4. Does it continue seamlessly from previous content? If NO, fix the transition
5. If you submit less than {deficit:,} characters, the catch-up has FAILED

🚨 **REMEMBER: {deficit:,} CHARACTERS IS THE ABSOLUTE MINIMUM FOR THIS CATCH-UP** 🚨

🚨 **GENERATE CATCH-UP CONTENT NOW - MINIMUM {deficit:,} CHARACTERS REQUIRED** 🚨

**FINAL REMINDER: Your catch-up must be AT LEAST {deficit:,} characters. Anything less means the catch-up failed.**
"""

        return prompt

    def _build_response_prompt(
        self,
        transcript_text: str,
        master_document: str,
        previous_content: str,
        response_num: int,
        response_plan: dict,
        target_chars: int
    ) -> str:
        """Build prompt for specific response generation."""

        user_instructions = self._extract_user_instructions()
        is_final_response = response_num == response_plan["responses_needed"]

        # Parse section-specific requirements and format for prompt
        section_reqs = self._parse_section_specific_requirements(user_instructions)
        section_requirements = self._format_section_requirements_for_prompt(
            section_reqs, "general", response_num, is_final_response
        )

        prompt = f"""{section_requirements}

🚨 **CRITICAL TTS OUTPUT INSTRUCTIONS - IMMEDIATE DISQUALIFICATION IF VIOLATED** 🚨

You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Any formatting violations will result in IMMEDIATE FAILURE.

**🚨 ABSOLUTE REQUIREMENTS - NON-NEGOTIABLE:**
- Output ONLY pure narrative text - no headers, sections, or formatting
- NEVER use bullet points (- like this) or numbered lists (1. like this)
- NEVER use markdown headers (# ## ###) or any HTML/markdown formatting
- NEVER use **bold**, *italics*, or formatting markers of any kind
- Write as continuous flowing speech - not document structure
- Spell out ALL numbers as words: "3" → "three", "2025" → "two thousand twenty five"
- Convert ALL symbols to words: "%" → "percent", "&" → "and", "@" → "at"
- Expand abbreviations: "Dr." → "Doctor", "vs." → "versus", "etc." → "et cetera"
- NO stage directions: no *laughs*, [pause], (sighs), ::thinking::
- Keep sentences under 25 words for natural speech flow

🚨 **THIS IS SPEECH CONTENT, NOT DOCUMENT CONTENT** 🚨

🔥🔥🔥 **USER STYLE SANCTITY - ABSOLUTE HOLY REQUIREMENTS** 🔥🔥🔥

**THESE USER INSTRUCTIONS ARE SACRED - YOU MUST EMBODY THEM COMPLETELY:**

🎯 **MANDATORY NARRATIVE VOICE:**
{user_instructions['role']}

🎭 **NON-NEGOTIABLE TONE & STYLE:**
{user_instructions['tone_style']}

🚨 **SACRED ADDITIONAL REQUIREMENTS:**
{user_instructions['additional_instructions'] if user_instructions['additional_instructions'] else 'None specified'}

**⚡ EVERY WORD YOU WRITE MUST REFLECT THESE USER INSTRUCTIONS ⚡**

## MASTER DOCUMENT GUIDANCE
{master_document[:2000]}{"..." if len(master_document) > 2000 else ""}

## PROGRESS STATUS
- Current Response: {response_num}/{response_plan['responses_needed']}
- Target This Response: {target_chars:,} characters
- Generated So Far: {len(previous_content):,} characters
- Overall Target: {response_plan['total_target']:,} characters

## CONTEXT
{"This is the FIRST response - begin the narrative" if response_num == 1 else f"Previous content (last 2000 chars): ...{previous_content[-2000:]}"}

🔄 **CRITICAL ANTI-REPETITION GUIDANCE:**
- This is Response {response_num} of {response_plan["responses_needed"]} - part of a COMPLETE STORY
- Review the previous content carefully to avoid repetition
- If a literal quote/phrase was already used, DO NOT repeat it unless user explicitly requests repetition
- If a concept was already covered, BUILD UPON IT rather than repeating it
- Each response should ADD NEW VALUE and ADVANCE THE NARRATIVE
- Create SEAMLESS FLOW from previous content - no redundant rehashing
- Only repeat if the user specifically asks for repetition or emphasis

═══════════════════════════════════════════════════════════════

## YOUR TASK
Generate Response {response_num} content following the master document plan above and the HOLY USER INSTRUCTIONS.

**🎯 LENGTH REQUIREMENT (CRITICAL - NON-NEGOTIABLE):**

🚨 **ABSOLUTE MINIMUM: {target_chars:,} CHARACTERS** 🚨
🚨 **YOU MUST OUTPUT AT LEAST {target_chars:,} CHARACTERS** 🚨
🚨 **ANYTHING UNDER {target_chars:,} CHARACTERS IS COMPLETELY UNACCEPTABLE** 🚨

- **TARGET: {target_chars:,} characters**
- **MINIMUM REQUIRED: {target_chars:,} characters (NOT NEGOTIABLE)**
- **PREFERRED RANGE: {target_chars:,} to {int(target_chars * 1.15):,} characters**
- **MAXIMUM ACCEPTABLE: {int(target_chars * 1.2):,} characters**

🔥 **CRITICAL INSTRUCTIONS:** 🔥
- Your response MUST be AT LEAST {target_chars:,} characters long
- Count characters as you write - this is MANDATORY
- If you reach {target_chars:,} characters and the content feels complete, ADD MORE CONTENT
- If you're under {target_chars:,} characters, you have FAILED the task
- Better to write {int(target_chars * 1.1):,} characters than {int(target_chars * 0.9):,} characters

**CONTENT REQUIREMENTS:**
- Follow the master document structure for Response {response_num}
- {"Begin the narrative according to the master document" if response_num == 1 else f"Continue seamlessly from the previous content (you've generated {len(previous_content):,} characters so far)"}
- Maintain the user's specified tone and style
- {"Complete the narrative - this is the final response" if is_final_response else "Prepare content for continuation in the next response"}
- **MOST IMPORTANT: Follow ALL TTS formatting rules above - output must be TTS-ready**

**🔍 MANDATORY VERIFICATION BEFORE SUBMITTING:**
1. Count the EXACT number of characters in your response
2. Is it AT LEAST {target_chars:,} characters? If NO, ADD MORE CONTENT
3. Is it between {target_chars:,} and {int(target_chars * 1.2):,} characters? If NO, adjust immediately
4. Double-check your character count - this is the MOST IMPORTANT requirement
5. If you submit less than {target_chars:,} characters, you have FAILED

🚨 **REMEMBER: {target_chars:,} CHARACTERS IS THE ABSOLUTE MINIMUM** 🚨

🚨 **GENERATE RESPONSE {response_num} NOW - MINIMUM {target_chars:,} CHARACTERS REQUIRED** 🚨

**FINAL REMINDER: Your response must be AT LEAST {target_chars:,} characters. Anything less is unacceptable.**
"""

        return prompt

    def _build_generation_prompt(
        self,
        transcript_text: str,
        master_document: str,
        previous_content: str,
        remaining_chars: int,
        round_number: int
    ) -> str:
        """Build prompt for content generation."""

        user_instructions = self._extract_user_instructions()

        if round_number == 1:
            # First generation
            prompt = f"""# TRANSCRIPT GENERATION - ROUND {round_number}

## YOUR ROLE
{user_instructions['role']}

## MASTER DOCUMENT
{master_document}

## ORIGINAL TRANSCRIPT
{transcript_text[:10000]}{"..." if len(transcript_text) > 10000 else ""}

## YOUR TASK
Generate the BEGINNING of the new transcript following the master document outline.

**CRITICAL REQUIREMENTS:**
- Generate EXACTLY {remaining_chars:,} characters (this is ROUND {round_number} of generation)
- Follow the master document structure and tone guidelines
- Start from the very beginning of the story/content
- Use the tone and style specified by the user: {user_instructions['tone_style']}
- This is the FIRST part - begin the narrative from the start

## USER INSTRUCTIONS (IMPORTANT - FROM USER)
**Structure:** {user_instructions['script_structure'] or "Follow the chapter structure in the master document"}
**Tone & Style:** {user_instructions['tone_style'] or "Professional, engaging narrative"}
**Retention & Flow:** {user_instructions['retention_flow'] or "Maintain engaging flow"}
**Additional:** {user_instructions['additional_instructions'] or "None"}

Generate the content now. Output EXACTLY {remaining_chars:,} characters."""

        else:
            # Continuation generation
            # Get last portion of previous content for context
            context_chars = min(5000, len(previous_content))
            context_content = previous_content[-context_chars:] if context_chars > 0 else ""

            prompt = f"""# TRANSCRIPT GENERATION - CONTINUATION ROUND {round_number}

## YOUR ROLE
{user_instructions['role']}

## MASTER DOCUMENT
{master_document}

## PROGRESS STATUS
- Total characters generated so far: {len(previous_content):,}
- Characters still needed: {remaining_chars:,}
- This is continuation round {round_number}

## PREVIOUS CONTENT (LAST {context_chars} CHARACTERS)
...{context_content}

## YOUR TASK
Continue the transcript seamlessly from where the previous content ended.

**CRITICAL REQUIREMENTS:**
- Generate EXACTLY {remaining_chars:,} characters
- Continue seamlessly from the previous content (no repetition)
- Follow the master document to see what sections still need to be covered
- Maintain the same tone and style: {user_instructions['tone_style']}
- Check the master document to see what parts are still incomplete

## USER INSTRUCTIONS (IMPORTANT - FROM USER)
**Structure:** {user_instructions['script_structure'] or "Follow the chapter structure in the master document"}
**Tone & Style:** {user_instructions['tone_style'] or "Professional, engaging narrative"}
**Retention & Flow:** {user_instructions['retention_flow'] or "Maintain engaging flow"}
**Additional:** {user_instructions['additional_instructions'] or "None"}

Continue the content now. Output EXACTLY {remaining_chars:,} characters."""

        return prompt

    def _ensure_input_fits(self, prompt: str) -> str:
        """Ensure prompt fits within model's input window."""
        max_input_chars = self.model_limits["max_input"]

        if len(prompt) <= max_input_chars:
            return prompt

        logger.warning(f"⚠️ Prompt too long ({len(prompt):,} chars), trimming to fit {max_input_chars:,} chars")

        # Keep the beginning and end, trim the middle (usually the original transcript)
        keep_start = max_input_chars // 3
        keep_end = max_input_chars // 3

        if len(prompt) > keep_start + keep_end:
            trimmed_prompt = (
                prompt[:keep_start] +
                f"\n\n[... CONTENT TRIMMED FOR INPUT WINDOW - {len(prompt) - keep_start - keep_end:,} chars removed ...]\n\n" +
                prompt[-keep_end:]
            )
            logger.info(f"✂️ Trimmed prompt to {len(trimmed_prompt):,} characters")
            return trimmed_prompt

        return prompt[:max_input_chars]

    def _chars_to_tokens(self, chars: int) -> int:
        """Convert characters to tokens, respecting API limits."""
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = chars // 4

        # Get the actual API token limit for this model
        max_tokens_allowed = self.model_limits.get("max_output_tokens", 16384)

        # Never exceed the API's actual token limit
        actual_tokens = min(estimated_tokens, max_tokens_allowed)

        if actual_tokens < estimated_tokens:
            logger.warning(f"⚠️ Token limit enforced: {estimated_tokens:,} tokens → {actual_tokens:,} tokens (API limit)")

        # Always log token conversion for debugging
        logger.info(f"🔧 Token Conversion: {chars:,} chars → {actual_tokens:,} tokens (limit: {max_tokens_allowed:,})")
        return actual_tokens


def process_simple_transcript(
    transcript_text: str,
    config: Dict[str, Any],
    output_dir: Optional[str] = None,
    mock_mode: bool = False
) -> str:
    """
    Main function to process transcript using the simple mechanism.

    Args:
        transcript_text: Original transcript text
        config: Configuration dictionary
        output_dir: Directory to save intermediate files
        mock_mode: Whether to use mock mode

    Returns:
        Processed transcript text
    """
    processor = SimpleTranscriptProcessor(config)
    return processor.process(transcript_text, output_dir, mock_mode)
