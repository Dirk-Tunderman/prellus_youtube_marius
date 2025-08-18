# Correction Plan: Enhanced User Instruction Emphasis with Section Awareness

## Problem Statement

The current prompt system includes user instructions but needs enhancement to:
- **Emphasize absolute compliance** with user instructions in every prompt
- **Make AI aware of what section it's creating** (intro, outro, specific parts/chapters)
- **Extract and highlight section-specific requirements** from user instructions
- **Emphasize literal/specific requirements** that must be included exactly
- **Do this through prompt modifications only** - no hardcoded detection logic

## Current State Analysis

### What's Working Well
- ✅ User instructions are included in every prompt (first tries, retries, fallbacks)
- ✅ Instructions are extracted consistently via `_extract_user_instructions()`
- ✅ All 5 prompt types include user instructions
- ✅ Instructions are preserved through all retry mechanisms

### What Needs Improvement
- ❌ User instructions are not visually prominent enough in prompts
- ❌ No special emphasis for intro/outro specific requirements
- ❌ Critical requirements get lost among general instructions
- ❌ No clear hierarchy of importance in user instructions

## Proposed Solution: Section-Aware Prompt Enhancement

### Core Principle
**PROMPT-BASED EMPHASIS ONLY** - Enhance prompts to make AI extremely aware of:
1. **Absolute compliance requirement** with user instructions
2. **What section it's currently creating** (intro, outro, specific parts)
3. **Section-specific requirements** extracted from user instructions
4. **Literal requirements** that must be included exactly as specified

### Specific Implementation Approach

#### 1. Enhanced User Instruction Header (All Prompts)
```
🚨🚨🚨 ABSOLUTE COMPLIANCE WITH USER INSTRUCTIONS REQUIRED 🚨🚨🚨
═══════════════════════════════════════════════════════════════

⚡ **CRITICAL**: You MUST follow these user instructions exactly. Any deviation is unacceptable.
⚡ **AWARENESS**: You are creating [SECTION TYPE] - pay special attention to requirements for this section.
⚡ **LITERAL COMPLIANCE**: When user specifies exact content, include it exactly as requested.

═══════════════════════════════════════════════════════════════
```

#### 2. Section Context Block (Dynamic per prompt)
```
📍 **CURRENT SECTION CONTEXT:**
- You are creating: [INTRO/PART 1/PART 2/OUTRO/etc.]
- Section purpose: [Brief description of what this section should accomplish]
- Special attention needed for: [Section-specific requirements from user instructions]

🎯 **SECTION-SPECIFIC USER REQUIREMENTS:**
[Extract and display any requirements that mention this specific section]
```

#### 3. User Instruction Analysis Block (All Prompts)
```
🔍 **USER INSTRUCTION ANALYSIS FOR THIS SECTION:**

📋 **GENERAL REQUIREMENTS (Apply to all sections):**
- Role: [User's role instruction]
- Tone & Style: [User's tone instruction]
- Retention & Flow: [User's retention instruction]

🎬 **INTRO-SPECIFIC REQUIREMENTS (if creating intro):**
[Any requirements mentioning "intro", "opening", "start", "begin", "hook"]

🎭 **OUTRO-SPECIFIC REQUIREMENTS (if creating outro):**
[Any requirements mentioning "outro", "conclusion", "ending", "close", "final"]

📖 **CONTENT-SPECIFIC REQUIREMENTS (for this section):**
[Any requirements mentioning specific topics, chapters, or content for this section]

⚡ **LITERAL REQUIREMENTS (must include exactly):**
[Any specific phrases, quotes, or exact content user wants included]
```

#### 4. Master Document Enhancement
When creating the master document, include section-specific analysis:
```
📋 **MASTER DOCUMENT SECTION ANALYSIS:**

🎬 **INTRO SECTION PLAN:**
- Requirements from user: [Extract intro-specific requirements]
- Must include: [Any literal content for intro]
- Tone for intro: [Specific intro tone if mentioned]

📖 **MAIN CONTENT SECTIONS:**
- Part 1: [Topic] - User requirements: [Specific requirements for this part]
- Part 2: [Topic] - User requirements: [Specific requirements for this part]
- [Continue for each section]

🎭 **OUTRO SECTION PLAN:**
- Requirements from user: [Extract outro-specific requirements]
- Must include: [Any literal content for outro]
- Closing style: [Specific outro style if mentioned]

⚡ **LITERAL CONTENT TO INCLUDE:**
[List all specific phrases, quotes, or exact content user wants included]
```

#### 5. Response Generation Context
For each response generation, make AI extremely aware:
```
🎯 **WHAT YOU ARE CREATING RIGHT NOW:**
- Current section: [INTRO/PART 1/PART 2/OUTRO]
- Section topic: [Specific topic for this section]
- Your task: Generate content for this specific section following ALL user requirements

🚨 **CRITICAL REMINDERS FOR THIS SECTION:**
- You MUST follow user instructions exactly
- Pay special attention to requirements for [CURRENT SECTION]
- Include any literal content specified for this section
- Maintain the exact tone and style requested by user
```

## Specific Implementation Plan

