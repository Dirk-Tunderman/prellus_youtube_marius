"""
Chunked Transcript Processor Module

This module handles the processing of very large transcripts by breaking them into
manageable chunks, processing each chunk separately using LLM APIs, and then
recombining the processed chunks into a coherent full transcript.

The processing follows a two-step approach:
1. Create a master document that outlines the structure and content
2. Process chunks with context from the master document and previous outputs
"""

import os
import re
import json
import logging
import time
from typing import Dict, Any, List, Tuple, Optional
import math
import time

from .segmenter import TranscriptSegmenter

# Import our processor interface
from .processor_base import TranscriptProcessorInterface
from .custom_prompts import (
    create_master_document_for_expansion_prompt,
    create_simplified_fallback_prompt,
)
from .litellm_processing import process_llm

logger = logging.getLogger(__name__)

# Master document prompt for single-pass processing (when transcript is small enough)
MASTER_DOCUMENT_PROMPT_SINGLE = """
# MASTER DOCUMENT CREATION

## YOUR ROLE
{role}

## OBJECTIVE
Create a detailed outline of the entire transcript's content as a master document that will guide the processing of individual chunks.

## CONTEXT & INPUT DETAILS
- ORIGINAL TRANSCRIPT LENGTH: {original_length} characters total
- TARGET TRANSCRIPT LENGTH: {target_length} characters total ({scaling_factor:.2f}x scaling)
- MAX OUTPUT CHUNK SIZE: {max_chunk_size} characters (API limit per request)
- REQUIRED CHUNKS: {required_chunks} chunks to reach target length
- SCALING DIRECTIVE: {scaling_directive}
- ACTION REQUIRED: {scaling_action}

## TASK DESCRIPTION
Create a master document that identifies the distinct chapters or major sections of the ORIGINAL content.
For each chapter, include:
1. A numbered chapter title (Chapter 1, Chapter 2, etc.) that summarizes the main topic
2. The ORIGINAL character range in the transcript (e.g., "Chapter 1: Introduction (0-{original_chunk_size} characters)")
3. A brief description of the chapter content (2-3 sentences)

## IMPORTANT PLANNING NOTES
- The original transcript will be processed in approximately {required_chunks} chunks
- Each chunk of the original transcript (about {original_chunk_size} characters) will be processed to produce approximately {target_chunk_size} characters
- This is a {scaling_directive} process - the model will need to {scaling_action} the content
- Your chapter divisions should logically divide the ORIGINAL content

## FORMATTING INSTRUCTIONS
- Start each chapter with exactly "Chapter N: Title (range)" with no asterisks or other markdown
- Follow each chapter title with a blank line
- Then include the description on the next line with no bullet points, asterisks or formatting
- Use another blank line to separate chapters
- Do not use markdown formatting like ** or * anywhere in your response

## EXAMPLE FORMAT
Chapter 1: Introduction (0-{original_chunk_size} characters)

This chapter introduces the main concepts of the lecture. It sets the context for the discussion and outlines key themes.

Chapter 2: Historical Background ({original_chunk_size}-{original_chunk_size_double} characters)

This chapter covers the historical context needed to understand the topic. It discusses important events and figures relevant to the subject.

## TONE & STYLE GUIDELINES
{tone_style}

The outline should provide a comprehensive map of the entire transcript's content and structure.
"""

# Master document prompt for first part of multi-part processing
MASTER_DOCUMENT_PROMPT_FIRST_PART = """
# MASTER DOCUMENT CREATION - PART 1

## YOUR ROLE
{role}

## OBJECTIVE
Create a detailed outline of the FIRST PART of a transcript's content.

## CONTEXT & INPUT DETAILS
- TOTAL TRANSCRIPT: {transcript_length} characters
- THIS SEGMENT: First {chunk_length} characters (Part 1 of {total_parts})
- SUGGESTED TOTAL CHAPTERS: {suggested_chapter_count} chapters
- ESTIMATED CHAPTERS IN THIS PART: {estimated_chapters_this_part} chapters

## TASK DESCRIPTION
Create the beginning of a master document that identifies the distinct chapters or major sections found in THIS PART of the content.
For each chapter, include:
1. A numbered chapter title (Chapter 1, Chapter 2, etc.) that summarizes the main topic
2. The approximate character range in the transcript (e.g., "Chapter 1: Introduction (0-5000 characters)")
3. A brief 2-3 sentence description of the chapter content

## FORMATTING INSTRUCTIONS
- Start each chapter with exactly "Chapter N: Title (range)" with no asterisks or other markdown
- Follow each chapter title with a blank line
- Then include the description on the next line with no bullet points, asterisks or formatting 
- Use another blank line to separate chapters
- Do not use markdown formatting like ** or * anywhere in your response
- Each chapter should be approximately 15000 characters long, though the exact length may vary

Only include chapters that appear in the first {chunk_length} characters.
Number chapters sequentially starting with Chapter 1.

## TONE & STYLE GUIDELINES
{tone_style}
"""

# Master document prompt for continuation parts
MASTER_DOCUMENT_PROMPT_CONTINUATION = """
# MASTER DOCUMENT CREATION - CONTINUATION

## YOUR ROLE
{role}

## OBJECTIVE
Continue a detailed outline of a transcript's content.

## CONTEXT & INPUT DETAILS
- TOTAL TRANSCRIPT: {transcript_length} characters
- THIS SEGMENT: Characters {start_char} to {end_char} (Part {part_num} of {total_parts})
- SUGGESTED TOTAL CHAPTERS: {suggested_chapter_count} chapters
- ESTIMATED CHAPTERS IN THIS PART: {estimated_chapters_this_part} chapters

## TASK DESCRIPTION
Continue the master document by identifying the distinct chapters or major sections found in THIS PART of the content.
For each chapter, include:
1. A numbered chapter title (Chapter N, where N continues from the previous part)
2. The approximate character range in the transcript (e.g., "Chapter 5: Topic (20000-25000 characters)")
3. A brief 2-3 sentence description of the chapter content

## FORMATTING INSTRUCTIONS
- Start each chapter with exactly "Chapter N: Title (range)" with no asterisks or other markdown
- Follow each chapter title with a blank line
- Then include the description on the next line with no bullet points, asterisks or formatting 
- Use another blank line to separate chapters
- Do not use markdown formatting like ** or * anywhere in your response
- Each chapter should be approximately 15000 characters long, though the exact length may vary

Only include chapters that appear in characters {start_char} to {end_char}.
Number chapters sequentially CONTINUING from the previous part (do not restart at Chapter 1).
The previous part ended with Chapter {last_chapter_num}.

## TONE & STYLE GUIDELINES
{tone_style}
"""

# Continuation prompt for processing each chunk
CONTINUATION_PROMPT = """
# TRANSCRIPT PROCESSING DIRECTIVE

## YOUR ROLE
{role}

## LENGTH REQUIREMENT
Your output MUST be {target_chunk_length} characters (acceptable range: {min_target_length}-{max_target_length})

## MASTER DOCUMENT OUTLINE
{master_document}

## YOUR TASK
1. Process segment {segment_number} of {total_segments}
2. Convert the transcript text into a polished, well-structured narrative format
3. CRITICAL LENGTH REQUIREMENT: Your output MUST be {target_chunk_length} characters ({scaling_factor:.2f}x the input)
4. This is a {scaling_direction} process - you need to {scaling_instruction}

## SCRIPT STRUCTURE
{script_structure}

## TONE & STYLE
{tone_style}

## RETENTION & FLOW TECHNIQUES
{retention_flow}

## ADDITIONAL INSTRUCTIONS
{additional_instructions}

## SEGMENT-SPECIFIC INSTRUCTIONS
{continuation_instructions}

## OUTPUT REQUIREMENTS
1. LENGTH: {target_chunk_length} characters (MUST be between {min_target_length}-{max_target_length})
2. DETAIL LEVEL: {detail_instruction}
3. Format with proper paragraphs (4-6 sentences) and punctuation
4. Convert lecture style to narrative style 
5. Remove speech disfluencies ("um", "uh", repetitive phrases)

## CHAPTER FORMATTING
- Include explicit chapter headings (e.g., "Chapter 1", "Chapter 2") as they appear in the text
- Start each chapter with its heading followed by a blank line
- Keep the original chapter numbering from the text

{retry_instruction}

This is ABSOLUTELY CRITICAL: Your response will be REJECTED if not within {min_target_length}-{max_target_length} characters.
Current input length: {input_length} characters
Target output length: {target_chunk_length} characters ({scaling_factor:.2f}x the input)
Acceptable range: {min_target_length}-{max_target_length} characters

[Final reminder: GENERATE EXACTLY {target_chunk_length} CHARACTERS (±10%)]
"""


