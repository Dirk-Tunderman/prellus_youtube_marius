# PROMPT_INFRASTRUCTURE.md

This document provides a comprehensive overview of the **Enhanced Section-Aware Processing System** used in the YouTube Transcript Processor's story generation system.

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Enhanced Data Structures](#enhanced-data-structures)
3. [Prompt Types and Usage](#prompt-types-and-usage)
4. [Complete Prompt Templates](#complete-prompt-templates)
5. [Time-Based Instructions](#time-based-instructions)
6. [Section Tracking Examples](#section-tracking-examples)
7. [Model-Specific Behaviors](#model-specific-behaviors)
8. [Dynamic Features](#dynamic-features)

## System Architecture Overview

The story generation system uses an **Enhanced Section-Aware Processing System** with the following key components:

### Processing Flow
```
Input → Time Parsing → Master Outline Creation → Structured Data Generation → Section-Aware Generation → Section-Aware Catch-up → Final Output
```

### Major Improvements (2025 Update)
1. **Concise Master Documents**: 80% reduction in verbosity - outline format only, not full content
2. **Structured Section Tracking**: Precise character boundaries with section-aware generation
3. **Time-Based Instruction Processing**: Automatic conversion of time ranges to character allocations
4. **Section-Aware Catch-up**: Context-aware deficit filling that respects section boundaries
5. **Enhanced Progress Tracking**: Real-time section completion monitoring
6. **Model-Aware Response Planning**: Clear breakpoints based on model output limits

### Key Innovations
1. **Structured Master Documents**: Creates CONCISE outlines with precise section boundaries
2. **Section-Aware Processing**: Each generation knows exactly which section it's working on
3. **Time-to-Character Conversion**: Handles user instructions like "10-15 minutes about X"
4. **CharacterBoundaryManager**: Real-time progress tracking with section context
5. **Enhanced Catch-up System**: Section-aware deficit filling that maintains content boundaries

## Enhanced Data Structures

The new system introduces structured data models for precise section tracking:

### SectionBoundary
```python
@dataclass
class SectionBoundary:
    section_id: str          # "1.1", "2.3"
    title: str               # User-provided or auto-generated
    start_char: int          # Exact start position
    end_char: int            # Exact end position
    target_chars: int        # Expected character count
    content_type: str        # "introduction", "main_content", "transition", "conclusion"
    key_points: List[str]    # Topics to cover
    user_instructions: str   # Section-specific guidance
    response_num: int        # Which LLM response generates this
```

### ResponseSection
```python
@dataclass
class ResponseSection:
    response_num: int                # 1, 2, 3, etc.
    sections: List[SectionBoundary]  # All sections in this response
    total_target_chars: int          # Total characters for this response
    start_char: int                  # Response start position
    end_char: int                    # Response end position
    completion_status: str           # "pending", "in_progress", "completed"
    actual_chars_generated: int      # Actual output
```

### MasterDocumentStructure
```python
@dataclass
class MasterDocumentStructure:
    total_target_chars: int               # Overall target
    total_duration_minutes: float         # Expected duration
    total_responses_needed: int           # Number of LLM calls
    response_sections: List[ResponseSection]  # All response data
    section_index: Dict[str, SectionBoundary]  # Quick lookup
    model_name: str                       # Model being used
    model_char_limit: int                 # Model's output limit
```

### CharacterBoundaryManager
Provides real-time progress tracking:
```python
class CharacterBoundaryManager:
    def update_progress(self, content: str) -> Dict[str, Any]
    def get_next_target(self, current_chars: int) -> Tuple[str, int]
    def get_section_context(self, section_id: str, current_chars: int) -> Dict[str, Any]
```

## Prompt Types and Usage

The enhanced system uses **6 main prompt types**:

| Prompt Type | When Used | Purpose |
|------------|-----------|---------|
| **Concise Master Outline** | Start of processing | Creates structured outline (NOT content) with precise boundaries |
| **Section-Aware Response Generation** | For each response chunk | Generates content with full section context |
| **Section-Aware Catch-up** | When response falls short | Fills deficit while respecting section boundaries |
| **Time-Based Instruction Processing** | During setup | Converts time ranges to character allocations |
| **TTS Formatting Rules** | All generation prompts | Ensures output is TTS-ready |
| **User Instructions Integration** | All prompts | Integrates custom user requirements |

## Complete Prompt Templates

### 1. Enhanced Master Document Creation Prompt

**NEW CONCISE OUTLINE-ONLY APPROACH:**

```
You are a content structure planner. Create a CONCISE OUTLINE ONLY - no story content.

# STRICT RULES
- Output ONLY section titles, boundaries, and brief topic notes (max 10 words per note)
- NO narrative text, NO detailed content, NO full sentences
- Use structured format EXACTLY as shown below
- Each section gets ONE LINE of description maximum

# PROJECT SPECIFICATIONS
Total Target: {target_length:,} characters (~{target_length // 250:,} words)
Duration: ~{target_length // CHARS_PER_MINUTE_BASE:.1f} minutes reading time
Model: {self.model} (Response limit: ~{model_char_limit:,} chars)
Responses Required: {response_plan['responses_needed']}

# USER REQUIREMENTS
Role: {user_instructions.get('role', 'Expert content creator')}
Tone: {user_instructions.get('tone_style', 'Professional and engaging')}
Structure: {script_structure if script_structure else 'Create appropriate structure'}

# TIME-BASED INSTRUCTIONS CONVERTED TO CHARACTERS:
- 10.0-15.0 min → [50,000-75,000] chars: Main topic discussion
- 15.0-20.0 min → [75,000-100,000] chars: Examples and case studies

# OUTPUT FORMAT (USE EXACTLY)

## RESPONSE ALLOCATION
Response 1: [0-50,000] chars
Response 2: [50,000-100,000] chars

## MASTER OUTLINE

### Response 1 [50,000 chars]
SECTION_1.1 | 0-20000 chars | [max 10 word topic description]
SECTION_1.2 | 20000-35000 chars | [max 10 word topic description]
SECTION_1.3 | 35000-50000 chars | [max 10 word topic description]

### Response 2 [50,000 chars]
SECTION_2.1 | 50000-75000 chars | [max 10 word topic description]
SECTION_2.2 | 75000-100000 chars | [max 10 word topic description]

## SECTION DETAILS
SECTION_1.1: [max 10 words describing core topic]
SECTION_1.2: [max 10 words describing core topic]

## TRANSITION NOTES
R1→R2: [5 words max on connection point]

END_OUTLINE

# CRITICAL REQUIREMENTS:
1. TOTAL outline must be UNDER 2,500 characters
2. Each section description: MAXIMUM 10 words
3. NO story content, ONLY structural planning
4. Precise character boundaries for EVERY section
5. Clear topic keywords, not full sentences
```

**Key Improvements:**
- **80% more concise** than old system
- **Enforced structure** with parsing validation
- **Character limits** on descriptions (max 10 words)
- **Time-to-character conversion** built-in
- **Model-aware response planning**

### 2. Section-Aware Response Generation Prompt

**COMPLETELY NEW** - Now includes full section context via `_build_response_prompt_with_sections()`:

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

## Time-Based Instructions

**NEW FEATURE**: The system now automatically converts time-based user instructions to character allocations.

### Supported Time Formats

```python
# Time range patterns
"0-10 minutes about introduction and background"
"10 to 25 minutes covering main analysis"
"25-30 minutes on conclusion and wrap-up"

# Duration patterns  
"first 10 minutes about opening"
"next 15 minutes discussing examples"
"last 5 minutes for summary"
```

### Conversion Process

1. **Parse Time Instructions** - Extract time ranges and topics
2. **Convert to Characters** - Using reading speed formula
3. **Map to Sections** - Create SectionBoundary objects
4. **Assign to Responses** - Determine which LLM call handles each section

### Example Conversion

```
User Input:
"0-10 minutes: introduction to the topic
10-25 minutes: detailed analysis with examples  
25-30 minutes: conclusion and next steps"

System Output:
SECTION_1.1 | 0-50000 chars | introduction to topic
SECTION_1.2 | 50000-125000 chars | detailed analysis with examples
SECTION_2.1 | 125000-150000 chars | conclusion and next steps

Response Planning:
Response 1: Sections 1.1-1.2 (0-125,000 chars)
Response 2: Section 2.1 (125,000-150,000 chars)
```

### Benefits

- **User-Friendly**: Natural time-based instructions
- **Precise Conversion**: Accounts for reading speed and playback speed
- **Automatic Mapping**: No manual character calculations needed
- **Section Awareness**: Each section knows its time context

## Section Tracking Examples

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