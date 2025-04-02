"""
Custom Prompt Templates Module

This module contains helper functions for generating structured prompts
for use in the transcript processing pipeline.
"""

import os

def create_master_document_for_expansion_prompt(transcript_text, target_length, chapter_number, segment_text, master_document=None):
    """
    Creates a structured prompt for expanding a chapter from a small segment of text.
    
    Args:
        transcript_text: Full transcript text (for context)
        target_length: Target character length for the expanded chapter
        chapter_number: The chapter number to assign
        segment_text: The specific text segment to expand
        master_document: The master document containing topic outlines (optional)
        
    Returns:
        A formatted prompt template with placeholders for prompt components
    """

    import os
    # Calculate expansion ratio
    expansion_ratio = target_length / len(segment_text) if len(segment_text) > 0 else 0
    min_target_length = int(target_length)
    max_target_length = int(target_length * 1.4)
    
    # Extract relevant portion of master document for this chapter if provided
    master_doc_extract = ""
    if master_document:
        # Try to extract just the relevant chapter section from the master document
        chapter_marker = f"## Chapter {chapter_number}:"
        next_chapter_marker = f"## Chapter {chapter_number + 1}:"
        
        if chapter_marker in master_document:
            start_idx = master_document.find(chapter_marker)
            if next_chapter_marker in master_document[start_idx:]:
                end_idx = master_document.find(next_chapter_marker, start_idx)
                master_doc_extract = master_document[start_idx:end_idx].strip()
            else:
                # If this is the last chapter, extract to the end
                master_doc_extract = master_document[start_idx:].strip()
        
        # If we couldn't extract the specific chapter, use the whole document
        if not master_doc_extract:
            master_doc_extract = master_document
    
    return f"""
# CHAPTER EXPANSION DIRECTIVE

## MASTER DOCUMENT OUTLINE
{master_doc_extract if master_doc_extract else "Create an engaging and detailed chapter based on the provided segment."}

## YOUR ROLE
{{role}}

## LENGTH REQUIREMENT
Your output MUST be at least {target_length} characters.

## CONTEXT & INPUT DETAILS
- ORIGINAL SEGMENT: {len(segment_text)} characters
- TARGET OUTPUT: {target_length} characters
- EXPANSION FACTOR: {expansion_ratio:.2f}x
- You are creating Chapter {chapter_number} ONLY in this response

## REASONING ABOUT EXPANSION
This task requires significant expansion of the original text. Consider:
1. The original segment is {len(segment_text)} characters
2. The target output is {target_length} characters
3. This means adding approximately {target_length - len(segment_text)} new characters
4. To achieve this, you must add substantial detail, examples, and descriptive content
5. Each topic from the master document should be thoroughly developed
6. You must maintain the core message while adding depth and richness

## YOUR TASK
1. Create "Chapter {chapter_number}" followed by an engaging title
2. EXPAND this content into a SINGLE, comprehensive chapter following the master document outline
3. The chapter should be detailed, engaging, and exactly {target_length} characters
4. Cover ALL topics mentioned in the master document outline for this chapter

## SCRIPT STRUCTURE
{{script_structure}}

## TONE & STYLE
{{tone_style}}

## RETENTION & FLOW TECHNIQUES
{{retention_flow}}

## ADDITIONAL INSTRUCTIONS
{{additional_instructions}}

## OUTPUT STRUCTURE
- Start with "Chapter {chapter_number}: [Your Engaging Title]"
- Organize content into logical sections with clear topic progression
- Include an introduction that sets up the chapter themes
- Develop each topic with multiple paragraphs of detailed content
- Conclude by summarizing key points and transitioning to the next chapter


## FORMATTING INSTRUCTIONS - FOLLOW EXACTLY
1. Format each complete sentence as follows:
   - End each sentence with a period (.)
   - Follow EACH sentence with TWO newlines (a blank line between sentences)
   - Example:
     "This is the first sentence."

     "This is the second sentence."

     "This is the third sentence."

2. Do NOT start a new line for commas, only for completed sentences
3. Use plain text only - no special characters, markdown, or formatting symbols
4. Avoid using brackets [], parentheses (), or other special formatting
5. This will be put in a TTS model, so prioritize natural speech patterns
6. DO NOT MAKE USE OF * [] () or other special characters only a - , . are allowed
7. For SUBCHAPTERS within a chapter, format like - Subchapter Title -   DO not number them
    eg: - The Importance of Sleep -
8. Do not put more than 3 subchapters in a chapter



## OUTPUT LENGTH VERIFICATION PROCESS
1. Count the exact number of characters in your response
2. Verify it is between {min_target_length} and {max_target_length} characters OR at least {min_target_length % 4} Words.
3. If too short: Add more descriptive details to reach target length
4. If too long: Trim less essential details while preserving core content


## IF YOU ARE HAVING TROUBLE WITH THE TARGET LENGTH:
1. Fill up the output with more sub topic related to the topics outlines in the master document
2. If you are still short, add more details 



CRITICAL: Your response will be REJECTED if not within {min_target_length}-{max_target_length} characters.
Current segment length: {len(segment_text)} characters
Target chapter length: EXACTLY {target_length} characters
Required expansion factor: {expansion_ratio:.1f}x

MOST CRITICAL:
- [Final reminder: GENERATE AT LEAST {target_length} CHARACTERS but preferably more!!]
- DO NOT MAKE USE OF * [] () or other special characters only a - , . are allowed
- This transcript will be read out by a Text To Speech model SO WRITE LIKE SOMEONE WOULD SPEAK/READ.
"""

