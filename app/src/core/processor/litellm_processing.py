"""
Universal LLM Processor Module

This module provides unified functions for processing text with various LLM providers
through LiteLLM, supporting OpenAI, Gemini, Anthropic, and DeepSeek models.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List, Union

import litellm
import google.generativeai as genai
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def process_with_llm(
    context: str,
    system_prompt: str,
    model: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    max_retries: int = 3,
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Universal function to process text with different LLM providers through LiteLLM.
    This function has the same signature as the existing code expects.
    
    Args:
        context: The input text/context to process
        system_prompt: System instructions for the model
        model: Model identifier (e.g., "gpt-4", "gemini-pro", "claude-3-opus-20240229")
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature for response generation (0.0 to 1.0)
        max_retries: Maximum number of retry attempts on failure
        additional_params: Any additional provider-specific parameters
        
    Returns:
        The processed text response from the LLM
    """
    return process_llm(
        text=context,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        max_retries=max_retries,
        additional_params=additional_params
    )

def process_llm(
    context: str,
    system_prompt: Optional[str] = None,
    model: str = None,  # Changed from hardcoded default to None
    max_tokens: int = 4000,
    temperature: float = 0.7,
    max_retries: int = 3,
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Universal function to process text with different LLM providers through LiteLLM.
    
    Args:
        text: The input text/context to process
        system_prompt: System instructions for the model
        model: Model identifier (e.g., "gpt-4", "gemini-pro", "claude-3-opus-20240229")
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature for response generation (0.0 to 1.0)
        max_retries: Maximum number of retry attempts on failure
        additional_params: Any additional provider-specific parameters
        
    Returns:
        The processed text response from the LLM
    """
    # Use default model from config.yaml if none specified
    
    if model is None:
        project_root = str(Path(__file__).parent.parent.parent)
        config_path = os.path.join(project_root, "app/config/config.yaml")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                model = config.get('ai', {}).get('model', "gemini-2.0-flash-lite")
            else:
                model = "gemini-2.0-flash-lite"  # Fallback default
        except Exception as e:
            logger.warning(f"Error loading model from config: {e}. Using default model.")
            model = "gemini-2.0-flash-lite"  # Fallback default
    else:
        logger.debug(f"Using model: {model}")
        
    # Check for model-specific API keys
    _check_api_key_for_model(model)
    
    # Format the model name appropriately for LiteLLM
    formatted_model = _format_model_name(model)
    
    logger.info(f"Processing text with model: {formatted_model}")
    
    # Check for mock mode
    if os.environ.get("MOCK_LLM_API") == "true":
        logger.info("Using mock LLM API mode")
        return f"Mock processed text using {formatted_model}: {context[:100]}..."
    
    # Set up additional parameters
    params = additional_params or {}
    
    # Add standard parameters if not explicitly set
    # GPT-5 models have special requirements: no max_completion_tokens, no temperature
    if formatted_model.startswith("gpt-5"):
        # GPT-5 doesn't accept max_completion_tokens parameter - let it use default
        # GPT-5 only supports temperature=1.0 (default), so don't set it
        # This allows GPT-5 to generate naturally without token limit constraints
        pass
    else:
        if "max_tokens" not in params:
            params["max_tokens"] = max_tokens
        if "temperature" not in params:
            params["temperature"] = temperature
    
    # Initialize retry counter and last error storage
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            # Special handling for Gemini models
            if "gemini" in formatted_model.lower():
                response = _process_with_gemini(
                    text=context,
                    system_prompt=system_prompt,
                    model=formatted_model,
                    params=params
                )
            else:
                # Standard message format for OpenAI, Anthropic, DeepSeek, etc.
                messages = [
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": context}
                ]
                
                # Log the actual parameters being sent
                logger.info(f"🔧 API Call Parameters:")
                logger.info(f"   Model: {formatted_model}")
                if formatted_model.startswith("gpt-5"):
                    logger.info(f"   Max completion tokens: auto (GPT-5 manages token limits)")
                    logger.info(f"   Temperature: default (1.0) - GPT-5 uses default only")
                else:
                    logger.info(f"   Max tokens: {params.get('max_tokens', 'not set')}")
                    logger.info(f"   Temperature: {params.get('temperature', 'not set')}")
                logger.info(f"   System prompt length: {len(system_prompt or ''):,} chars")
                logger.info(f"   User message length: {len(context):,} chars")

                # Make the API call
                response = litellm.completion(
                    model=formatted_model,
                    messages=messages,
                    **params
                )
                
                # Extract the response text
                response = response.choices[0].message.content
                
            logger.info(f"Received response from LLM. Length: {len(response)} characters")
            return response
            
        except Exception as e:
            last_error = e
            retry_count += 1

            # Check if this is an overload error
            is_overload = "overloaded" in str(e).lower() or "529" in str(e)

            if is_overload:
                logger.warning(f"API overloaded on attempt {retry_count}/{max_retries}: Anthropic servers are experiencing high load")
            else:
                logger.warning(f"API error on attempt {retry_count}/{max_retries}: {str(e)}")

            # Implement exponential backoff with longer waits for overload
            if retry_count < max_retries:
                if is_overload:
                    # Much longer wait for overload: 15, 30, 60 seconds
                    sleep_time = 15 * (2 ** (retry_count - 1))
                    logger.info(f"API overloaded - waiting {sleep_time} seconds before retry...")
                else:
                    # Standard exponential backoff: 2, 4, 8 seconds
                    sleep_time = 2 ** retry_count
                    logger.info(f"Retrying in {sleep_time} seconds...")

                time.sleep(sleep_time)
    
    # If we've exhausted retries, attempt fallback if configured
    if os.environ.get("LLM_FALLBACK_ENABLED") == "true" and os.environ.get("LLM_FALLBACK_MODEL"):
        fallback_model = os.environ.get("LLM_FALLBACK_MODEL")
        logger.info(f"Attempting fallback to model: {fallback_model}")
        try:
            return process_llm(
                context=context,
                system_prompt=system_prompt,
                model=fallback_model,
                max_tokens=max_tokens,
                temperature=temperature,
                max_retries=1,  # Only try once with fallback
                additional_params=additional_params
            )
        except Exception as fallback_error:
            logger.exception(f"Fallback also failed: {fallback_error}")
    
    # Log the error and re-raise
    logger.error(f"Failed to process with {formatted_model} after {max_retries} attempts. Last error: {last_error}")
    if last_error:
        raise last_error
    else:
        raise Exception(f"Failed to get valid response from {formatted_model} after {max_retries} attempts")

def _process_with_gemini(
    text: str,
    system_prompt: Optional[str],
    model: str,
    params: Dict[str, Any]
) -> str:
    """
    Process text with Gemini models, handling their specific requirements.
    
    Args:
        text: The input text to process
        system_prompt: System instructions
        model: Formatted model name
        params: Processing parameters
        
    Returns:
        The response text
    """
    # For Gemini, combine the system prompt and user text
    # This is because Gemini doesn't natively support system prompts
    combined_prompt = f"{system_prompt}\n\n{text}" if system_prompt else text
    
    # Handle raw vs litellm gemini format
    if model.startswith("gemini/"):
        # Using LiteLLM format
        messages = [
            {"role": "user", "content": combined_prompt}
        ]
        
        response = litellm.completion(
            model=model,
            messages=messages,
            max_tokens=params.get("max_tokens", 4000),
            temperature=params.get("temperature", 0.7)
        )
        
        return response.choices[0].message.content
    else:
        # Direct API call to Gemini
        # Extract the actual model name
        model_name = model.replace("gemini/", "")
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        
        # Configure the model
        gemini_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": params.get("temperature", 0.7),
                "max_output_tokens": params.get("max_tokens", 4000),
                "top_p": params.get("top_p", 1.0),
                "top_k": params.get("top_k", 40)
            }
        )
        
        # Generate content
        safety_settings = params.get("safety_settings", None)
        if safety_settings:
            response = gemini_model.generate_content(
                combined_prompt,
                safety_settings=safety_settings
            )
        else:
            response = gemini_model.generate_content(combined_prompt)
            
        # Return the response text
        return response.text

def _format_model_name(model: str) -> str:
    """
    Format the model name according to provider requirements for LiteLLM.
    
    Args:
        model: The model identifier
        
    Returns:
        Properly formatted model name for LiteLLM
    """
    # If the model already has a provider prefix, return as is
    if "/" in model:
        return model
        
    # Add provider prefix based on model name patterns
    if any(name in model.lower() for name in ["gpt", "text-davinci", "babbage", "curie", "ada", "davinci"]):
        # OpenAI models don't need a prefix
        return model
    elif "gemini" in model.lower():
        # Gemini models need the "gemini/" prefix for litellm
        return f"gemini/{model}"
    elif any(name in model.lower() for name in ["claude", "anthropic"]):
        # Anthropic models don't need a prefix in LiteLLM
        return model
    elif "deepseek" in model.lower():
        # DeepSeek models need the "deepseek/" prefix
        return f"deepseek/{model}"
    else:
        # Default case, return as is
        logger.warning(f"Unknown model type: {model}. Using without provider prefix.")
        return model

def _check_api_key_for_model(model: str) -> None:
    """
    Verify that the appropriate API key is set for the selected model.
    
    Args:
        model: The model identifier
        
    Raises:
        ValueError: If the required API key is not set
    """
    # Determine provider from model name
    provider = "unknown"
    if any(name in model.lower() for name in ["gpt", "text-davinci", "babbage", "curie", "ada", "davinci"]):
        provider = "openai"
        key_name = "OPENAI_API_KEY"
    elif "gemini" in model.lower():
        provider = "gemini"
        key_name = "GOOGLE_API_KEY" if not os.environ.get("GEMINI_API_KEY") else "GEMINI_API_KEY"
    elif any(name in model.lower() for name in ["claude", "anthropic"]):
        provider = "anthropic"
        key_name = "ANTHROPIC_API_KEY"
    elif "deepseek" in model.lower():
        provider = "deepseek"
        key_name = "DEEPSEEK_API_KEY"
    else:
        # Default case, we'll try to proceed
        return
        
    # Check for API key
    api_key = os.environ.get(key_name)
    if not api_key:
        error_msg = f"Missing {key_name} for {provider} model: {model}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    