class ChunkedProcessor:
    """
    Processor for large transcripts using chunking strategies.

    This class handles the processing of large transcripts by breaking them into
    more manageable chunks, processing each chunk, and recombining them.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the chunked processor.

        Args:
            config: Configuration dictionary for the processor
        """
        self.chunk_size = config.get("chunk_size", 15000)
        self.max_retries = config.get("max_retries", 3)
        self.min_output_length = config.get("min_output_length", 13000)
        self.max_output_length = config.get("max_output_length", 20000)
        self.master_doc_max_size = config.get("master_doc_max_size", 2000000)

        # New options for chapter-aligned chunking
        self.use_chapter_aligned_chunking = config.get(
            "use_chapter_aligned_chunking", True
        )
        self.max_chapter_chunk_size = config.get("max_chapter_chunk_size", 20000)

        self.output_dir = None  # Will be set in process() method

        logger.info(
            f"Initialized ChunkedProcessor with chunk_size={self.chunk_size}, "
            f"max_retries={self.max_retries}, min_output_length={self.min_output_length}, "
            f"max_output_length={self.max_output_length}, "
            f"master_doc_max_size={self.master_doc_max_size}, "
            f"use_chapter_aligned_chunking={self.use_chapter_aligned_chunking}, "
            f"max_chapter_chunk_size={self.max_chapter_chunk_size}"
        )

    def process(
        self,
        transcript_text: str,
        ai_processor: TranscriptProcessorInterface,
        mock_mode: bool = False,
        output_dir: str = None,
        config: Dict[str, Any] = None,
    ) -> str:
        """
        Process a large transcript by creating a master document and then processing chunks.

        Args:
            transcript_text: The full transcript text to process
            ai_processor: The processor to use for AI operations
            mock_mode: If True, simulates processing without making actual API calls
            output_dir: Optional directory to save individual chunks and master document
            config: Configuration dictionary including target length

        Returns:
            The processed transcript text
        """
        self.output_dir = output_dir

        if mock_mode:
            # For testing without making actual API calls
            logger.info("Running in mock mode, simulating API calls")
            from unittest.mock import MagicMock

            ai_processor = MagicMock()
            ai_processor.process_text.return_value = "This is a mock processed result."

        # Calculate scaling factor
        original_length = len(transcript_text)
        target_length = config.get("ai", {}).get("length_in_chars", original_length)
        scaling_factor = target_length / original_length if original_length > 0 else 1.0

        # Create master document
        master_document = self._create_master_document(
            transcript_text, ai_processor, config
        )

        if output_dir:
            # Save master document
            master_doc_path = os.path.join(output_dir, "master_document.txt")
            with open(master_doc_path, "w", encoding="utf-8") as f:
                f.write(master_document)
            logger.info(f"Saved master document to {master_doc_path}")

        # Choose processing approach based on scaling factor
        if scaling_factor > 1.0:
            # Use expansion chapters approach for extreme expansion
            logger.info(
                f"Using expansion chapters approach for high scaling factor ({scaling_factor:.2f}x)"
            )
            processed_transcript = self._process_with_expansion_chapters(
                transcript_text, master_document, ai_processor, config
            )
        elif self.use_chapter_aligned_chunking:
            # Use chapter-aligned chunking approach
            logger.info("Using chapter-aligned chunking approach")
            processed_transcript = self._process_with_chapter_aligned_chunks(
                transcript_text, master_document, ai_processor, config
            )
        else:
            # Use fixed-size chunking approach
            logger.info("Using fixed-size chunking approach")
            processed_transcript = self._process_chunks_with_continuity(
                transcript_text, master_document, ai_processor, config
            )

        # FINAL LENGTH CHECK: Check if the transcript is too long and trim if needed
        processed_transcript_length = len(processed_transcript)
        expected_length = config.get("ai", {}).get("length_in_chars", original_length)
        logger.info(f"Final transcript length: {processed_transcript_length} characters")
        logger.info(f"Expected transcript length: {expected_length} characters")
        
        # Calculate maximum acceptable length (expected length + 50,000 characters)
        max_acceptable_length = expected_length + 50000
        logger.info(f"Maximum acceptable length: {max_acceptable_length} characters")
        
        # Check if transcript needs trimming
        if processed_transcript_length > max_acceptable_length:
            logger.warning(f"Transcript is too long by {processed_transcript_length - max_acceptable_length} characters")
            
            # Find chapter boundaries in the transcript
            chapter_pattern = re.compile(r'^Chapter \d+', re.MULTILINE)
            chapter_matches = list(chapter_pattern.finditer(processed_transcript))
            
            if len(chapter_matches) > 1:  # Only proceed if we have more than one chapter
                logger.info(f"Found {len(chapter_matches)} chapters in the transcript")
                
                # Create a list of chapter positions and sizes
                chapters = []
                for i in range(len(chapter_matches)):
                    start_pos = chapter_matches[i].start()
                    end_pos = chapter_matches[i+1].start() if i < len(chapter_matches) - 1 else len(processed_transcript)
                    chapter_size = end_pos - start_pos
                    chapter_title = processed_transcript[start_pos:start_pos+50].split("\n")[0]
                    
                    chapters.append({
                        'index': i,
                        'start': start_pos,
                        'end': end_pos,
                        'size': chapter_size,
                        'title': chapter_title
                    })
                
                # Log chapter information
                for ch in chapters:
                    logger.info(f"Chapter {ch['index'] + 1}: {ch['title']} ({ch['size']} chars)")
                
                # Calculate how many chapters we need to remove from the end
                chapters_to_keep = len(chapters)
                trimmed_length = processed_transcript_length
                
                # Remove chapters from the end until we're within the max acceptable length
                while trimmed_length > max_acceptable_length and chapters_to_keep > 1:
                    chapters_to_keep -= 1
                    removed_chapter_size = chapters[chapters_to_keep]['size']
                    trimmed_length -= removed_chapter_size
                    logger.info(f"Reducing lenght")
                
                if chapters_to_keep < len(chapters):
                    # Reconstruct the transcript with only the chapters we're keeping
                    trimmed_transcript = processed_transcript[:chapters[chapters_to_keep]['start']]
                    final_length = len(trimmed_transcript)
                    
                    logger.info(f"Trimmed transcript")

                    
                    processed_transcript = trimmed_transcript
                    
                    # Save the trimmed transcript if output_dir is provided
                    if output_dir:
                        trimmed_path = os.path.join(output_dir, "trimmed_transcript.txt")
                        with open(trimmed_path, "w", encoding="utf-8") as f:
                            f.write(processed_transcript)
                        logger.info(f"Saved trimmed transcript to {trimmed_path}")
                else:
                    logger.warning("Could not trim transcript by removing whole chapters.")
            else:
                logger.warning("Not enough chapters found to trim the transcript")
        
        return processed_transcript

    def _parse_master_document(self, master_document: str) -> List[Dict[str, Any]]:
        """
        Parse the master document to extract chapter information.

        Args:
            master_document: The master document text

        Returns:
            A list of chapter dictionaries containing title, number, and description
        """
        # Use regex to extract chapters from the master document with a more robust pattern
        # This regex is more flexible to handle various formats including markdown and plain text
        chapter_pattern = r"\*?\*?Chapter\s+(\d+)(?:\s*[:-]\s*|\s+)([^(]*?)(?:\s*\([^)]+\))?(?:\*?\*?)(?:\n\n|\n|\Z)((?:(?!\*?\*?Chapter\s+\d+(?:\s*[:-]\s*|\s+))[\s\S])*)"
        chapter_matches = re.finditer(chapter_pattern, master_document, re.DOTALL)

        chapters = []
        for match in chapter_matches:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            chapter_description = match.group(3).strip() if match.group(3) else ""

            # Store the character range of the chapter in the master document
            start_pos = match.start()
            end_pos = match.end()

            chapters.append(
                {
                    "number": chapter_num,
                    "title": chapter_title,
                    "description": chapter_description,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "text": match.group(0),
                    "length": end_pos - start_pos,
                }
            )

        # Sort chapters by number to ensure correct order
        chapters.sort(key=lambda x: x["number"])

        if chapters:
            # Calculate average chapter size and other statistics
            chapter_lengths = [c["length"] for c in chapters]
            avg_chapter_length = sum(chapter_lengths) / len(chapter_lengths)
            min_chapter_length = min(chapter_lengths)
            max_chapter_length = max(chapter_lengths)
            target_chapter_size = 15000  # Our target chapter size

            logger.info(
                f"Successfully extracted {len(chapters)} chapters from master document"
            )
            logger.info(
                f"Chapter statistics: avg={avg_chapter_length:.0f}, min={min_chapter_length}, max={max_chapter_length} (target={target_chapter_size})"
            )

            # Check if chapters are significantly different from target size
            if (
                avg_chapter_length < target_chapter_size * 0.5
                or avg_chapter_length > target_chapter_size * 2
            ):
                logger.warning(
                    f"Average chapter length ({avg_chapter_length:.0f}) is far from target size ({target_chapter_size})"
                )

            # Log the first few chapters for debugging
            for i, chapter in enumerate(chapters[:3]):
                logger.debug(
                    f"Chapter {chapter['number']}: {chapter['title']} (Pos: {chapter['start_pos']}-{chapter['end_pos']}, Length: {chapter['length']})"
                )

            if len(chapters) > 3:
                logger.debug(f"... and {len(chapters) - 3} more chapters")
        else:
            logger.warning(
                "No chapters found in master document using standard pattern"
            )

            # Fallback: Try a simpler regex pattern as a last resort
            logger.info("Attempting fallback chapter detection method")
            simple_pattern = r"Chapter\s+(\d+)[^\n]*\n"
            chapter_matches = re.finditer(simple_pattern, master_document)

            # Get all potential chapter start positions
            positions = [
                (int(match.group(1)), match.start()) for match in chapter_matches
            ]

            if positions:
                positions.sort()  # Sort by chapter number

                # Create chapters based on positions
                for i, (num, pos) in enumerate(positions):
                    end_pos = (
                        positions[i + 1][1]
                        if i < len(positions) - 1
                        else len(master_document)
                    )
                    text = master_document[pos:end_pos].strip()

                    # Extract title - everything after "Chapter N" on the first line
                    title_match = re.search(r"Chapter\s+\d+[:-]?\s*([^\n]+)", text)
                    title = (
                        title_match.group(1).strip()
                        if title_match
                        else f"Unknown Chapter {num}"
                    )

                    # Description is everything after the first line
                    lines = text.split("\n", 1)
                    description = lines[1].strip() if len(lines) > 1 else ""

                    chapters.append(
                        {
                            "number": num,
                            "title": title,
                            "description": description,
                            "start_pos": pos,
                            "end_pos": end_pos,
                            "text": text,
                        }
                    )

                logger.info(f"Fallback method found {len(chapters)} chapters")
            else:
                logger.warning(
                    "Fallback chapter detection also failed - no chapters found"
                )
                # Log the first 500 characters of the master document for debugging
                preview = master_document[:500].replace("\n", " ")
                logger.debug(f"Master document preview: {preview}...")

        return chapters

    def _create_master_document(
        self,
        transcript_text: str,
        ai_processor: TranscriptProcessorInterface,
        config: Dict[str, Any],
    ) -> str:
        """
        Create a master document that outlines the structure and content of the transcript.
        The function handles both expansion and condensation of transcripts.

        Args:
            transcript_text: The full transcript text
            ai_processor: The AI processor to use
            config: Configuration dictionary including target length

        Returns:
            The master document as a string
        """
        # Get original transcript length
        original_length = len(transcript_text)

        # Get target length from config
        target_length = config.get("ai", {}).get("length_in_chars", original_length)

        # Calculate scaling factor
        scaling_factor = target_length / original_length if original_length > 0 else 1.0

        # Define API output limits
        max_chunk_size = 15000  # Maximum output chunk size the API can handle

        # Calculate how many chunks we'll need to reach target length
        required_chunks = math.ceil(target_length / max_chunk_size)

        # Calculate original chunk size needed to produce the desired output
        original_chunk_size = min(math.ceil(original_length / required_chunks), 15000)

        # Calculate target chunk size (output size per chunk)
        target_chunk_size = min(
            max_chunk_size, math.ceil(target_length / required_chunks)
        )

        # Extract structured prompt components from config
        prompt_role = config.get("ai", {}).get(
            "prompt_role",
            "You are an expert writer tasked with processing transcript content.",
        )
        prompt_script_structure = config.get("ai", {}).get(
            "prompt_script_structure", ""
        )
        prompt_tone_style = config.get("ai", {}).get("prompt_tone_style", "")
        prompt_retention_flow = config.get("ai", {}).get("prompt_retention_flow", "")
        prompt_additional_instructions = config.get("ai", {}).get(
            "prompt_additional_instructions", ""
        )

        # Determine scaling direction for prompting
        if scaling_factor > 1.0:
            logger.info(
                f"Using expansion-specific master document for high scaling factor ({scaling_factor:.2f}x)"
            )
            return self._create_master_document_for_expansion(
                transcript_text, target_length, ai_processor, config
            )
        elif scaling_factor < 1.0:
            scaling_directive = "content condensation"
            scaling_action = "condense while preserving key information"
        else:
            scaling_directive = "minimal length adjustment"
            scaling_action = "maintain similar level of detail with minor adjustments"

        # Log the plan
        logger.info(
            f"Creating master document with scaling factor: {scaling_factor:.2f}x"
        )
        logger.info(
            f"Original length: {original_length} characters, Target length: {target_length} characters"
        )
        logger.info(
            f"Required chunks: {required_chunks}, Original chunk size: {original_chunk_size}, Target chunk size: {target_chunk_size}"
        )
        logger.info(f"Scaling directive: {scaling_directive}")

        # Check if we need to process this in chunks or all at once
        if original_length <= self.master_doc_max_size:
            # For a shorter master document we can process in one go
            logger.info(
                f"Creating master document in one pass ({original_length} characters)"
            )

            # Calculate example values for the prompt
            original_chunk_size_double = original_chunk_size * 2

            # Format the master document prompt with structured components
            master_document_prompt = MASTER_DOCUMENT_PROMPT_SINGLE.format(
                original_length=original_length,
                target_length=target_length,
                scaling_factor=scaling_factor,
                max_chunk_size=max_chunk_size,
                required_chunks=required_chunks,
                original_chunk_size=original_chunk_size,
                original_chunk_size_double=original_chunk_size_double,
                target_chunk_size=target_chunk_size,
                scaling_directive=scaling_directive,
                scaling_action=scaling_action,
                role=prompt_role,
                tone_style=prompt_tone_style,
            )

            # Process the entire transcript
            master_document = process_llm(
                context=transcript_text,
                model=config.get("ai", {}).get("model"),
                system_prompt=master_document_prompt,
                max_tokens=4096,
                temperature=0.7,
            )

            logger.info(
                f"Master document created [OUTPUT SIZE: {len(master_document)} characters]"
            )

            # Save the master document and prompt if output_dir is provided
            if self.output_dir:
                master_doc_path = os.path.join(self.output_dir, "master_document.txt")
                with open(master_doc_path, "w", encoding="utf-8") as f:
                    f.write(master_document)
                logger.info(f"Saved master document to {master_doc_path}")

                # Save the prompt used for debugging
                prompt_path = os.path.join(
                    self.output_dir, "master_document_prompt.txt"
                )
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(master_document_prompt)
                logger.debug(f"Saved master document prompt to {prompt_path}")

            return master_document

        # For larger transcripts, we process in chunks
        transcript_length = len(transcript_text)
        logger.info(
            f"Creating master document in chunks (transcript size: {transcript_length} characters)"
        )

        # Determine chunk size for master document
        master_doc_chunk_size = (
            self.master_doc_max_size // 2
        )  # Use half the max size for better processing

        # Split the transcript into chunks for master document creation
        chunks = []
        for i in range(0, transcript_length, master_doc_chunk_size):
            end_idx = min(i + master_doc_chunk_size, transcript_length)
            chunks.append(transcript_text[i:end_idx])

        total_chunks = len(chunks)
        logger.info(
            f"Split transcript into {total_chunks} chunks for master document creation"
        )

        # Calculate suggested chapter count based on transcript length
        # Aim for chapters of ~15000 characters
        suggested_chapter_count = max(1, math.ceil(transcript_length / 15000))

        # Process each chunk and combine into a full master document
        master_doc_parts = []

        for i, chunk in enumerate(chunks):
            chunk_length = len(chunk)
            logger.info(
                f"Processing master document chunk {i+1}/{total_chunks} [SIZE: {chunk_length} characters]"
            )

            # Calculate estimated number of chapters for this chunk
            estimated_chapters_this_part = max(
                1, round((chunk_length / transcript_length) * suggested_chapter_count)
            )

            if i == 0:
                # First chunk uses the first part prompt
                prompt = MASTER_DOCUMENT_PROMPT_FIRST_PART.format(
                    total_parts=total_chunks,
                    chunk_length=chunk_length,
                    transcript_length=transcript_length,
                    suggested_chapter_count=suggested_chapter_count,
                    estimated_chapters_this_part=estimated_chapters_this_part,
                    role=prompt_role,
                    tone_style=prompt_tone_style,
                )
                logger.info(f"Using FIRST PART prompt for chunk {i+1}/{total_chunks}")
            else:
                # Subsequent chunks use the continuation prompt
                previous_outline = master_doc_parts[-1]
                # Extract the last chapter number from the previous outline
                chapter_pattern = r"Chapter\s+(\d+):"
                chapter_matches = re.findall(chapter_pattern, previous_outline)

                # Use a fallback pattern if the first one doesn't find any chapters
                if not chapter_matches:
                    fallback_pattern = r"Chapter\s+(\d+)"
                    chapter_matches = re.findall(fallback_pattern, previous_outline)

                # Get the last chapter number or default to 0
                last_chapter_num = 0
                if chapter_matches:
                    try:
                        last_chapter_num = int(chapter_matches[-1])
                        logger.info(
                            f"Found last chapter number from previous part: Chapter {last_chapter_num}"
                        )
                    except (ValueError, IndexError) as e:
                        logger.warning(
                            f"Error parsing last chapter number: {e}. Using default of 0."
                        )
                else:
                    logger.warning(
                        "No chapter numbers found in previous part. Using default of 0."
                    )

                start_char = i * master_doc_chunk_size
                end_char = min((i + 1) * master_doc_chunk_size, transcript_length)

                prompt = MASTER_DOCUMENT_PROMPT_CONTINUATION.format(
                    part_num=i + 1,
                    total_parts=total_chunks,
                    start_char=start_char,
                    end_char=end_char,
                    last_chapter_num=last_chapter_num,
                    transcript_length=transcript_length,
                    suggested_chapter_count=suggested_chapter_count,
                    estimated_chapters_this_part=estimated_chapters_this_part,
                    role=prompt_role,
                    tone_style=prompt_tone_style,
                )
                logger.info(f"Using CONTINUATION prompt for chunk {i+1}/{total_chunks}")

            # Process this chunk
            chunk_master_doc = process_llm(
                context=chunk, system_prompt=prompt, model=config.get("ai", {}).get("model"),max_tokens=4096, temperature=0.7
            )

            # Log the output size
            logger.info(
                f"Master document chunk {i+1} processed [OUTPUT SIZE: {len(chunk_master_doc)} characters]"
            )

            # Add to master document parts
            master_doc_parts.append(chunk_master_doc)

            # Save chunk processing info if output directory is provided
            if self.output_dir:
                chunk_dir = os.path.join(self.output_dir, "master_chunks")
                os.makedirs(chunk_dir, exist_ok=True)

                # Save original chunk
                original_path = os.path.join(
                    chunk_dir, f"original_master_chunk_{i+1}.txt"
                )
                with open(original_path, "w", encoding="utf-8") as f:
                    f.write(chunk)

                # Save processed chunk
                processed_path = os.path.join(
                    chunk_dir, f"processed_master_chunk_{i+1}.txt"
                )
                with open(processed_path, "w", encoding="utf-8") as f:
                    f.write(chunk_master_doc)

                # Save prompt
                prompt_path = os.path.join(chunk_dir, f"prompt_master_chunk_{i+1}.txt")
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(prompt)

        # Combine all master document parts
        full_master_document = "\n\n".join(master_doc_parts)

        # Clean up formatting issues
        full_master_document = re.sub(r"\n{3,}", "\n\n", full_master_document)

        logger.info(
            f"Full master document created [OUTPUT SIZE: {len(full_master_document)} characters]"
        )

        return full_master_document

    def _create_master_document_for_expansion(
        self, transcript_text, target_length, ai_processor, config
    ):
        """
        Create a master document specifically designed for extreme expansion cases.

        Args:
            transcript_text: The original transcript text
            target_length: The target length in characters
            ai_processor: The AI processor to use
            config: Configuration dictionary with prompt components

        Returns:
            A master document with detailed chapter outlines
        """
        # Import modules at function level to avoid scope issues
        import os
        import time
        
        original_length = len(transcript_text)
        scaling_factor = target_length / original_length

        # Extract structured prompt components
        prompt_role = config.get("ai", {}).get("prompt_role", "")
        prompt_script_structure = config.get("ai", {}).get(
            "prompt_script_structure", ""
        )
        prompt_tone_style = config.get("ai", {}).get("prompt_tone_style", "")
        prompt_retention_flow = config.get("ai", {}).get("prompt_retention_flow", "")
        prompt_additional_instructions = config.get("ai", {}).get(
            "prompt_additional_instructions", ""
        )
        
        # Get model from config
        model = config.get("ai", {}).get("model")

        # Calculate how many output chapters we need based on target length
        max_chapter_size = 15000  # Max API output size
        required_chapters = math.ceil(target_length / max_chapter_size)

        # Generate master document with detailed topic outlines
        master_doc = "# MASTER DOCUMENT FOR EXTREME EXPANSION\n\n"
        master_doc += f"Original Length: {original_length} characters\n"
        master_doc += f"Target Length: {target_length} characters\n"
        master_doc += f"Scaling Factor: {scaling_factor:.2f}x\n"
        master_doc += f"Required Chapters: {required_chapters}\n\n"

        # Divide the original transcript into roughly equal segments
        segment_size = original_length / required_chapters

        for i in range(required_chapters):
            start_char = int(i * segment_size)
            end_char = int(min((i + 1) * segment_size, original_length))

            # Extract the segment text
            segment_text = transcript_text[start_char:end_char]

            # Create a detailed chapter outline
            master_doc += f"## Chapter {i+1}: {segment_text[:50]}... ({start_char}-{end_char})\n\n"
            master_doc += f"This segment contains approximately {len(segment_text)} characters and should be expanded to at least {max_chapter_size} characters.\n\n"

            # Generate topic outline for this segment using an API call
            topic_prompt = f"""
    # CHAPTER TOPIC OUTLINE GENERATOR

    ## YOUR ROLE
    {prompt_role}

    ## OBJECTIVE
    Identify 5-8 main topics that can be expanded upon for Chapter {i+1}.

    ## CONTEXT
    This is segment {i+1} of {required_chapters} from a transcript that needs to be expanded {scaling_factor:.2f}x.

    ## SEGMENT TEXT TO ANALYZE
    {segment_text}

    ## YOUR TASK
    For each topic:
    1. Provide a clear, descriptive title
    2. Briefly explain what should be covered (2-3 sentences)
    3. Suggest additional related subtopics that aren't explicitly mentioned but would enhance this chapter

    ## OUTPUT FORMAT
    Format your response as "TOPICS TO COVER IN CHAPTER {i+1}:" followed by a numbered list of topics with brief descriptions.

    ## TONE & STYLE
    {prompt_tone_style}
    """

            # Make a separate API call to get topic suggestions
            try:
                topic_outline = process_llm(
                    context=segment_text,
                    system_prompt=topic_prompt,
                    model=model,  # Use model from config
                    max_tokens=4096,
                    temperature=0.7,
                )

                master_doc += topic_outline + "\n\n"
            except Exception as e:
                logger.error(f"Error generating topic outline for Chapter {i+1}: {e}")
                # Fallback if API call fails
                master_doc += f"TOPICS TO COVER IN CHAPTER {i+1}:\n"
                master_doc += "1. Main theme of this segment\n"
                master_doc += "2. Historical context and background\n"
                master_doc += "3. Key developments and events\n"
                master_doc += "4. Important figures and their contributions\n"
                master_doc += "5. Significance and impact\n\n"

            master_doc += "EXPANSION GUIDANCE:\n"
            master_doc += "- Add historical context and background information\n"
            master_doc += "- Include relevant examples, anecdotes, and case studies\n"
            master_doc += "- Develop each concept thoroughly with explanations\n"
            master_doc += "- Add descriptive details to create vivid imagery\n"
            master_doc += (
                "- Incorporate relevant quotes or perspectives from experts\n\n"
            )

        # Add example for the first chapter
        master_doc += """
    EXAMPLE DETAILED CHAPTER OUTLINE (for reference):

    ## Chapter 1: Introduction to the Netherlands (0-1200)

    TOPICS TO COVER IN CHAPTER 1:
    1. Geography and Landscape of the Netherlands
    - Describe the unique flat terrain and coastal geography
    - Explain how geography shaped Dutch culture and development
    - Include details about notable geographic features (polders, dikes, canals)

    2. Dutch Cultural Identity
    - Explore the origins of Dutch cultural traits like practicality and tolerance
    - Discuss the dual naming of Holland vs. Netherlands
    - Examine how geography influenced national character

    3. Early Settlement History
    - Cover prehistoric settlements in the region
    - Discuss early tribal populations and their way of life
    - Explain the challenges of living in a low-lying coastal area

    4. Development of Transportation and Infrastructure
    - Detail the importance of canals and waterways
    - Explain the early development of dikes and water management
    - Describe traditional Dutch transportation methods

    5. Formation of Dutch Identity
    - Discuss linguistic and cultural development
    - Explain how Dutch identity emerged as distinct from neighboring regions
    - Explore early political structures and governance

    EXPANSION GUIDANCE:
    - Include vivid descriptions of the Dutch landscape
    - Add historical anecdotes about early Dutch innovations
    - Include relevant historical context about European development during this period
    - Add details about daily life in early Dutch settlements
    - Incorporate accounts of travelers who visited the region
    """

        return master_doc

    def _process_with_expansion_chapters(
        self,
        transcript_text: str,
        master_document: str,
        ai_processor: TranscriptProcessorInterface,
        config: Dict[str, Any],
    ) -> str:
        """
        Process transcript for extreme expansion cases by creating full-length chapters from small segments.

        Args:
            transcript_text: Original transcript text
            master_document: Master document with chapter plan
            ai_processor: AI processor to use
            config: Configuration including target length

        Returns:
            The expanded transcript as a string
        """
        # Import modules at function level to avoid scope issues
        import os
        import time
        
        original_length = len(transcript_text)
        target_length = config.get("ai", {}).get("length_in_chars", original_length)
        scaling_factor = target_length / original_length if original_length > 0 else 1.0
        
        # Get model from config
        model = config.get("ai", {}).get("model")

        logger.info(
            f"Processing transcript with extreme expansion ({scaling_factor:.2f}x)"
        )

        # Extract structured prompt components
        prompt_role = config.get("ai", {}).get("prompt_role", "")
        prompt_script_structure = config.get("ai", {}).get(
            "prompt_script_structure", ""
        )
        prompt_tone_style = config.get("ai", {}).get("prompt_tone_style", "")
        prompt_retention_flow = config.get("ai", {}).get("prompt_retention_flow", "")
        prompt_additional_instructions = config.get("ai", {}).get(
            "prompt_additional_instructions", ""
        )

        # Calculate number of chapters needed to reach target length
        max_chapter_size = 15000  # API output limit per call
        required_chapters = math.ceil(target_length / max_chapter_size)

        # Create segment boundaries for the original transcript
        segment_size = original_length / required_chapters
        segments = []

        for i in range(required_chapters):
            start_char = int(i * segment_size)
            end_char = int(min((i + 1) * segment_size, original_length))
            segments.append(
                {
                    "chapter_num": i + 1,
                    "start_char": start_char,
                    "end_char": end_char,
                    "text": transcript_text[start_char:end_char],
                }
            )

        logger.info(
            f"Divided original transcript ({original_length} chars) into {len(segments)} segments for expansion"
        )

        # Process each segment into a full chapter
        processed_chapters = []
        chunks_info = []
        previous_chapter = None

        # Create chunks directory if output_dir is provided
        chunks_dir = None
        if self.output_dir:
            chunks_dir = os.path.join(self.output_dir, "expansion_chunks")
            os.makedirs(chunks_dir, exist_ok=True)
            logger.info(f"Created directory for expansion chunks: {chunks_dir}")

        for i, segment in enumerate(segments):
            chapter_num = segment["chapter_num"]
            is_last = i == len(segments) - 1

            logger.info(
                f"Processing expansion segment {i+1}/{len(segments)} for Chapter {chapter_num}"
            )
            logger.info(
                f"Original segment size: {len(segment['text'])} chars, target: {max_chapter_size} chars"
            )

            # Create expansion prompt using our updated format
            prompt = create_master_document_for_expansion_prompt(
                transcript_text=transcript_text,
                target_length=max_chapter_size,
                chapter_number=chapter_num,
                segment_text=segment["text"],
                master_document=master_document,  # Pass the master document
            ).format(
                role=prompt_role,
                script_structure=prompt_script_structure,
                tone_style=prompt_tone_style,
                retention_flow=prompt_retention_flow,
                additional_instructions=prompt_additional_instructions,
            )

            # Add previous chapter context if available
            if previous_chapter:
                prompt += f"\n\nPREVIOUS CHAPTER ENDING (for continuity):\n{previous_chapter[-400:]}"

            # Save the original segment if output_dir is provided
            if chunks_dir:
                segment_path = os.path.join(chunks_dir, f"original_segment_{i+1}.txt")
                with open(segment_path, "w", encoding="utf-8") as f:
                    f.write(segment["text"])

                prompt_path = os.path.join(chunks_dir, f"prompt_segment_{i+1}.txt")
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(prompt)

            # Process this segment into a full chapter
            success = False
            retries = 0
            chapter_text = (
                None  # Initialize to None to track if we ever get any response
            )

            while not success and retries < self.max_retries:
                try:
                    new_chapter_text = process_llm(
                        context=segment["text"],
                        system_prompt=prompt,
                        model=model,  # Use model from config
                        max_tokens=4096,
                        temperature=0.7,
                    )

                    # Save this output regardless of validation (will be used if all retries fail)
                    chapter_text = new_chapter_text

                    # Validate output length
                    output_length = len(chapter_text)
                    logger.info(
                        f"Generated Chapter {chapter_num}: {output_length} characters"
                    )

                    min_target_length = int(max_chapter_size * 0.7)
                    max_target_length = int(max_chapter_size * 1.7)

                    if output_length < min_target_length:
                        logger.warning(
                            f"Chapter {chapter_num} is too short ({output_length} vs. min {min_target_length}). Retrying."
                        )
                        # Update prompt with instruction to make output longer
                        additional_length_needed = min_target_length - output_length
                        prompt += f"\n\nYour last output was TOO SHORT ({output_length} characters). Please add approximately {additional_length_needed} more characters to reach the minimum length of {min_target_length}."
                        retries += 1
                        continue

                    if output_length > max_target_length:
                        logger.warning(
                            f"Chapter {chapter_num} is too long ({output_length} vs. max {max_target_length}). Retrying."
                        )
                        # Update prompt with instruction to make output shorter
                        excess_length = output_length - max_target_length
                        prompt += f"\n\nYour last output was TOO LONG ({output_length} characters). Please remove approximately {excess_length} characters to stay under the maximum length of {max_target_length}."
                        retries += 1
                        continue

                    # If we get here, the output is valid
                    success = True

                except Exception as e:
                    logger.error(f"Error generating Chapter {chapter_num}: {e}")
                    retries += 1
                    time.sleep(2)  # Wait before retry

            # If all retries failed but we still have output, use the last attempt instead of falling back
            if not success and chapter_text:
                logger.warning(
                    f"All retries failed for Chapter {chapter_num}. Using last generated output."
                )
            # If we have no output at all, create a placeholder
            elif not chapter_text:
                logger.error(
                    f"No valid output generated for Chapter {chapter_num}. Creating placeholder."
                )
                chapter_text = f"Chapter {chapter_num}\n\n[Unable to generate content for this chapter]\n\n{segment['text']}"

            # Add to processed chapters
            processed_chapters.append(chapter_text)
            previous_chapter = chapter_text

            # Record chunk info
            output_length = len(chapter_text)
            chunks_info.append(
                {
                    "chunk_index": i,
                    "chapter_num": chapter_num,
                    "original_length": len(segment["text"]),
                    "target_length": max_chapter_size,
                    "processed_length": output_length,
                    "expansion_ratio": (
                        output_length / len(segment["text"])
                        if len(segment["text"]) > 0
                        else 0
                    ),
                    "start_char": segment["start_char"],
                    "end_char": segment["end_char"],
                    "is_last_chunk": is_last,
                    "all_retries_failed": not success,
                }
            )

            # Save the processed chapter if output_dir is provided
            if chunks_dir:
                chapter_path = os.path.join(chunks_dir, f"processed_chapter_{i+1}.txt")
                with open(chapter_path, "w", encoding="utf-8") as f:
                    f.write(chapter_text)

        # Join all chapters and return
        expanded_transcript = "\n\n".join(processed_chapters)

        # Save chunk info if output directory exists
        if self.output_dir:
            chunks_info_path = os.path.join(
                self.output_dir, "expansion_chunks_info.json"
            )
            with open(chunks_info_path, "w", encoding="utf-8") as f:
                json.dump(chunks_info, f, indent=2)

        return expanded_transcript

    def _create_chapter_aligned_chunks(
        self, chapters: List[Dict[str, Any]], transcript_length: int = None
    ) -> List[Dict[str, Any]]:
        """
        Create processing chunks that align with chapter boundaries.

        Args:
            chapters: The list of chapters extracted from the master document
            transcript_length: Optional total length of the transcript

        Returns:
            A list of chunk dictionaries containing start_char, end_char, and chapter information
        """
        if not chapters:
            logger.warning("No chapters provided to create chunks")
            return []

        logger.info(f"Creating chapter-aligned chunks from {len(chapters)} chapters")

        # Define maximum size for a chapter-aligned chunk
        max_chunk_size = self.max_chapter_chunk_size
        target_chapter_size = 15000  # Target size per chapter for consistency
        logger.info(
            f"Maximum chapter chunk size: {max_chunk_size} characters, target chapter size: {target_chapter_size} characters"
        )

        # Initialize chunks
        chunks = []
        current_chunk = {
            "chapter_numbers": [],
            "start_char": 0,
            "end_char": 0,
            "chapters": [],
        }

        # Filter chapters by their existence in the transcript
        # This is needed because sometimes the master document might mention chapters
        # that don't actually appear in the transcript
        first_chapter_number = chapters[0]["number"]

        # Map actual transcript character positions to chapters based on their relative positions
        # This assumes the master document chapter ranges are proportional to the transcript
        if transcript_length:
            # Calculate mapping factor from master document to transcript
            # This is a simple proportional mapping and might need refinement
            for chapter in chapters:
                # Calculate relative positions within the master document if needed
                # Implement more sophisticated mapping if necessary
                pass

        # Process chapters to create chunks
        for i, chapter in enumerate(chapters):
            chapter_num = chapter["number"]

            # Skip chapters that don't make sense (like negative chapter numbers)
            if chapter_num < 1:
                logger.warning(f"Skipping invalid chapter number: {chapter_num}")
                continue

            # Determine if this is the first chapter
            is_first_chapter = i == 0

            # For the first chapter, start a new chunk
            if is_first_chapter:
                current_chunk = {
                    "chapter_numbers": [chapter_num],
                    "start_char": 0,  # Start of transcript
                    "end_char": 0,  # Will be updated
                    "chapters": [chapter],
                }
            else:
                # Estimate chapter size
                if transcript_length:
                    # Skip chapters that might cause invalid chunk creation
                    if not current_chunk["chapter_numbers"]:
                        logger.warning(
                            f"Current chunk has no chapters, adding chapter {chapter_num}"
                        )
                        current_chunk["chapter_numbers"].append(chapter_num)
                        current_chunk["chapters"].append(chapter)
                        continue

                    # If we know the transcript length, we can estimate chapter sizes
                    # This is a more accurate estimation based on target chapter size
                    est_chapter_size = min(
                        target_chapter_size, transcript_length // len(chapters)
                    )
                    current_chunk_size = est_chapter_size * len(
                        current_chunk["chapter_numbers"]
                    )

                    # Check if adding this chapter would exceed the max chunk size
                    if (
                        current_chunk_size + est_chapter_size > max_chunk_size
                        and len(current_chunk["chapter_numbers"]) > 0
                    ):
                        # Finalize current chunk
                        chunks.append(current_chunk)

                        # Start new chunk with this chapter
                        current_chunk = {
                            "chapter_numbers": [chapter_num],
                            "start_char": 0,  # Will be updated
                            "end_char": 0,  # Will be updated
                            "chapters": [chapter],
                        }
                    else:
                        # Add chapter to current chunk
                        current_chunk["chapter_numbers"].append(chapter_num)
                        current_chunk["chapters"].append(chapter)
                else:
                    # Skip chapters that might cause invalid chunk creation
                    if not current_chunk["chapter_numbers"]:
                        logger.warning(
                            f"Current chunk has no chapters, adding chapter {chapter_num}"
                        )
                        current_chunk["chapter_numbers"].append(chapter_num)
                        current_chunk["chapters"].append(chapter)
                        continue

                    # If we don't know the transcript length, use a simpler heuristic
                    # For example, limit by number of chapters per chunk
                    max_chapters_per_chunk = max(
                        1, max_chunk_size // target_chapter_size
                    )  # Calculate based on target size

                    if len(current_chunk["chapter_numbers"]) >= max_chapters_per_chunk:
                        # Finalize current chunk
                        chunks.append(current_chunk)

                        # Start new chunk with this chapter
                        current_chunk = {
                            "chapter_numbers": [chapter_num],
                            "start_char": 0,  # Will be updated
                            "end_char": 0,  # Will be updated
                            "chapters": [chapter],
                        }
                    else:
                        # Add chapter to current chunk
                        current_chunk["chapter_numbers"].append(chapter_num)
                        current_chunk["chapters"].append(chapter)

        # Add the last chunk if it's not empty
        if current_chunk["chapter_numbers"]:
            chunks.append(current_chunk)

        # Now we need to determine the actual character positions in the transcript
        # This is a simplification - in reality, we'd need to parse the transcript
        # to find the actual chapter positions
        if transcript_length:
            # Simple heuristic: divide the transcript equally among chunks
            chunk_size = transcript_length // len(chunks)

            for i, chunk in enumerate(chunks):
                chunk["start_char"] = i * chunk_size
                chunk["end_char"] = (
                    (i + 1) * chunk_size if i < len(chunks) - 1 else transcript_length
                )

        # Log chunk information
        logger.info(f"Created {len(chunks)} chapter-aligned chunks:")
        for i, chunk in enumerate(chunks):
            if len(chunk["chapter_numbers"]) == 1:
                chapter_info = f"Chapter {chunk['chapter_numbers'][0]}"
            else:
                chapter_info = f"Chapters {chunk['chapter_numbers'][0]}-{chunk['chapter_numbers'][-1]}"

            logger.info(
                f"  Chunk {i+1}: {chapter_info}, Range: {chunk['start_char']}-{chunk['end_char']}"
            )

        return chunks

    def _process_with_chapter_aligned_chunks(
        self,
        transcript_text: str,
        master_document: str,
        ai_processor: TranscriptProcessorInterface,
        config: Dict[str, Any],
    ) -> str:
        """
        Process the transcript using chunks aligned with chapter boundaries with flexible scaling.
        Includes improved length validation and adaptive retry logic.

        Args:
            transcript_text: The full transcript text
            master_document: The master document outlining the content
            ai_processor: The AI processor to use
            config: Configuration dictionary including target length

        Returns:
            The processed transcript as a string
        """
        logger.info("Using chapter-aligned chunking approach with flexible scaling")

        # Calculate original and target lengths
        original_length = len(transcript_text)
        target_length = config.get("ai", {}).get("length_in_chars", original_length)

        # Calculate scaling factor
        scaling_factor = target_length / original_length if original_length > 0 else 1.0

        # Extract structured prompt components
        prompt_role = config.get("ai", {}).get("prompt_role", "")
        prompt_script_structure = config.get("ai", {}).get("prompt_script_structure", "")
        prompt_tone_style = config.get("ai", {}).get("prompt_tone_style", "")
        prompt_retention_flow = config.get("ai", {}).get("prompt_retention_flow", "")
        prompt_additional_instructions = config.get("ai", {}).get("prompt_additional_instructions", "")
        
        # Get model from config
        model = config.get("ai", {}).get("model")

        logger.info(f"Original length: {original_length} characters")
        logger.info(f"Target length: {target_length} characters")
        logger.info(f"Scaling factor: {scaling_factor:.2f}x")

        # First, parse the master document to extract chapter information
        chapters = self._parse_master_document(master_document)

        if not chapters:
            logger.warning(
                "No chapters found in master document. Falling back to fixed-size chunking."
            )
            return self._process_chunks_with_continuity(
                transcript_text, master_document, ai_processor, config
            )

        logger.info(f"Found {len(chapters)} chapters in master document")

        # Create chapter-aligned chunks
        chapter_chunks = self._create_chapter_aligned_chunks(chapters, original_length)

        logger.info(f"Created {len(chapter_chunks)} chapter-aligned processing chunks")

        # Process each chunk with chapter-specific context
        processed_chunks = []
        chunks_info = []

        # Create chunks directory if output_dir is provided
        chunks_dir = None
        if self.output_dir:
            chunks_dir = os.path.join(self.output_dir, "chapter_chunks")
            os.makedirs(chunks_dir, exist_ok=True)

        for i, chunk in enumerate(chapter_chunks):
            chunk_index = i + 1
            total_chunks = len(chapter_chunks)
            is_last_chunk = i == len(chapter_chunks) - 1

            # Extract the relevant chunk of text
            start_char = chunk["start_char"]
            end_char = chunk["end_char"]
            chunk_text = transcript_text[start_char:end_char]
            input_length = len(chunk_text)

            # Calculate target length for this chunk based on scaling factor
            target_chunk_length = int(input_length * scaling_factor)

            # Ensure chunk doesn't exceed API limits
            if target_chunk_length > 20000:
                logger.warning(
                    f"Target chunk length {target_chunk_length} exceeds API limit. Capping at 20000 characters."
                )
                target_chunk_length = 20000

            # Set acceptable range with wider tolerance for condensation
            if scaling_factor < 0.7:  # For significant condensation
                min_target_length = int(
                    target_chunk_length * 0.7
                )  # 70% of target (more tolerant lower bound)
                max_target_length = int(
                    target_chunk_length * 1.3
                )  # 130% of target (more tolerant upper bound)
            elif scaling_factor > 1.3:  # For significant expansion
                min_target_length = int(target_chunk_length * 0.8)  # 80% of target
                max_target_length = int(target_chunk_length * 1.2)  # 120% of target
            else:  # For minor adjustments
                min_target_length = int(target_chunk_length * 0.9)  # 90% of target
                max_target_length = int(target_chunk_length * 1.1)  # 110% of target

            # Create dynamic instructions based on scaling factor
            if scaling_factor > 1.5:
                scaling_direction = "expansion"
                scaling_instruction = f"EXPAND the content to add more details, examples, and clearer explanations"
                detail_instruction = "ADD substantial details, examples, and explanations while maintaining accuracy"
            elif scaling_factor < 0.7:
                scaling_direction = "condensation"
                scaling_instruction = f"CONDENSE the content while preserving all key information and main points"
                detail_instruction = "FOCUS on the most important points and essential information without losing key content"
            else:
                scaling_direction = "adjustment"
                scaling_instruction = (
                    f"maintain similar content depth with some minor adjustments"
                )
                detail_instruction = "Maintain similar level of detail with minor adjustments to reach target length"

            # Create a description of the chapters in this chunk for logging
            if len(chunk["chapter_numbers"]) == 1:
                chapter_info = f"Chapter {chunk['chapter_numbers'][0]}"
            else:
                chapter_info = f"Chapters {chunk['chapter_numbers'][0]}-{chunk['chapter_numbers'][-1]}"

            logger.info(
                f"Processing {'FINAL ' if is_last_chunk else ''}chunk {chunk_index}/{total_chunks} containing {chapter_info}"
            )
            logger.info(
                f"Input size: {input_length} characters, Target size: {target_chunk_length} characters ({scaling_factor:.2f}x)"
            )

            # Determine continuation instructions based on position
            if i == 0:
                continuation_instructions = (
                    "This is the FIRST chunk. Begin your narrative from the start."
                )
                previous_context = ""
            else:
                continuation_instructions = f"This is chunk #{i+1}. CONTINUE the narrative seamlessly from the previous chunk. DO NOT repeat content from previous chunks."
                # Include a portion of the previous output for continuity
                previous_context = f"\nPREVIOUS CHUNK OUTPUT (ending):\n{processed_chunks[-1][-1000:]}\n"

            # Create chapter-specific instructions
            chapter_instructions = self._create_chapter_instructions(chunk)

            # Process the chunk
            success = False
            retries = 0
            processed_chunk = None
            retry_instruction = ""  # Start with no retry instruction

            while not success and retries < self.max_retries:
                try:
                    # Create the prompt with all necessary context and any retry instructions
                    prompt_with_context = CONTINUATION_PROMPT.format(
                        segment_number=i + 1,
                        total_segments=total_chunks,
                        master_document=master_document,
                        target_chunk_length=target_chunk_length,
                        min_target_length=min_target_length,
                        max_target_length=max_target_length,
                        scaling_factor=scaling_factor,
                        scaling_direction=scaling_direction,
                        scaling_instruction=scaling_instruction,
                        detail_instruction=detail_instruction,
                        continuation_instructions=continuation_instructions
                        + previous_context
                        + chapter_instructions,
                        input_length=input_length,
                        retry_instruction=retry_instruction,
                        role=prompt_role,
                        script_structure=prompt_script_structure,
                        tone_style=prompt_tone_style,
                        retention_flow=prompt_retention_flow,
                        additional_instructions=prompt_additional_instructions,
                    )

                    processed_chunk = process_llm(
                        context=chunk_text,
                        system_prompt=prompt_with_context,
                        model=model,  # Use model from config instead of hardcoded value
                        max_tokens=4096,
                        temperature=0.7,
                    )

                    # Log the output size
                    output_length = len(processed_chunk)
                    logger.info(
                        f"Chunk {i+1} processed [OUTPUT SIZE: {output_length} characters]"
                    )
                    logger.info(
                        f"Target was {target_chunk_length} characters (Range: {min_target_length}-{max_target_length})"
                    )

                    # Validate output length against target
                    if output_length < min_target_length:
                        logger.warning(
                            f"Processed chunk {i+1} is too short ({output_length} chars vs target min {min_target_length}). Retrying."
                        )

                        # Update retry instruction to guide the model to produce a longer output
                        length_diff = min_target_length - output_length
                        percentage_diff = int((length_diff / target_chunk_length) * 100)
                        retry_instruction = f"RETRY INSTRUCTION: Your previous output was TOO SHORT ({output_length} characters). You need to make this output LONGER by approximately {percentage_diff}% or {length_diff} characters. Include more details, examples, or explanations while maintaining the same quality."

                        retries += 1
                        continue

                    # Only enforce maximum length for non-last chunks
                    if not is_last_chunk and output_length > max_target_length:
                        logger.warning(
                            f"Processed chunk {i+1} is too long ({output_length} chars vs target max {max_target_length}). Retrying."
                        )

                        # Update retry instruction to guide the model to produce a shorter output
                        length_diff = output_length - max_target_length
                        percentage_diff = int((length_diff / target_chunk_length) * 100)
                        retry_instruction = f"RETRY INSTRUCTION: Your previous output was TOO LONG ({output_length} characters). You need to make this output SHORTER by approximately {percentage_diff}% or {length_diff} characters. Be more concise while retaining all key information."

                        retries += 1
                        continue

                    # If we get here, the chunk is valid
                    success = True
                    processed_chunks.append(processed_chunk)

                    # Record chunk info
                    # Record chunk info
                    chunks_info.append(
                        {
                            "chunk_index": i,
                            "chapters": chunk["chapter_numbers"],
                            "original_length": input_length,
                            "target_length": target_chunk_length,
                            "processed_length": output_length,
                            "scaling_factor": scaling_factor,
                            "actual_ratio": (
                                output_length / input_length if input_length > 0 else 0
                            ),
                            "within_target_range": min_target_length
                            <= output_length
                            <= max_target_length,
                            "start_char": start_char,
                            "end_char": end_char,
                            "is_last_chunk": is_last_chunk,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {e}")
                    retries += 1
                    time.sleep(2)  # Wait before retry

            # If all retries failed, use fallback processing
            if not success:
                logger.warning(
                    f"All retries failed for chunk {i+1}. Using simplified processing."
                )
                # Try with a simpler prompt as fallback
                try:
                    simple_prompt = create_simplified_fallback_prompt(
                        chunk_text=chunk_text,
                        target_length=target_chunk_length,
                        scaling_factor=scaling_factor,
                        previous_output_length=(
                            len(processed_chunk) if processed_chunk else 0
                        ),
                        chapter_info=chapter_info,
                    )

                    processed_chunk = process_llm(
                        context=chunk_text,
                        system_prompt=simple_prompt,
                        model=model,  # Use model from config instead of hardcoded value
                        max_tokens=4096,
                        temperature=0.7,
                    )

                    output_length = len(processed_chunk)
                    logger.info(
                        f"Chunk {i+1} processed with simplified prompt [OUTPUT SIZE: {output_length} characters]"
                    )

                    processed_chunks.append(processed_chunk)

                    # Record chunk info
                    chunks_info.append(
                        {
                            "chunk_index": i,
                            "chapters": chunk["chapter_numbers"],
                            "original_length": input_length,
                            "target_length": target_chunk_length,
                            "processed_length": output_length,
                            "scaling_factor": scaling_factor,
                            "actual_ratio": (
                                output_length / input_length if input_length > 0 else 0
                            ),
                            "simplified": True,
                        }
                    )

                except Exception as e:
                    # If even that fails, just use original with a note
                    logger.error(
                        f"Simplified processing failed for chunk {i+1}. Using original with note: {e}"
                    )
                    processed_chunk = f"[Processing failed for this section. Original content preserved.]\n\n{chunk_text}"
                    processed_chunks.append(processed_chunk)

                    # Record chunk info
                    chunks_info.append(
                        {
                            "chunk_index": i,
                            "chapters": chunk["chapter_numbers"],
                            "original_length": input_length,
                            "target_length": target_chunk_length,
                            "processed_length": len(processed_chunk),
                            "scaling_factor": scaling_factor,
                            "actual_ratio": 1.0,  # Just preserving original
                            "preserved_original": True,
                        }
                    )

            # Save the processed chunk if output_dir is provided
            if chunks_dir and processed_chunk:
                chunk_path = os.path.join(
                    chunks_dir, f"processed_chapter_chunk_{i+1}.txt"
                )
                with open(chunk_path, "w", encoding="utf-8") as f:
                    f.write(processed_chunk)

        # Calculate and log processing statistics
        if chunks_info:
            original_total = sum(info.get("original_length", 0) for info in chunks_info)
            target_total = sum(info.get("target_length", 0) for info in chunks_info)
            processed_total = sum(
                info.get("processed_length", 0) for info in chunks_info
            )

            logger.info(f"Chapter-aligned chunking processing completed:")
            logger.info(f"  - Original text: {original_total:,} characters")
            logger.info(
                f"  - Target text: {target_total:,} characters ({scaling_factor:.2f}x)"
            )
            logger.info(
                f"  - Processed text: {processed_total:,} characters ({processed_total/original_total:.2f}x)"
            )
            logger.info(
                f"  - Target ratio: {scaling_factor:.2f}x, Actual ratio: {processed_total/original_total:.2f}x"
            )

        # Join all processed chunks to form the final transcript
        final_transcript = "\n\n".join(processed_chunks)

        # Clean up any formatting issues
        final_transcript = re.sub(r"\n{3,}", "\n\n", final_transcript)

        return final_transcript

    def _extract_title_from_text(self, text: str) -> str:
        """Extract a meaningful title from text."""
        # Simple implementation - use first sentence or first 50 chars
        first_part = text.split(".")[0].strip()
        if len(first_part) > 50:
            return first_part[:50] + "..."
        return first_part

    def _process_chunks_with_continuity(
        self,
        transcript_text: str,
        master_document: str,
        ai_processor: TranscriptProcessorInterface,
        config: Dict[str, Any] = None,
    ) -> str:
        """
        Process the transcript in fixed-size chunks while maintaining continuity between chunks.
        This method is used as a fallback when chapter-aligned chunking is disabled.

        Args:
            transcript_text: The full transcript text
            master_document: The master document outlining the content
            ai_processor: The AI processor to use
            config: Configuration dictionary including target length and prompt components

        Returns:
            The processed transcript as a string
        """
        # Extract structured prompt components
        prompt_role = config.get("ai", {}).get("prompt_role", "")
        prompt_script_structure = config.get("ai", {}).get(
            "prompt_script_structure", ""
        )
        prompt_tone_style = config.get("ai", {}).get("prompt_tone_style", "")
        prompt_retention_flow = config.get("ai", {}).get("prompt_retention_flow", "")
        prompt_additional_instructions = config.get("ai", {}).get(
            "prompt_additional_instructions", ""
        )
        
        # Get model from config
        model = config.get("ai", {}).get("model")

        # Split into processing chunks (20K characters each)
        chunks = []
        for i in range(0, len(transcript_text), self.chunk_size):
            end_idx = min(i + self.chunk_size, len(transcript_text))
            chunks.append(transcript_text[i:end_idx])

        total_chunks = len(chunks)
        logger.info(
            f"Split transcript into {total_chunks} fixed-size processing chunks"
        )

        # Process each chunk with continuity
        processed_chunks = []
        chunks_info = []

        # Create chunks directory if output_dir is provided
        chunks_dir = None
        if self.output_dir:
            chunks_dir = os.path.join(self.output_dir, "chunks")
            os.makedirs(chunks_dir, exist_ok=True)
            logger.info(f"Created directory for individual chunks: {chunks_dir}")

            # Save original chunks
            for i, chunk in enumerate(chunks):
                original_chunk_path = os.path.join(
                    chunks_dir, f"original_chunk_{i+1}.txt"
                )
                with open(original_chunk_path, "w", encoding="utf-8") as f:
                    f.write(chunk)

        for i, chunk in enumerate(chunks):
            chunk_length = len(chunk)
            is_last_chunk = i == total_chunks - 1

            if is_last_chunk:
                logger.info(
                    f"Processing FINAL chunk {i+1}/{total_chunks} [INPUT SIZE: {chunk_length} characters]"
                )
            else:
                logger.info(
                    f"Processing chunk {i+1}/{total_chunks} [INPUT SIZE: {chunk_length} characters]"
                )

            # Determine continuation instructions based on position
            if i == 0:
                continuation_instructions = (
                    "This is the FIRST chunk. Begin your narrative from the start."
                )
                previous_context = ""
            else:
                continuation_instructions = f"This is chunk #{i+1}. CONTINUE the narrative seamlessly from the previous chunk. DO NOT repeat content from previous chunks."
                # Include a portion of the previous output for continuity
                previous_context = f"\nPREVIOUS CHUNK OUTPUT (ending):\n{processed_chunks[-1][-1000:]}\n"

            # Calculate character positions for this chunk
            start_char = i * self.chunk_size
            end_char = min(start_char + self.chunk_size, len(transcript_text))

            # Calculate target length and scaling factor
            if config and "ai" in config and "length_in_chars" in config["ai"]:
                target_length = config["ai"]["length_in_chars"]
                original_length = len(transcript_text)
                scaling_factor = (
                    target_length / original_length if original_length > 0 else 1.0
                )
                target_chunk_length = int(chunk_length * scaling_factor)

                # Set appropriate min/max target lengths
                if scaling_factor < 0.7:  # For significant condensation
                    min_target_length = int(target_chunk_length * 0.7)
                    max_target_length = int(target_chunk_length * 1.3)
                elif scaling_factor > 1.3:  # For significant expansion
                    min_target_length = int(target_chunk_length * 0.8)
                    max_target_length = int(target_chunk_length * 1.2)
                else:  # For minor adjustments
                    min_target_length = int(target_chunk_length * 0.9)
                    max_target_length = int(target_chunk_length * 1.1)

                # Create dynamic instructions based on scaling factor
                if scaling_factor > 1.5:
                    scaling_direction = "expansion"
                    scaling_instruction = f"EXPAND the content to add more details, examples, and clearer explanations"
                    detail_instruction = "ADD substantial details, examples, and explanations while maintaining accuracy"
                elif scaling_factor < 0.7:
                    scaling_direction = "condensation"
                    scaling_instruction = f"CONDENSE the content while preserving all key information and main points"
                    detail_instruction = "FOCUS on the most important points and essential information without losing key content"
                else:
                    scaling_direction = "adjustment"
                    scaling_instruction = (
                        f"maintain similar content depth with some minor adjustments"
                    )
                    detail_instruction = "Maintain similar level of detail with minor adjustments to reach target length"
            else:
                # Default values if no target length is specified
                target_chunk_length = chunk_length
                min_target_length = int(chunk_length * 0.8)
                max_target_length = int(chunk_length * 1.2)
                scaling_factor = 1.0
                scaling_direction = "adjustment"
                scaling_instruction = "maintain similar content depth"
                detail_instruction = "Maintain the same level of detail"

            # Create the prompt with all necessary context
            prompt_with_context = CONTINUATION_PROMPT.format(
                segment_number=i + 1,
                total_segments=total_chunks,
                master_document=master_document,
                target_chunk_length=target_chunk_length,
                min_target_length=min_target_length,
                max_target_length=max_target_length,
                scaling_factor=scaling_factor,
                scaling_direction=scaling_direction,
                scaling_instruction=scaling_instruction,
                detail_instruction=detail_instruction,
                continuation_instructions=continuation_instructions + previous_context,
                input_length=chunk_length,
                retry_instruction="",
                role=prompt_role,
                script_structure=prompt_script_structure,
                tone_style=prompt_tone_style,
                retention_flow=prompt_retention_flow,
                additional_instructions=prompt_additional_instructions,
            )

            # Log first 200 characters of the prompt
            prompt_preview = prompt_with_context[:200].replace("\n", " ").strip()
            logger.info(f'System prompt: "{prompt_preview}..."')

            # Save the complete prompt used for this chunk if output_dir is provided
            if chunks_dir:
                prompt_path = os.path.join(chunks_dir, f"prompt_chunk_{i+1}.txt")
                with open(prompt_path, "w", encoding="utf-8") as f:
                    f.write(prompt_with_context)

            # Process the chunk
            success = False
            retries = 0
            processed_chunk = None

            while not success and retries < self.max_retries:
                try:
                    processed_chunk = process_llm(
                        context=chunk,
                        system_prompt=prompt_with_context,
                        model=model,  # Use model from config
                        max_tokens=4096,
                        temperature=0.7,
                    )

                    # Log the output size
                    output_length = len(processed_chunk)
                    logger.info(
                        f"Chunk {i+1} processed [OUTPUT SIZE: {output_length} characters]"
                    )

                    # Calculate expected minimum length based on input size
                    # For small chunks, expect at least 80% of input length
                    # For larger chunks, use the configured minimum length
                    expected_min_length = min(
                        self.min_output_length, max(int(chunk_length * 0.8), 1000)
                    )

                    # Validate output length
                    if output_length < min_target_length:
                        logger.warning(
                            f"Processed chunk {i+1} is too short ({output_length} chars vs expected min {min_target_length}). Retrying."
                        )
                        retries += 1
                        continue

                    # Only enforce maximum length for reasonably sized inputs and NOT for the last chunk
                    # Last chunk can be any size, so we skip maximum length validation for it
                    if not is_last_chunk and output_length > max_target_length:
                        logger.warning(
                            f"Processed chunk {i+1} is too long ({output_length} chars vs expected max {max_target_length}). Retrying."
                        )
                        retries += 1
                        continue

                    # If we get here, the chunk is valid
                    success = True
                    processed_chunks.append(processed_chunk)

                    # Record chunk info
                    chunks_info.append(
                        {
                            "chunk_index": i,
                            "original_length": chunk_length,
                            "target_length": target_chunk_length,
                            "processed_length": output_length,
                            "scaling_factor": scaling_factor,
                            "actual_ratio": (
                                output_length / chunk_length if chunk_length > 0 else 0
                            ),
                            "start_char": start_char,
                            "end_char": end_char,
                            "is_last_chunk": is_last_chunk,
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {e}")
                    retries += 1
                    time.sleep(2)  # Wait before retry

                # If all retries failed, use a placeholder or simplified version
            # If all retries failed, use a placeholder or simplified version
            if not success:
                logger.warning(
                    f"All retries failed for chunk {i+1}. Using simplified processing."
                )
                # Try with a simpler prompt as fallback
                try:
                    simple_prompt = create_simplified_fallback_prompt(
                        chunk_text=chunk,
                        target_length=target_chunk_length,
                        scaling_factor=scaling_factor,
                    )

                    simplified_prompt = simple_prompt[:200].replace("\n", " ").strip()
                    logger.info(
                        f'Using simplified prompt (first 200 chars): "{simplified_prompt}..."'
                    )

                    # Save the simplified prompt if output_dir is provided
                    if chunks_dir:
                        simplified_prompt_path = os.path.join(
                            chunks_dir, f"simplified_prompt_chunk_{i+1}.txt"
                        )
                        with open(simplified_prompt_path, "w", encoding="utf-8") as f:
                            f.write(simple_prompt)

                    processed_chunk = process_llm(
                        context=chunk,
                        system_prompt=simple_prompt,
                        model=model,  # Use model from config instead of hardcoded value
                        max_tokens=4096,
                        temperature=0.7,
                    )

                    logger.info(
                        f"Chunk {i+1} processed with simplified prompt [OUTPUT SIZE: {len(processed_chunk)} characters]"
                    )

                    processed_chunks.append(processed_chunk)

                    # Record chunk info
                    chunks_info.append(
                        {
                            "chunk_index": i,
                            "original_length": chunk_length,
                            "target_length": target_chunk_length,
                            "processed_length": len(processed_chunk),
                            "scaling_factor": scaling_factor,
                            "actual_ratio": (
                                len(processed_chunk) / chunk_length
                                if chunk_length > 0
                                else 0
                            ),
                            "start_char": start_char,
                            "end_char": end_char,
                            "simplified": True,
                        }
                    )

                except Exception as e:
                    # If even that fails, just use original with a note
                    logger.error(
                        f"Simplified processing failed for chunk {i+1}. Using original with note: {e}"
                    )
                    processed_chunk = f"[Processing failed for this section. Original content preserved.]\n\n{chunk}"
                    processed_chunks.append(processed_chunk)

                    # Record chunk info
                    chunks_info.append(
                        {
                            "chunk_index": i,
                            "original_length": chunk_length,
                            "target_length": target_chunk_length,
                            "processed_length": len(processed_chunk),
                            "scaling_factor": scaling_factor,
                            "actual_ratio": (
                                len(processed_chunk) / chunk_length
                                if chunk_length > 0
                                else 0
                            ),
                            "start_char": start_char,
                            "end_char": end_char,
                            "preserved_original": True,
                        }
                    )

            # Save the processed chunk if output_dir is provided
            if chunks_dir and processed_chunk:
                chunk_path = os.path.join(chunks_dir, f"processed_chunk_{i+1}.txt")
                with open(chunk_path, "w", encoding="utf-8") as f:
                    f.write(processed_chunk)
                logger.info(f"Saved processed chunk {i+1} to {chunk_path}")

        # Save chunks info
        if self.output_dir:
            chunks_info_path = os.path.join(self.output_dir, "chunks_info.json")
            with open(chunks_info_path, "w", encoding="utf-8") as f:
                json.dump(chunks_info, f, indent=2)
            logger.info(f"Saved chunks info to {chunks_info_path}")

        # Combine all processed chunks into a single transcript
        processed_transcript = "\n\n".join(processed_chunks)

        # Clean up any formatting issues
        processed_transcript = re.sub(r"\n{3,}", "\n\n", processed_transcript)

        return processed_transcript


def process_large_transcript(
    transcript_text: str,
    config: Dict[str, Any],
    mock_mode: bool = False,
    output_dir: str = None,
    json_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Process a large transcript by creating a master document and then processing chunks with continuity.

    Args:
        transcript_text: The full transcript text to process
        config: Configuration dictionary for the processor
        mock_mode: If True, simulates processing without making actual API calls
        output_dir: Optional directory to save individual chunks and master document
        json_data: Optional JSON data containing additional information

    Returns:
        The processed transcript text
    """
    # Import here to avoid circular imports
    from .gemini_processor import GeminiProcessor

    # Before processing, extract prompt fields from json_data if available
    # and add them to the config
    if json_data and "promptData" in json_data:
        prompt_data = json_data.get("promptData", {})

        # If the ai section doesn't exist in config, create it
        if "ai" not in config:
            config["ai"] = {}

        # Map each prompt field to config
        config["ai"]["prompt_role"] = prompt_data.get("yourRole", "")
        config["ai"]["prompt_script_structure"] = prompt_data.get("scriptStructure", "")
        config["ai"]["prompt_tone_style"] = prompt_data.get("toneAndStyle", "")
        config["ai"]["prompt_retention_flow"] = prompt_data.get("retentionAndFlow", "")
        config["ai"]["prompt_additional_instructions"] = prompt_data.get(
            "additionalInstructions", ""
        )

    processor = ChunkedProcessor(config)
    # ai_processor = GeminiProcessor(config)
    ai_processor = None
    return processor.process(
        transcript_text,
        ai_processor,
        mock_mode=mock_mode,
        output_dir=output_dir,
        config=config,
    )
