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
    model: str = "gemini-2.0-flash-lite",
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
            
            logger.warning(f"API error on attempt {retry_count}/{max_retries}: {str(e)}")
            
            # Implement exponential backoff
            if retry_count < max_retries:
                sleep_time = 2 ** retry_count
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    # If we've exhausted retries, attempt fallback if configured
    if os.environ.get("LLM_FALLBACK_ENABLED") == "true" and os.environ.get("LLM_FALLBACK_MODEL"):
        fallback_model = os.environ.get("LLM_FALLBACK_MODEL")
        logger.info(f"Attempting fallback to model: {fallback_model}")
        try:
            return process_llm(
                text=context,
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