def create_simplified_fallback_prompt(chunk_text, target_length, scaling_factor, 
                                    previous_output_length=0, chapter_info="this section"):
    """
    Creates a simplified fallback prompt for when regular processing fails.
    
    Args:
        chunk_text: The text chunk to process
        target_length: Target output length in characters
        scaling_factor: The scaling factor (ratio of target to original length)
        previous_output_length: Length of the previous failed output
        chapter_info: Description of the chapter content
        
    Returns:
        A simplified prompt string
    """
    # Set acceptable range with wider tolerance for condensation
    if scaling_factor < 0.7:  # For significant condensation
        min_target_length = int(target_length * 0.7)
        max_target_length = int(target_length * 1.3)
        acceptable_variation_percent = 30
    elif scaling_factor > 1.3:  # For significant expansion
        min_target_length = int(target_length * 0.8)
        max_target_length = int(target_length * 1.2)
        acceptable_variation_percent = 20
    else:  # For minor adjustments
        min_target_length = int(target_length * 0.9)
        max_target_length = int(target_length * 1.1)
        acceptable_variation_percent = 10
    
    previous_length_issue = "short" if previous_output_length < min_target_length else "long"
    
    # Determine scaling direction
    if scaling_factor > 1.2:
        scaling_direction = "expansion"
        scaling_instruction = f"EXPAND the content to add more details and examples"
    elif scaling_factor < 0.8:
        scaling_direction = "condensation"
        scaling_instruction = f"CONDENSE the content while preserving key information"
    else:
        scaling_direction = "adjustment"
        scaling_instruction = f"maintain similar content with minor adjustments"
    
    return f"""
# SIMPLIFIED PROCESSING INSTRUCTION

## LENGTH REQUIREMENT
Your output MUST be {target_length} characters (range: {min_target_length}-{max_target_length})

## CONTENT DETAILS
This section contains {chapter_info}.

## YOUR TASK
1. Your output MUST be {target_length} characters ({scaling_factor:.2f}x the input length)
2. This is a {scaling_factor:.2f}x {scaling_direction} process
3. You need to {scaling_instruction}

## FORMATTING INSTRUCTIONS
- Include chapter headings (e.g., "Chapter 1", "Chapter 2") if they appear in the text
- Use proper paragraphs and punctuation
- Remove speech disfluencies ("um", "uh", repetitive phrases)

{f"IMPORTANT: Your last output was too {previous_length_issue} at {previous_output_length} characters." if previous_output_length > 0 else ""}

CRITICAL: Your response will be REJECTED if not between {min_target_length} and {max_target_length} characters.
If you're struggling with the target length, aim exactly for {target_length} characters.


CRITICAL
[Final reminder: GENERATE AT LEAST {target_length} CHARACTERS but preferably more!!]
"""