### Step 1: Create Section-Aware User Instruction Parser
**File**: `app/src/core/processor/simple_processor.py`
**Function**: `_extract_user_instructions()` (enhance existing)

Add logic to:
1. **Parse user instructions** for section-specific content
2. **Extract intro-specific requirements** (mentions of "intro", "opening", "start", "hook")
3. **Extract outro-specific requirements** (mentions of "outro", "conclusion", "ending", "close")
4. **Extract content-specific requirements** (mentions of specific topics, chapters, parts)
5. **Extract literal requirements** (exact phrases, quotes in quotes)

**No automatic detection** - just simple text parsing for obvious keywords.

### Step 2: Enhance Master Document Prompt
**File**: `app/src/core/processor/simple_processor.py`
**Function**: `_build_master_document_prompt()`

Add these sections to the prompt:
1. **Absolute compliance header** (as shown above)
2. **Section analysis block** that breaks down user requirements by section
3. **Literal content tracking** for exact phrases to include
4. **Section-specific planning** for intro/outro requirements

### Step 3: Enhance All Response Generation Prompts
**Functions to modify**:
- `_build_response_prompt()`
- `_build_response_prompt_with_sections()`
- `_build_catch_up_prompt()`
- `_build_shortened_response_prompt()`

Add to each prompt:
1. **Section context block** - what section is being created
2. **Section-specific requirements** - requirements for this specific section
3. **Literal content reminders** - exact content to include
4. **Absolute compliance emphasis** - must follow user instructions exactly

### Step 4: Add Section Detection Logic
**File**: `app/src/core/processor/simple_processor.py`

Simple logic to determine current section:
- Response 1 = "INTRO"
- Final response = "OUTRO"
- Middle responses = "PART X" or based on master document structure
- Pass this context to all prompt functions

## Example Implementation

### Example User Instructions:
```
Role: You are a wildlife expert storyteller
Script Structure: Start with a dramatic hook about lions. Main content should cover 3 parts: 1) Lions in general 2) Special lions in South Africa 3) The Zulu tribe connection. End with "The roar of the lion echoes through time."
Tone & Style: Dramatic and educational
Additional Instructions: When talking about South Africa lions, you must mention the Kruger National Park specifically. The story must include the exact phrase "These magnificent creatures rule the savanna."
```

### How This Gets Processed:

#### Master Document Prompt Enhancement:
```
🚨🚨🚨 ABSOLUTE COMPLIANCE WITH USER INSTRUCTIONS REQUIRED 🚨🚨🚨

📋 **SECTION-SPECIFIC USER REQUIREMENTS ANALYSIS:**

🎬 **INTRO REQUIREMENTS:**
- Must start with "dramatic hook about lions"
- Opening style: Dramatic

📖 **MAIN CONTENT STRUCTURE:**
- Part 1: Lions in general
- Part 2: Special lions in South Africa (MUST mention Kruger National Park specifically)
- Part 3: The Zulu tribe connection

🎭 **OUTRO REQUIREMENTS:**
- Must end with exact phrase: "The roar of the lion echoes through time."

⚡ **LITERAL CONTENT TO INCLUDE:**
- "These magnificent creatures rule the savanna." (exact phrase required)
- "The roar of the lion echoes through time." (exact ending required)
- Kruger National Park (must be mentioned in South Africa section)
```

#### Response Generation Prompt Enhancement:
```
🎯 **WHAT YOU ARE CREATING RIGHT NOW:**
- Current section: PART 2 (Special lions in South Africa)
- Your task: Generate content about special lions in South Africa

🚨 **CRITICAL REQUIREMENTS FOR THIS SECTION:**
- You MUST mention Kruger National Park specifically
- You MUST include the exact phrase "These magnificent creatures rule the savanna."
- Maintain dramatic and educational tone
- This is Part 2 of 3 - connect to general lions (Part 1) and lead to Zulu connection (Part 3)
```

## Technical Implementation Details

### Functions to Modify:

1. **`_extract_user_instructions()`** - Add section-specific parsing
2. **`_build_master_document_prompt()`** - Add section analysis and literal content tracking
3. **`_build_response_prompt()`** - Add section context and specific requirements
4. **`_build_response_prompt_with_sections()`** - Add section awareness
5. **`_build_catch_up_prompt()`** - Maintain section context in catch-up
6. **`_build_shortened_response_prompt()`** - Maintain requirements in shortening

### Key Principles:
- **No complex automatic detection** - just simple keyword matching
- **Always pass section context** to prompt functions
- **Extract literal requirements** (content in quotes or explicitly stated)
- **Make AI extremely aware** of what section it's creating
- **Emphasize absolute compliance** in every prompt

## Success Criteria

1. **AI knows exactly what section it's creating** (intro/part/outro)
2. **Section-specific requirements are highlighted** in relevant prompts
3. **Literal content requirements are impossible to miss**
4. **Absolute compliance is emphasized** in every prompt
5. **User feedback confirms** AI follows instructions more faithfully

## Implementation Approach

**Single-phase implementation** with all enhancements:
- Modify existing prompt functions only
- Add section-aware parsing to user instruction extraction
- No new frontend fields or backend changes needed
- Test with existing user instruction system
- Verify all 5 prompt types work correctly
