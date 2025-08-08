#!/usr/bin/env python3
"""
Test the new simple processor method using existing transcript
"""

import os
import sys
import json
import yaml

# Change to app directory
os.chdir('app')
sys.path.insert(0, '.')

def test_new_method():
    """Test the new method with existing transcript."""
    
    # Load existing transcript
    transcript_dir = "data/transcripts/X0tAVPDIR9I_20250805_122037"
    raw_transcript_path = os.path.join(transcript_dir, "raw", "transcript.txt")
    
    if not os.path.exists(raw_transcript_path):
        print(f"❌ Transcript not found: {raw_transcript_path}")
        return False
    
    with open(raw_transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
    
    print("🧪 Testing New Simple Method")
    print("=" * 50)
    print(f"📝 Transcript length: {len(transcript_text):,} characters")
    print(f"📁 Using transcript: {transcript_dir}")
    
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Modify config for testing - test response-aware system
    config['ai']['length'] = 3  # 3 minutes target to test response-aware generation
    config['ai']['prompt_script_structure'] = """
    Chapter 1: Opening and Introduction (40% of content)
    Chapter 2: Main Development (35% of content)
    Chapter 3: Conclusion and Wrap-up (25% of content)
    """
    config['ai']['prompt_role'] = "You are an expert storyteller who creates engaging narratives."
    config['ai']['prompt_tone_style'] = "Conversational and engaging"
    config['ai']['prompt_script_structure'] = "Create a clear beginning, middle, and end"
    
    print(f"🎯 Target: {config['ai']['length']} minute(s)")
    print(f"🤖 Model: {config['ai']['model']}")
    print("=" * 50)
    
    try:
        # Import and test the processor
        # Import the simple processor directly to avoid TTS dependencies
        from src.transcript_pipeline.processor.simple_processor import process_simple_transcript
        
        # Create a test output directory
        test_output_dir = os.path.join(transcript_dir, "test_simple_output")
        os.makedirs(test_output_dir, exist_ok=True)
        
        # Process using the new method
        print("🚀 Starting processing with new simple method...")
        # Load transcript text
        transcript_path = os.path.join(transcript_dir, "raw", "transcript.json")
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        # Extract text from transcript
        if isinstance(transcript_data, list):
            transcript_text = " ".join([entry.get("text", "") for entry in transcript_data])
        else:
            transcript_text = transcript_data.get("text", "")

        # Process using simple processor directly
        processed_text = process_simple_transcript(
            transcript_text=transcript_text,
            config=config,
            output_dir=test_output_dir,
            mock_mode=False
        )

        # Create result structure for compatibility
        processed_file = os.path.join(test_output_dir, "narrative_transcript.txt")
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(processed_text)

        result = {
            "processed_file": processed_file,
            "metadata": {
                "original_length": len(transcript_text),
                "processed_length": len(processed_text),
                "processing_method": "simple"
            }
        }
        
        print("✅ Processing completed!")
        print(f"📊 Results:")
        print(f"   Processed file: {result.get('processed_file')}")
        print(f"   Processing method: {result.get('metadata', {}).get('processing_method')}")
        print(f"   Original length: {result.get('metadata', {}).get('original_length'):,} chars")
        print(f"   Processed length: {result.get('metadata', {}).get('processed_length'):,} chars")
        
        # Read the result
        processed_file = result.get('processed_file')
        if processed_file and os.path.exists(processed_file):
            with open(processed_file, 'r', encoding='utf-8') as f:
                processed_content = f.read()
            
            ratio = len(processed_content) / len(transcript_text)
            print(f"   Length ratio: {ratio:.2f}x")
            
            # Show a preview
            print("\n📖 Preview of processed content:")
            print("-" * 50)
            print(processed_content[:500] + "..." if len(processed_content) > 500 else processed_content)
            print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_new_method()
    print(f"\n{'✅ Test PASSED' if success else '❌ Test FAILED'}")
    sys.exit(0 if success else 1)
