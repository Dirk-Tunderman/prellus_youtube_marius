# PROMPT_INFRASTRUCTURE.md

This document provides a comprehensive overview of the prompt infrastructure used in the YouTube Transcript Processor's story generation system.

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Prompt Types and Usage](#prompt-types-and-usage)
3. [Complete Prompt Templates](#complete-prompt-templates)
4. [Length Handling Examples](#length-handling-examples)
5. [Model-Specific Behaviors](#model-specific-behaviors)
6. [Dynamic Features](#dynamic-features)

## System Architecture Overview

The story generation system uses a **Response-Aware Processing System** with the following key components:

### Processing Flow
```
Input → Master Document Creation → Response Planning → Sequential Generation → Catch-up (if needed) → Final Output
```

### Key Innovations
1. **Master Document with Response Planning**: Creates a structured plan before generation
2. **Dynamic Length Calculation**: Based on duration, speed, and TTS reading rates
3. **Response-Aware Generation**: Each response knows its position in the overall narrative
4. **Catch-up System**: Ensures precise length targeting with additional generation rounds

## Prompt Types and Usage

The system uses **5 main prompt types**:

| Prompt Type | When Used | Purpose |
|------------|-----------|---------|
| **Master Document Creation** | Start of processing | Plans entire content structure and response breakdown |
| **Response Generation** | For each response chunk | Generates specific portion of content |
| **Catch-up Generation** | When response falls short | Fills deficit to meet length requirements |
| **TTS Formatting Rules** | All generation prompts | Ensures output is TTS-ready |
| **User Instructions** | All prompts | Integrates custom user requirements |

## Complete Prompt Templates

### 1. Master Document Creation Prompt

This prompt is used in `_build_master_document_prompt()` (lines 266-357 in simple_processor.py):

```python
# MASTER DOCUMENT CREATION WITH RESPONSE PLANNING

## TARGET SPECIFICATIONS
- Total Length: {target_length:,} characters
- Duration: ~{target_length // (180 * 4.7):.1f} minutes
- Responses Needed: {response_plan['responses_needed']}

## RESPONSE BREAKDOWN
You need to structure content for {response_plan['responses_needed']} responses:

### Response {plan['response_num']} - CHARACTER RANGE: {start_char:,} to {end_char:,}
- **Target Length**: {plan['target_chars']:,} characters ({plan['percentage_of_total']:.1f}% of total)
- **Time Range**: {start_minutes:.1f} to {end_minutes:.1f} minutes of final content
- **Content Sections**: [YOU MUST SPECIFY which parts/chapters/sections go in this character range]
- **Character Breakdown**: [YOU MUST break down how characters are distributed within this response]

## USER-PROVIDED STRUCTURE (IMPORTANT - USE THIS)
{user_instructions['script_structure']}

**TASK**: Adapt the above user structure to fit the {response_plan['responses_needed']} response breakdown.
Map user's chapters/sections to specific responses.

## USER INSTRUCTIONS
**Role:** {user_instructions['role']}
**Tone & Style:** {user_instructions['tone_style'] or "Professional, engaging narrative style"}
**Additional:** {user_instructions['additional_instructions'] or "None specified"}

## ORIGINAL TRANSCRIPT
{transcript_text[:10000]}{"..." if len(transcript_text) > 10000 else ""}

## OUTPUT REQUIREMENTS
Create a master document that:

**CRITICAL - SECTION BREAKDOWN REQUIRED:**
1. Map your provided structure to the response breakdown above
2. **For EACH Response, specify EXACTLY:**
   - Which sections/parts/chapters go in that character range
   - Approximate character allocation per section within that response
   - Key content points for each section
   - Transition points between responses

**EXAMPLE FORMAT (adapt to your content):**
```
Response 1 (0-50,000 characters):
- Introduction Section (0-15,000 chars): Opening hook, context setting
- Main Point 1 (15,000-35,000 chars): Core concept explanation
- Transition (35,000-50,000 chars): Bridge to next response

Response 2 (50,000-100,000 characters):
- Main Point 2 (50,000-75,000 chars): Deep dive into topic
- Examples Section (75,000-100,000 chars): Case studies and examples
```

3. Ensure smooth narrative flow across all responses
4. Maintain the user's specified tone and style throughout
5. **MOST IMPORTANT**: Be specific about character allocation - don't be vague!

Generate the master document now with explicit section breakdown.
```

### 2. Response Generation Prompt

This prompt is used in `_build_response_prompt()` (lines 669-776 in simple_processor.py):

```python
# RESPONSE {response_num} OF {response_plan['responses_needed']} GENERATION

## PROGRESS STATUS
- Current Response: {response_num}/{response_plan['responses_needed']}
- Target This Response: {target_chars:,} characters
- Generated So Far: {len(previous_content):,} characters
- Overall Target: {response_plan['total_target']:,} characters

## MASTER DOCUMENT
{master_document}

## USER INSTRUCTIONS (MAINTAIN THROUGHOUT)
**Role:** {user_instructions['role']}
**Tone & Style:** {user_instructions['tone_style'] or "Professional, engaging narrative style"}
**Additional:** {user_instructions['additional_instructions'] or "None specified"}

## CONTEXT
{"This is the FIRST response - begin the narrative" if response_num == 1 else f"Previous content (last 2000 chars): ...{previous_content[-2000:]}"}

## TTS OUTPUT INSTRUCTIONS (CRITICAL)
You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Follow these strict formatting rules:

**Mandatory Requirements:**

Text Content Rules:
- Output ONLY the actual spoken words - no descriptions, actions, or meta-text
- NEVER include stage directions like *laughs*, [pause], (sighs), ::thinking::, or any text in brackets, parentheses, or asterisks
- NEVER use formatting markers such as **bold**, *italics*, or any markdown/HTML
- Write everything exactly as it should be pronounced out loud

Number and Symbol Conversion:
- Spell out ALL numbers as words: 3 → "three", 2025 → "two thousand twenty-five"
- Convert ALL symbols to words: @ → "at", # → "hashtag", % → "percent", & → "and"

Abbreviation and Acronym Handling:
- Expand ALL abbreviations: Dr. → "Doctor", vs. → "versus", etc. → "et cetera"
- For acronyms, spell them out with spaces: FBI → "F B I"

Sentence Structure:
- Keep sentences under 25 words when possible
- Use periods for clear stops, commas for natural breathing points
- Break complex ideas into multiple simple sentences

**Forbidden Elements - You must NEVER include:**
- Text within asterisks: *any text*
- Text within brackets: [any text]
- Text within parentheses for asides: (any text)
- Bullet points or numbered lists
- Sound effect descriptions
- Action or emotional descriptions

## YOUR TASK
Generate Response {response_num} content following the master document plan.

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
```

### 3. Catch-up Generation Prompt

This prompt is used in `_build_catch_up_prompt()` (lines 587-667 in simple_processor.py):

```python
# CATCH-UP CONTENT GENERATION

## TTS OUTPUT INSTRUCTIONS (CRITICAL)
You must generate text that will be read aloud by a Text-to-Speech (TTS) system. Follow these strict formatting rules:

**Mandatory Requirements:**
- Output ONLY the actual spoken words - no descriptions, actions, or meta-text
- NEVER include stage directions like *laughs*, [pause], (sighs), ::thinking::, or any text in brackets, parentheses, or asterisks
- NEVER use formatting markers such as **bold**, *italics*, or any markdown/HTML
- Write everything exactly as it should be pronounced out loud
- Spell out ALL numbers as words: 3 → "three", 2025 → "two thousand twenty-five"
- Convert ALL symbols to words: @ → "at", # → "hashtag", % → "percent", & → "and"
- Expand ALL abbreviations: Dr. → "Doctor", vs. → "versus", etc. → "et cetera"

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
5. **NO REPETITION** - Don't repeat what was already said
6. **NATURAL FLOW** - Content should feel like a natural continuation

**🔍 MANDATORY CATCH-UP VERIFICATION:**
1. Count the EXACT number of characters in your catch-up response
2. Is it AT LEAST {deficit:,} characters? If NO, ADD MORE CONTENT IMMEDIATELY
3. Is it between {deficit:,} and {int(deficit * 1.2):,} characters? If NO, adjust
4. Does it continue seamlessly from previous content? If NO, fix the transition
5. If you submit less than {deficit:,} characters, the catch-up has FAILED

🚨 **REMEMBER: {deficit:,} CHARACTERS IS THE ABSOLUTE MINIMUM FOR THIS CATCH-UP** 🚨

🚨 **GENERATE CATCH-UP CONTENT NOW - MINIMUM {deficit:,} CHARACTERS REQUIRED** 🚨

**FINAL REMINDER: Your catch-up must be AT LEAST {deficit:,} characters. Anything less means the catch-up failed.**
```

### 4. User Instructions Structure

User instructions are extracted from the structured prompt data and integrated into all generation prompts:

```python
# User instruction fields (from _extract_user_instructions())
{
    "role": "You are an expert writer tasked with processing transcript content.",
    "script_structure": "User-provided chapter/section structure",
    "tone_style": "Professional, engaging narrative style",
    "retention_flow": "Maintain engaging flow throughout",
    "additional_instructions": "Any additional requirements"
}
```

### 5. TTS Formatting Rules

Applied to ALL generation prompts to ensure TTS-ready output:

```
## TTS OUTPUT INSTRUCTIONS (CRITICAL)

**Mandatory Requirements:**

Text Content Rules:
- Output ONLY the actual spoken words - no descriptions, actions, or meta-text
- NEVER include stage directions like *laughs*, [pause], (sighs), ::thinking::
- NEVER use formatting markers such as **bold**, *italics*, or any markdown/HTML
- Write everything exactly as it should be pronounced out loud

Number and Symbol Conversion:
- Spell out ALL numbers as words: 3 → "three", 2025 → "two thousand twenty-five"
- Convert ALL symbols to words: @ → "at", # → "hashtag", % → "percent", & → "and"

Abbreviation and Acronym Handling:
- Expand ALL abbreviations: Dr. → "Doctor", vs. → "versus", etc. → "et cetera"
- For acronyms, spell them out with spaces: FBI → "F B I"

Sentence Structure:
- Keep sentences under 25 words when possible
- Use periods for clear stops, commas for natural breathing points
- Break complex ideas into multiple simple sentences

**Forbidden Elements:**
- Text within asterisks: *any text*
- Text within brackets: [any text]
- Text within parentheses for asides: (any text)
- Bullet points or numbered lists
- Sound effect descriptions
- Action or emotional descriptions
```

## Length Handling Examples

### Example 1: 1 Hour Story (~10,000 characters)

**Input Parameters:**
- Duration: 60 minutes
- Speed: 1.0x
- Model: Claude 3.7 Sonnet (64K token output limit)

**Calculation:**
```python
base_tts_reading_speed = 180  # words per minute
effective_reading_speed = 180 / 1.0 = 180 WPM
avg_chars_per_word = 4.7
target_length = 60 * 180 * 4.7 = 50,760 characters
```

**Response Planning:**
```
Model capacity: 64,000 tokens * 0.75 = 48,000 safe tokens = 192,000 characters per response
Responses needed: ceil(50,760 / 192,000) = 1 response

Response 1: 0-50,760 characters (100% of content)
- Introduction: 0-10,000 chars
- Main content: 10,000-40,000 chars
- Conclusion: 40,000-50,760 chars
```

**Generation Flow:**
1. Create master document with full structure
2. Generate single response of 50,760 characters
3. No catch-up needed (single response covers all)

### Example 2: 5 Hour Story (~250,000 characters)

**Input Parameters:**
- Duration: 300 minutes
- Speed: 1.0x
- Model: GPT-4o (16K token output limit)

**Calculation:**
```python
base_tts_reading_speed = 180  # words per minute
effective_reading_speed = 180 / 1.0 = 180 WPM
avg_chars_per_word = 4.7
target_length = 300 * 180 * 4.7 = 253,800 characters
```

**Response Planning:**
```
Model capacity: 16,384 tokens * 0.75 = 12,288 safe tokens = 49,152 characters per response
Responses needed: ceil(253,800 / 49,152) = 6 responses

Response 1: 0-49,152 characters (19.4%)
Response 2: 49,152-98,304 characters (19.4%)
Response 3: 98,304-147,456 characters (19.4%)
Response 4: 147,456-196,608 characters (19.4%)
Response 5: 196,608-245,760 characters (19.4%)
Response 6: 245,760-253,800 characters (3.2%) - Final response
```

**Generation Flow:**
1. Create master document with 6-response structure
2. Generate Response 1 (49,152 chars)
3. Generate Response 2 (49,152 chars)
4. If any response falls short by >15%, trigger catch-up
5. Continue through all 6 responses
6. Final response includes story conclusion

### Example 3: Speed-Adjusted Story

**Input Parameters:**
- Duration: 120 minutes
- Speed: 0.8x (slower playback)
- Model: Claude 3.7 Sonnet

**Calculation:**
```python
base_tts_reading_speed = 180  # words per minute
effective_reading_speed = 180 / 0.8 = 225 WPM (MORE content needed for slower speed)
avg_chars_per_word = 4.7
target_length = 120 * 225 * 4.7 = 126,900 characters
```

At 0.8x speed, content plays 25% slower, so we need 25% MORE content for the same duration.

## Model-Specific Behaviors

### Claude Models (Anthropic)
```python
# From MODEL_LIMITS in simple_processor.py
"claude-3-7-sonnet-20250219": {
    "max_input": 800,000,     # 800K character input window
    "max_output": 256,000,     # 64K tokens * 4 chars
    "max_output_tokens": 64000 # Actual API limit: 64,000 tokens
}
```

**Characteristics:**
- Large output capacity allows fewer responses for long content
- Better at maintaining narrative consistency across long generations
- Response planning typically needs 1-3 responses for most use cases
- Catch-up rarely needed due to accurate length targeting

### GPT Models (OpenAI)
```python
"gpt-4o": {
    "max_input": 500,000,      # 500K character input window
    "max_output": 65,536,      # 16K tokens * 4 chars
    "max_output_tokens": 16384 # Actual API limit: 16,384 tokens
}
```

**Characteristics:**
- Smaller output capacity requires more responses for long content
- May need 4-6 responses for 5-hour stories
- More likely to need catch-up rounds for precision
- Better suited for shorter content or heavily chunked generation

### Gemini Models (Google)
```python
"gemini-2.5-pro-preview-06-05": {
    "max_input": 4,000,000,    # 4M character input window
    "max_output": 262,144,     # 65K tokens * 4 chars
    "max_output_tokens": 65536 # Actual API limit: 65,536 tokens
}
```

**Characteristics:**
- Huge input window allows full transcript context
- Similar output capacity to Claude models
- Good for fallback when primary models are overloaded
- Response planning similar to Claude models

## Dynamic Features

### 1. Response Planning Algorithm

```python
def _create_response_plan(self, target_length: int) -> dict:
    # Get model's safe output capacity (75% of max tokens)
    max_tokens = self.model_limits.get("max_output_tokens", 16384)
    safe_tokens = int(max_tokens * 0.75)
    chars_per_response = safe_tokens * 4
    
    # Calculate response breakdown
    needed_responses = math.ceil(target_length / chars_per_response)
    
    # Create detailed plan for each response
    for i in range(needed_responses):
        response_chars = chars_per_response if i < needed_responses - 1 else remaining_chars
        response_plan.append({
            "response_num": i + 1,
            "target_chars": response_chars,
            "percentage_of_total": (response_chars / target_length) * 100
        })
```

### 2. Catch-up System

**Trigger Conditions:**
- Response generates <85% of target characters
- Deficit exceeds 30% on final response
- Critical for maintaining precise timing

**Process:**
1. Calculate deficit: `deficit = min_chars - actual_chars`
2. Generate catch-up content targeting deficit
3. Append to main content
4. Continue with next response

### 3. Character-to-Token Conversion

```python
def _chars_to_tokens(self, chars: int) -> int:
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = chars // 4
    
    # Get the actual API token limit for this model
    max_tokens_allowed = self.model_limits.get("max_output_tokens", 16384)
    
    # Never exceed the API's actual token limit
    actual_tokens = min(estimated_tokens, max_tokens_allowed)
    
    return actual_tokens
```

### 4. Fallback Model Handling

**When Primary Model Overloaded:**
```python
fallback_models = ["gemini-2.0-flash-lite"]
if fallback_enabled and fallback_models:
    for fallback_model in fallback_models:
        # Try fallback with conservative limits
        master_document = process_llm(
            context="Create the master document...",
            system_prompt=master_prompt,
            model=fallback_model,
            max_tokens=8000,  # Conservative limit
            temperature=0.7
        )
```

### 5. Input Window Management

**When Prompt Exceeds Model Limits:**
```python
def _ensure_input_fits(self, prompt: str) -> str:
    max_input_chars = self.model_limits["max_input"]
    
    if len(prompt) <= max_input_chars:
        return prompt
    
    # Keep beginning and end, trim middle
    keep_start = max_input_chars // 3
    keep_end = max_input_chars // 3
    
    trimmed_prompt = (
        prompt[:keep_start] +
        "\n\n[... CONTENT TRIMMED ...]\n\n" +
        prompt[-keep_end:]
    )
    return trimmed_prompt
```

## Processing Modes

### Recreation Mode (Custom Instructions Present)
**Triggered when:** User provides role, structure, tone, or additional instructions
**Behavior:** 
- Ignores original transcript subject matter
- Creates entirely new content based on user specifications
- Uses master document to plan new narrative structure

### Improvement Mode (No Custom Instructions)
**Triggered when:** No user instructions provided
**Behavior:**
- Enhances existing transcript
- Maintains original subject and structure
- Improves readability and flow

## Key Metrics and Tolerances

| Metric | Value | Description |
|--------|-------|-------------|
| **Target Precision** | ±15% | Acceptable range for response length |
| **Catch-up Trigger** | <85% | When response falls below this, catch-up activates |
| **Safe Token Usage** | 75% | Conservative limit to avoid API cutoffs |
| **Character/Token Ratio** | 4:1 | Estimation for token conversion |
| **TTS Reading Speed** | 180 WPM | Base reading speed for duration calculations |
| **Speed Adjustment** | 1/speed | Inverse relationship: slower speed = more content |

## Summary

The prompt infrastructure is designed for:
1. **Precision**: Multiple mechanisms ensure accurate length targeting
2. **Flexibility**: Handles stories from minutes to hours
3. **Reliability**: Fallback systems and catch-up ensure completion
4. **Quality**: TTS-optimized output with proper formatting
5. **Customization**: Full support for user-defined narratives

The system's strength lies in its response-aware approach, where each generation knows its role in the overall narrative, combined with dynamic catch-up to ensure precise length requirements are met.