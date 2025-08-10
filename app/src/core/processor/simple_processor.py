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
import logging
from typing import Dict, Any, Optional, List, Tuple
from .processor_base import TranscriptProcessorInterface
from .litellm_processing import process_llm

logger = logging.getLogger(__name__)

# Model-specific limits (characters AND tokens)
# IMPORTANT: We track both characters and actual API token limits
MODEL_LIMITS = {
    # OpenAI Models - Current 2024/2025 limits
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
        master_document, response_plan = self._create_master_document(transcript_text, target_length)
        
        if output_dir:
            master_doc_path = os.path.join(output_dir, "master_document.txt")
            with open(master_doc_path, "w", encoding="utf-8") as f:
                f.write(master_document)
            logger.info(f"💾 Saved master document to {master_doc_path}")
        
        # Step 2: Generate content using response-aware approach
        logger.info("✨ Step 2: Generating content with response planning...")
        processed_transcript = self._generate_content(
            transcript_text, master_document, response_plan, output_dir
        )
        
        logger.info(f"🎉 Processing complete! Generated {len(processed_transcript):,} characters")
        return processed_transcript
    
    def _calculate_target_length(self, transcript_text: str) -> int:
        """Calculate target length based on user input or default scaling."""
        # Check if user specified duration (minutes)
        duration_minutes = self.ai_config.get("length")
        if duration_minutes:
            # Convert minutes to characters (using reading speed calculation)
            effective_reading_speed = 225  # words per minute
            avg_chars_per_word = 4.7
            target_length = int(duration_minutes * effective_reading_speed * avg_chars_per_word)
            logger.info(f"📊 Target from duration: {duration_minutes} min → {target_length:,} chars")
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
    
    def _create_master_document(self, transcript_text: str, target_length: int) -> tuple[str, dict]:
        """Create master document with response planning."""
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
        try:
            # Calculate safe token count for master document (1/4 of max output)
            master_doc_chars = self.model_limits["max_output"] // 4
            master_doc_tokens = self._chars_to_tokens(master_doc_chars)

            logger.info(f"📋 Master document generation: {master_doc_chars:,} chars → {master_doc_tokens:,} tokens")

            master_document = process_llm(
                context="Create the master document as specified in the system prompt.",  # Simple user message
                system_prompt=master_prompt,
                model=self.model,
                max_tokens=master_doc_tokens,  # Use safe token conversion
                temperature=0.7,
                max_retries=5  # More retries for master document
            )
        except Exception as e:
            if "overloaded" in str(e).lower():
                logger.warning("⚠️ Primary model overloaded, attempting fallback...")

                # Try fallback models
                fallback_models = self.ai_config.get("fallback_models", ["gemini-2.0-flash-lite"])
                fallback_enabled = self.ai_config.get("fallback_enabled", True)

                if fallback_enabled and fallback_models:
                    for fallback_model in fallback_models:
                        try:
                            logger.info(f"🔄 Trying fallback model: {fallback_model}")
                            master_document = process_llm(
                                context="Create the master document as specified in the system prompt.",
                                system_prompt=master_prompt,
                                model=fallback_model,
                                max_tokens=8000,  # Conservative limit for fallback
                                temperature=0.7,
                                max_retries=3
                            )
                            logger.info(f"✅ Fallback model {fallback_model} succeeded!")
                            break
                        except Exception as fallback_error:
                            logger.warning(f"❌ Fallback model {fallback_model} also failed: {fallback_error}")
                            continue
                    else:
                        # All fallbacks failed
                        logger.error("🚨 CRITICAL: All models (primary + fallbacks) are overloaded")
                        logger.error("   This indicates widespread API issues across providers")
                        logger.error("   Please try again in 15-30 minutes")
                        raise Exception("All AI models are currently overloaded - please try again later") from e
                else:
                    logger.error("🚨 CRITICAL: Primary model overloaded and no fallbacks configured")
                    raise Exception("Anthropic API overloaded - please try again later") from e
            else:
                raise e
        
        logger.info(f"📋 Master document created: {len(master_document):,} characters")
        return master_document, response_plan
    
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

    def _create_response_plan(self, target_length: int) -> dict:
        """Calculate how many responses needed based on model capacity."""

        # Get model's safe output capacity (75% of max tokens in chars)
        max_tokens = self.model_limits.get("max_output_tokens", 16384)
        safe_tokens = int(max_tokens * 0.75)
        chars_per_response = safe_tokens * 4

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
        """Build master document prompt with response planning."""

        # Check if user provided structure
        has_user_structure = bool(user_instructions.get("script_structure", "").strip())

        prompt = f"""# MASTER DOCUMENT CREATION WITH RESPONSE PLANNING

## TARGET SPECIFICATIONS
- Total Length: {target_length:,} characters
- Duration: ~{target_length // (180 * 4.7):.1f} minutes
- Responses Needed: {response_plan['responses_needed']}

## RESPONSE BREAKDOWN
You need to structure content for {response_plan['responses_needed']} responses:
"""

        # Add response breakdown with explicit section mapping
        for plan in response_plan["response_plan"]:
            start_char = sum(p['target_chars'] for p in response_plan["response_plan"][:plan['response_num']-1])
            end_char = start_char + plan['target_chars']
            start_minutes = start_char / (180 * 4.7)
            end_minutes = end_char / (180 * 4.7)

            prompt += f"""
### Response {plan['response_num']} - CHARACTER RANGE: {start_char:,} to {end_char:,}
- **Target Length**: {plan['target_chars']:,} characters ({plan['percentage_of_total']:.1f}% of total)
- **Time Range**: {start_minutes:.1f} to {end_minutes:.1f} minutes of final content
- **Content Sections**: [YOU MUST SPECIFY which parts/chapters/sections go in this character range]
- **Character Breakdown**: [YOU MUST break down how characters are distributed within this response]
"""

        # Handle user structure
        if has_user_structure:
            prompt += f"""
## USER-PROVIDED STRUCTURE (IMPORTANT - USE THIS)
{user_instructions['script_structure']}

**TASK**: Adapt the above user structure to fit the {response_plan['responses_needed']} response breakdown.
Map user's chapters/sections to specific responses.
"""
        else:
            prompt += f"""
## STRUCTURE CREATION NEEDED
User did not provide specific structure. Create appropriate chapters/sections that:
1. Fit the {response_plan['responses_needed']} response breakdown
2. Work well with the content theme
3. Maintain narrative flow across responses
"""

        prompt += f"""
## USER INSTRUCTIONS
**Role:** {user_instructions['role']}
**Tone & Style:** {user_instructions['tone_style'] or "Professional, engaging narrative style"}
**Additional:** {user_instructions['additional_instructions'] or "None specified"}

## ORIGINAL TRANSCRIPT
{transcript_text[:10000]}{"..." if len(transcript_text) > 10000 else ""}

## OUTPUT REQUIREMENTS
Create a master document that:

**CRITICAL - SECTION BREAKDOWN REQUIRED:**
1. {"Map your provided structure to the response breakdown above" if has_user_structure else "Create logical sections/chapters that fit the response breakdown above"}
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
"""

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

        # Get context from recent content (last 3000 characters)
        context_chars = min(3000, len(generated_content))
        recent_content = generated_content[-context_chars:] if context_chars > 0 else ""

        # Calculate acceptable range for catch-up
        min_chars = int(deficit * 0.85)
        max_chars = int(deficit * 1.15)

        prompt = f"""# CATCH-UP CONTENT GENERATION

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

        prompt = f"""# RESPONSE {response_num} OF {response_plan['responses_needed']} GENERATION

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
