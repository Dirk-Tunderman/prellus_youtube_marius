#!/usr/bin/env python3
"""
Test script to isolate GPT-5 output limitation issue.
Tests both direct OpenAI API and LiteLLM approaches.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_openai():
    """Test GPT-5 using direct OpenAI SDK"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Simple test prompt
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Write a detailed, comprehensive response."},
            {"role": "user", "content": "Write a detailed around 300000 character story about a space exploration mission. Make it engaging and comprehensive with rich descriptions and dialogue."}
        ]
        
        logger.info("🚀 Testing GPT-5 with direct OpenAI SDK...")
        logger.info(f"   Requesting: ~300000 characters")
        
        response = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            # No max_tokens limit - let GPT-5 decide
        )
        
        content = response.choices[0].message.content
        
        logger.info(f"✅ Direct OpenAI Results:")
        logger.info(f"   Generated: {len(content):,} characters")
        logger.info(f"   Input tokens: {response.usage.prompt_tokens:,}")
        logger.info(f"   Output tokens: {response.usage.completion_tokens:,}")
        logger.info(f"   Total tokens: {response.usage.total_tokens:,}")
        logger.info(f"   Chars per token: {len(content) / response.usage.completion_tokens:.2f}")
        logger.info(f"   Finish reason: {response.choices[0].finish_reason}")
        
        return len(content)
        
    except Exception as e:
        logger.error(f"❌ Direct OpenAI test failed: {e}")
        return 0

def test_litellm():
    """Test GPT-5 using LiteLLM"""
    try:
        import litellm
        
        # Simple test prompt
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Write a detailed, comprehensive response."},
            {"role": "user", "content": "Write a detailed 300000 character story about a space exploration mission. Make it engaging and comprehensive with rich descriptions and dialogue."}
        ]
        
        logger.info("🚀 Testing GPT-5 with LiteLLM...")
        logger.info(f"   Requesting: ~300000 characters")
        
        response = litellm.completion(
            model="gpt-5",
            messages=messages,
            # No max_tokens - let GPT-5 decide
        )
        
        content = response.choices[0].message.content
        
        logger.info(f"✅ LiteLLM Results:")
        logger.info(f"   Generated: {len(content):,} characters")
        if hasattr(response, 'usage') and response.usage:
            logger.info(f"   Input tokens: {response.usage.prompt_tokens:,}")
            logger.info(f"   Output tokens: {response.usage.completion_tokens:,}")
            logger.info(f"   Total tokens: {response.usage.total_tokens:,}")
            logger.info(f"   Chars per token: {len(content) / response.usage.completion_tokens:.2f}")
        logger.info(f"   Finish reason: {response.choices[0].finish_reason}")
        
        return len(content)
        
    except Exception as e:
        logger.error(f"❌ LiteLLM test failed: {e}")
        return 0

def test_with_max_tokens():
    """Test GPT-5 with explicit max_tokens parameter"""
    try:
        import litellm
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Write a detailed, comprehensive response."},
            {"role": "user", "content": "Write a detailed 300000 character story about space exploration. Make it engaging with rich descriptions."}
        ]
        
        logger.info("🚀 Testing GPT-5 with max_tokens=300000...")
        
        response = litellm.completion(
            model="gpt-5",
            messages=messages
        )
        
        content = response.choices[0].message.content
        
        logger.info(f"✅ Max Tokens Test Results:")
        logger.info(f"   Generated: {len(content):,} characters")
        if hasattr(response, 'usage') and response.usage:
            logger.info(f"   Input tokens: {response.usage.prompt_tokens:,}")
            logger.info(f"   Output tokens: {response.usage.completion_tokens:,}")
            logger.info(f"   Total tokens: {response.usage.total_tokens:,}")
        logger.info(f"   Finish reason: {response.choices[0].finish_reason}")
        
        return len(content)
        
    except Exception as e:
        logger.error(f"❌ Max tokens test failed: {e}")
        return 0

def main():
    logger.info("=" * 60)
    logger.info("GPT-5 Output Limitation Investigation")
    logger.info("=" * 60)
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("❌ OPENAI_API_KEY not found in environment")
        return
    
    results = {}
    
    # Test 1: Direct OpenAI SDK
    logger.info("\n" + "=" * 40)
    logger.info("TEST 1: Direct OpenAI SDK")
    logger.info("=" * 40)
    results['direct'] = test_direct_openai()
    
    # Test 2: LiteLLM (our current approach)
    logger.info("\n" + "=" * 40)
    logger.info("TEST 2: LiteLLM (Current Approach)")
    logger.info("=" * 40)
    results['litellm'] = test_litellm()
    
    # Test 3: LiteLLM with explicit max_tokens
    logger.info("\n" + "=" * 40)
    logger.info("TEST 3: LiteLLM with max_tokens")
    logger.info("=" * 40)
    results['max_tokens'] = test_with_max_tokens()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for test, chars in results.items():
        logger.info(f"   {test:12}: {chars:,} characters")
    
    # Analysis
    if results.get('direct', 0) > results.get('litellm', 0):
        logger.info("\n🔍 ANALYSIS: Direct OpenAI generates more content than LiteLLM")
        logger.info("   → Issue may be with LiteLLM wrapper, not GPT-5 itself")
    elif all(v < 40000 for v in results.values() if v > 0):
        logger.info("\n🔍 ANALYSIS: All approaches limited to ~30K chars")
        logger.info("   → Likely OpenAI API limitation or model behavior")
    else:
        logger.info("\n🔍 ANALYSIS: Mixed results - need further investigation")

if __name__ == "__main__":
    main()