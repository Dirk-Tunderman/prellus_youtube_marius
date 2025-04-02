"""
Enhanced Flask backend for YouTube Transcript Processor with structured prompt fields
Running on port 5001
Features:
- Process YouTube transcripts with customizable prompts
- Save prompts to storage for later use
- Load previously saved prompts
"""

from flask_cors import CORS
import sys
import datetime
import os
import uuid
import yaml
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file
import shutil
import re


# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import the youtube_to_audio function from the scripts directory
from scripts.youtube_to_audio import youtube_to_audio, load_config

# Disable buffering to ensure prints are immediately visible in logs
sys.stdout.reconfigure(line_buffering=True)
# If using Python < 3.9, use this instead:
# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Ensure prompt storage directory exists
PROMPT_STORAGE_DIR = os.path.join(project_root, "app/data/stored_prompts")
os.makedirs(PROMPT_STORAGE_DIR, exist_ok=True)


def save_prompt_to_file(prompt_data, prompt_name):
    """
    Save a prompt to a JSON file in the stored_prompts directory

    Args:
        prompt_data: Dictionary containing the prompt fields
        prompt_name: Name of the prompt to save

    Returns:
        Dictionary with information about the saved file
    """
    # Create a unique identifier
    unique_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()

    # Create the prompt structure
    prompt_file = {
        "meta_data": {
            "prompt_name": prompt_name,
            "date": timestamp,
            "unique_identifier": unique_id,
        },
        "prompt": {
            "Role": prompt_data.get("yourRole", ""),
            "Script_Structure": prompt_data.get("scriptStructure", ""),
            "Tone_Style": prompt_data.get("toneAndStyle", ""),
            "Retention_Flow": prompt_data.get("retentionAndFlow", ""),
            "Additional_instructions": prompt_data.get("additionalInstructions", ""),
        },
    }

    # Create filename based on unique ID
    filename = f"{unique_id}.json"
    file_path = os.path.join(PROMPT_STORAGE_DIR, filename)

    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(prompt_file, f, indent=2)

    return {
        "success": True,
        "filename": filename,
        "path": file_path,
        "prompt_name": prompt_name,
        "unique_id": unique_id,
        "timestamp": timestamp,
    }


def get_all_prompts():
    """
    Get a list of all saved prompts

    Returns:
        List of prompt metadata from all saved JSON files
    """
    prompts = []

    # Get all JSON files in the prompts directory
    for filename in os.listdir(PROMPT_STORAGE_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(PROMPT_STORAGE_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    prompt_data = json.load(f)

                # Extract metadata and add to list
                if "meta_data" in prompt_data:
                    meta = prompt_data["meta_data"]
                    prompts.append(
                        {
                            "unique_id": meta.get("unique_identifier"),
                            "prompt_name": meta.get("prompt_name"),
                            "date": meta.get("date"),
                            "filename": filename,
                        }
                    )
            except Exception as e:
                print(f"Error reading prompt file {filename}: {e}")

    # Sort by date (newest first)
    prompts.sort(key=lambda x: x.get("date", ""), reverse=True)
    return prompts


def get_prompt_by_id(unique_id):
    """
    Get a specific prompt by its unique ID

    Args:
        unique_id: The unique identifier of the prompt

    Returns:
        The prompt data if found, None otherwise
    """
    filename = f"{unique_id}.json"
    file_path = os.path.join(PROMPT_STORAGE_DIR, filename)

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading prompt file {filename}: {e}")
            return None

    return None


@app.route("/api/transcripts/process", methods=["POST"])
def process_transcript():
    """Process a YouTube transcript request with structured prompt fields and detailed error handling"""
    try:
        data = request.json

        # Extract and print the data
        url = data.get("url", "Not provided")
        title = data.get("title", "")  # Extract title from request
        prompt_data = data.get("promptData", {})
        duration = data.get("duration", "Not provided")
        voice = data.get("voice", "Not provided")
        speed = data.get("speed", "Not provided")
        print(f"\n\ndata in da beginnenning: {data}\n\n")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n===== RECEIVED TRANSCRIPT PROCESSING REQUEST =====")
        print(f"TIMESTAMP: {timestamp}")
        print(f"URL: {url}")
        print(f"TITLE: {title}")
        print(f"Duration: {duration} minutes")

        # Log structured prompt fields
        print("=== STRUCTURED PROMPT FIELDS ===")
        for field, value in prompt_data.items():
            print(
                f"{field}: {value[:50]}..."
                if len(str(value)) > 50
                else f"{field}: {value}"
            )
        print("=================================================\n")

        # Format the structured prompt data for processing
        # Create a combined prompt with all fields
        combined_prompt = ""
        if prompt_data.get("yourRole"):
            combined_prompt += f"YOUR ROLE:\n{prompt_data['yourRole']}\n\n"
        if prompt_data.get("scriptStructure"):
            combined_prompt += (
                f"SCRIPT STRUCTURE:\n{prompt_data['scriptStructure']}\n\n"
            )
        if prompt_data.get("toneAndStyle"):
            combined_prompt += f"TONE & STYLE:\n{prompt_data['toneAndStyle']}\n\n"
        if prompt_data.get("retentionAndFlow"):
            combined_prompt += (
                f"RETENTION & FLOW TECHNIQUES:\n{prompt_data['retentionAndFlow']}\n\n"
            )
        if prompt_data.get("additionalInstructions"):
            combined_prompt += (
                f"ADDITIONAL INSTRUCTIONS:\n{prompt_data['additionalInstructions']}\n\n"
            )

        # Create JSON data to pass to the pipeline
        json_data = {
            "timestamp": timestamp,
            "url": url,
            "title": title,  # Add title to the JSON data
            "prompt": combined_prompt,  # Combined prompt text
            "promptData": prompt_data,  # Structured prompt data
            "duration": duration,
        }

        sys.stdout.flush()

        # Detailed error handling for config loading
        try:
            config_path = os.path.join(project_root, "app/config/config.yaml")
            print(f"Loading config from: {config_path}")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found at {config_path}")

            config = load_config(config_path)
            print("Config loaded successfully")

            # Inject structured prompt data into config
            if "ai" not in config:
                config["ai"] = {}

            # Add combined prompt as custom_prompt
            config["ai"]["custom_prompt"] = combined_prompt

            # Add voice and speed to config
            config["ai"]["voice_pack"] = voice
            config["ai"]["speed"] = speed

            # Also store structured prompt data
            config["ai"]["prompt_structure"] = prompt_data


            print("Injected structured prompt data into config")

        except Exception as config_error:
            error_msg = f"Config error: {str(config_error)}"
            print(error_msg)
            return jsonify({"error": error_msg}), 500

        # Run the youtube_to_audio pipeline with better error handling
        if url != "Not provided":
            try:
                print(f"Starting youtube_to_audio for URL: {url}")
                # Pass json_data to the youtube_to_audio function which now includes the title
                result = youtube_to_audio(json_data["url"], config, json_data=json_data)
                print(f"Pipeline execution started for URL: {url}")
                print(
                    f"Results will be saved to: {result.get('video_dir', 'Unknown location')}"
                )
            except Exception as pipeline_error:
                error_msg = f"Pipeline error: {str(pipeline_error)}"
                print(error_msg)
                import traceback

                print(traceback.format_exc())
                return jsonify({"error": error_msg}), 500

        # Return success response
        return jsonify(
            {
                "id": "transcript_123",
                "title": title or "Processed Video",  # Use the title in the response
                "status": "processing",
                "message": "Transcript processing started",
            }
        )

    except Exception as e:
        print(f"General error: {str(e)}")
        import traceback

        print(traceback.format_exc())
        sys.stdout.flush()
        return jsonify({"error": str(e)}), 500


@app.route("/api/transcripts", methods=["GET"])
def get_transcripts():
    """Return a list of mock transcripts"""
    print("Getting transcript list")
    sys.stdout.flush()  # Force flush the output
    return jsonify(
        [
            {
                "id": "1",
                "title": "Introduction to AI",
                "url": "https://www.youtube.com/watch?v=abc123",
                "createdAt": "2023-04-15",
                "status": "completed",
                "audioStatus": "completed",
                "audioUrl": "https://example.com/audio/transcript_1.mp3",
            },
            {
                "id": "2",
                "title": "Machine Learning Fundamentals",
                "url": "https://www.youtube.com/watch?v=def456",
                "createdAt": "2023-05-20",
                "status": "completed",
                "audioStatus": None,
            },
        ]
    )


@app.route("/api/audio/generate/<transcript_id>", methods=["POST"])
def generate_audio(transcript_id):
    """Generate audio for a transcript"""
    print(f"Generating audio for transcript: {transcript_id}")
    sys.stdout.flush()  # Force flush the output
    return jsonify(
        {
            "transcriptId": transcript_id,
            "status": "completed",
            "url": f"https://example.com/audio/transcript_{transcript_id}.mp3",
            "message": "Audio generation completed successfully",
        }
    )


@app.route("/api/prompts/save", methods=["POST"])
def save_prompt():
    """Save a prompt to storage"""
    try:
        data = request.json
        prompt_data = data.get("promptData", {})
        prompt_name = data.get("promptName", "Unnamed Prompt")

        # Validate prompt name
        if not prompt_name or len(prompt_name.strip()) == 0:
            prompt_name = "Unnamed Prompt"

        print(f"Saving prompt: {prompt_name}")

        # Save the prompt
        result = save_prompt_to_file(prompt_data, prompt_name)

        print(f"Prompt saved successfully: {result['filename']}")
        return jsonify(
            {
                "success": True,
                "message": "Prompt saved successfully",
                "promptId": result["unique_id"],
                "promptName": result["prompt_name"],
            }
        )

    except Exception as e:
        print(f"Error saving prompt: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/prompts", methods=["GET"])
def list_prompts():
    """Get a list of all saved prompts"""
    try:
        prompts = get_all_prompts()
        return jsonify(prompts)
    except Exception as e:
        print(f"Error listing prompts: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/prompts/<prompt_id>", methods=["GET"])
def get_prompt(prompt_id):
    """Get a specific prompt by ID"""
    try:
        prompt = get_prompt_by_id(prompt_id)
        if prompt:
            # Convert from storage format to frontend format
            frontend_format = {
                "promptData": {
                    "yourRole": prompt["prompt"].get("Role", ""),
                    "scriptStructure": prompt["prompt"].get("Script_Structure", ""),
                    "toneAndStyle": prompt["prompt"].get("Tone_Style", ""),
                    "retentionAndFlow": prompt["prompt"].get("Retention_Flow", ""),
                    "additionalInstructions": prompt["prompt"].get(
                        "Additional_instructions", ""
                    ),
                },
                "metaData": prompt["meta_data"],
            }
            return jsonify(frontend_format)
        else:
            return jsonify({"success": False, "error": "Prompt not found"}), 404
    except Exception as e:
        print(f"Error retrieving prompt: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test", methods=["GET"])
def test():
    """Test endpoint to verify API is working"""
    print("API test endpoint accessed")
    sys.stdout.flush()  # Force flush the output
    return jsonify({"status": "ok", "message": "API is working on port 5001"})


@app.route("/", methods=["GET"])
def home():
    """Home page with API info"""
    return """
    <html>
    <head>
        <title>YouTube Transcript API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #4285f4;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                margin: 10px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            a {
                color: #4285f4;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>YouTube Transcript Processor API</h1>
        <p>Running on port 5001. Available endpoints:</p>
        <ul>
            <li><a href="/api/test">/api/test</a> - Test API connectivity</li>
            <li><a href="/api/transcripts">/api/transcripts</a> - Get mock transcripts</li>
            <li><b>/api/transcripts/process</b> - POST endpoint for processing transcripts</li>
            <li><b>/api/audio/generate/{transcript_id}</b> - POST endpoint for generating audio</li>
        </ul>
    </body>
    </html>
    """


@app.route("/api/prompts/<prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    """Delete a specific prompt by ID"""
    try:
        # Construct the file path
        filename = f"{prompt_id}.json"
        file_path = os.path.join(PROMPT_STORAGE_DIR, filename)

        # Check if the file exists
        if os.path.exists(file_path):
            # Delete the file
            os.remove(file_path)
            print(f"Prompt {prompt_id} deleted successfully")
            return jsonify(
                {"success": True, "message": f"Prompt {prompt_id} deleted successfully"}
            )
        else:
            print(f"Prompt {prompt_id} not found for deletion")
            return jsonify({"success": False, "error": "Prompt not found"}), 404
    except Exception as e:
        print(f"Error deleting prompt: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects", methods=["GET"])
def get_projects():
    """Get a list of all transcript projects"""
    try:
        projects = []
        transcripts_dir = os.path.join(project_root, "app/data/transcripts")
        # Ensure the directory exists
        if not os.path.exists(transcripts_dir):
            return jsonify([])

        # List all directories in the transcripts folder
        for project_name in os.listdir(transcripts_dir):
            project_path = os.path.join(transcripts_dir, project_name)
            print(f"Project path: {project_path}")
            # Skip non-directories and hidden folders
            if not os.path.isdir(project_path) or project_name.startswith("."):
                continue

            # Check for metadata.json
            metadata_path = os.path.join(project_path, "metadata.json")
            metadata = {}
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                except Exception as e:
                    print(f"Error reading metadata for {project_name}: {e}")

            # Extract date safely - ensure it's a string
            date_value = metadata.get("timestamp", "Unknown")
            if not isinstance(date_value, str):
                date_str = str(date_value)
            else:
                date_str = date_value

            # Check for transcript file
            transcript_path = os.path.join(
                project_path, "processed", "narrative_transcript.txt"
            )
            has_transcript = os.path.exists(transcript_path)

            # Check for audio file (look for any .wav file in the audio directory)
            audio_dir = os.path.join(project_path, "audio")
            audio_files = []
            if os.path.exists(audio_dir):
                audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]

            # Create project info
            project_info = {
                "id": project_name,
                "name": metadata.get("title", project_name),
                "date": date_str,
                "hasTranscript": has_transcript,
                "audioFiles": audio_files,
                "url": metadata.get("url", ""),
            }

            projects.append(project_info)

        # Sort projects by creation date (based on folder name as fallback)
        projects.sort(key=lambda x: x.get("id", ""), reverse=True)

        return jsonify(projects)

    except Exception as e:
        print(f"Error getting projects: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/transcript", methods=["GET"])
def get_transcript(project_id):
    """Get the narrative transcript text for a project"""
    try:
        transcript_path = os.path.join(
            project_root,
            "app/data/transcripts",
            project_id,
            "processed",
            "narrative_transcript.txt",
        )

        if os.path.exists(transcript_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()

            return jsonify({"projectId": project_id, "text": transcript_text})
        else:
            return jsonify({"error": "Transcript not found"}), 404

    except Exception as e:
        print(f"Error getting transcript: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/transcript/download", methods=["GET"])
def download_transcript(project_id):
    """Download the narrative transcript file"""
    try:
        transcript_path = os.path.join(
            project_root,
            "app/data/transcripts",
            project_id,
            "processed",
            "narrative_transcript.txt",
        )

        if os.path.exists(transcript_path):
            # Get project name for better filename
            metadata_path = os.path.join(
                project_root, "app/data/transcripts", project_id, "metadata.json"
            )

            project_name = project_id
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        project_name = metadata.get("title", project_id)
                except:
                    # Use default project_id if metadata can't be read
                    pass

            # Replace invalid filename characters
            project_name = (
                project_name.replace("/", "_").replace("\\", "_").replace(":", "_")
            )
            filename = f"{project_name}_transcript.txt"

            return send_file(
                transcript_path,
                as_attachment=True,
                download_name=filename,
                mimetype="text/plain",
            )
        else:
            return jsonify({"error": "Transcript file not found"}), 404

    except Exception as e:
        print(f"Error downloading transcript: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>/audio/<filename>", methods=["GET"])
def download_audio(project_id, filename):
    """Download audio file"""
    try:
        # Security check to prevent directory traversal attacks
        if ".." in filename or filename.startswith("/"):
            return jsonify({"error": "Invalid filename"}), 400

        audio_path = os.path.join(
            project_root, "app/data/transcripts", project_id, "audio", filename
        )

        if os.path.exists(audio_path) and filename.endswith(".wav"):
            return send_file(
                audio_path,
                as_attachment=True,
                download_name=filename,
                mimetype="audio/wav",
            )
        else:
            return jsonify({"error": "Audio file not found"}), 404

    except Exception as e:
        print(f"Error downloading audio: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete an entire project folder"""
    print(f"Deleting project: {project_id}")
    try:
        # Security check to prevent directory traversal attacks
        if ".." in project_id or project_id.startswith("/"):
            return jsonify({"error": "Invalid project ID"}), 400

        project_path = os.path.join(project_root, "app/data/transcripts", project_id)

        if os.path.exists(project_path) and os.path.isdir(project_path):
            # Delete the entire project directory
            shutil.rmtree(project_path)
            print(f"Project {project_id} deleted successfully")

            return jsonify(
                {
                    "success": True,
                    "message": f"Project {project_id} deleted successfully",
                }
            )
        else:
            return jsonify({"error": "Project not found"}), 404

    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/apikeys", methods=["GET"])
def get_api_keys():
    """Get information about configured API keys (without revealing the actual keys)"""
    try:
        # Get environment variables
        api_keys = {
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY")),
            "qwen": bool(os.environ.get("QWEN_API_KEY")),
        }

        # Return only which keys are configured (true/false), not the actual keys
        return jsonify(api_keys)
    except Exception as e:
        print(f"Error retrieving API keys: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/apikeys", methods=["POST"])
def save_api_key():
    """Save an API key to the .env file"""
    try:
        data = request.json
        provider = data.get("provider")
        key = data.get("key")

        if not provider or not key:
            return jsonify({"error": "Provider and key are required"}), 400

        # Validate the provider
        valid_providers = ["openai", "gemini", "anthropic", "deepseek", "qwen"]
        if provider not in valid_providers:
            return jsonify({"error": "Invalid provider"}), 400

        # Define the environment variable name based on provider
        env_var_name = f"{provider.upper()}_API_KEY"

        # Path to .env file
        env_path = os.path.join(project_root, ".env")

        # Read current .env file content
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_content = f.read()

        # Check if the key already exists in the file
        key_pattern = re.compile(rf"^{env_var_name}=.*$", re.MULTILINE)
        if key_pattern.search(env_content):
            # Replace existing key
            env_content = key_pattern.sub(f"{env_var_name}={key}", env_content)
        else:
            # Add new key at the end
            if env_content and not env_content.endswith("\n"):
                env_content += "\n"
            env_content += f"{env_var_name}={key}\n"

        # Write back to .env file
        with open(env_path, "w") as f:
            f.write(env_content)

        # Also update current environment variables
        os.environ[env_var_name] = key

        print(f"API key for {provider} saved successfully")
        return jsonify({"success": True})

    except Exception as e:
        print(f"Error saving API key: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/apikeys/<provider>", methods=["DELETE"])
def delete_api_key(provider):
    """Delete an API key from the .env file"""
    try:
        # Validate the provider
        valid_providers = ["openai", "gemini", "anthropic", "deepseek", "qwen"]
        if provider not in valid_providers:
            return jsonify({"error": "Invalid provider"}), 400

        # Define the environment variable name based on provider
        env_var_name = f"{provider.upper()}_API_KEY"

        # Path to .env file
        env_path = os.path.join(project_root, ".env")

        if not os.path.exists(env_path):
            return jsonify({"error": ".env file not found"}), 404

        # Read current .env file content
        with open(env_path, "r") as f:
            env_content = f.read()

        # Check if the key exists in the file
        key_pattern = re.compile(rf"^{env_var_name}=.*$", re.MULTILINE)
        if key_pattern.search(env_content):
            # Replace with empty value
            env_content = key_pattern.sub(f"{env_var_name}=", env_content)

            # Write back to .env file
            with open(env_path, "w") as f:
                f.write(env_content)

            # Remove from current environment variables or set to empty
            os.environ[env_var_name] = ""

            print(f"API key for {provider} deleted successfully")
            return jsonify({"success": True})
        else:
            return jsonify({"error": f"No API key found for {provider}"}), 404

    except Exception as e:
        print(f"Error deleting API key: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/defaultmodel", methods=["GET"])
def get_default_model():
    """Get the currently configured default model"""
    try:
        # Path to config file
        config_path = os.path.join(project_root, "app/config/config.yaml")

        # If config file doesn't exist, return empty
        if not os.path.exists(config_path):
            return jsonify({"model": ""})

        # Load the config
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}

        # Get the model from config
        model = ""
        if "ai" in config and "model" in config["ai"]:
            model = config["ai"]["model"]

        return jsonify({"model": model})

    except Exception as e:
        print(f"Error retrieving default model: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/defaultmodel", methods=["POST"])
def save_default_model():
    """Save the default model to configuration"""
    try:
        data = request.json
        model = data.get("model")

        if not model:
            return jsonify({"error": "Model is required"}), 400

        # Path to config file
        config_path = os.path.join(project_root, "app/config/config.yaml")

        # Load existing config or create new one
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

        # Ensure ai section exists
        if "ai" not in config:
            config["ai"] = {}

        # Update model
        config["ai"]["model"] = model

        # Save the config
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        print(f"Default model set to: {model}")
        return jsonify({"success": True})

    except Exception as e:
        print(f"Error saving default model: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/models", methods=["GET"])
def get_available_models():
    """Get a list of available models based on configured API keys"""
    try:
        # Check which API keys are configured
        api_keys = {
            "openai": bool(os.environ.get("OPENAI_API_KEY")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY")),
            "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY")),
            "qwen": bool(os.environ.get("QWEN_API_KEY")),
        }

        # Define all available models
        all_models = [
            {
                "value": "gpt-3.5-turbo",
                "label": "OpenAI GPT-3.5 Turbo",
                "provider": "openai",
            },
            {"value": "gpt-4", "label": "OpenAI GPT-4", "provider": "openai"},
            {
                "value": "gpt-4-turbo",
                "label": "OpenAI GPT-4 Turbo",
                "provider": "openai",
            },
            {"value": "gemini-pro", "label": "Google Gemini Pro", "provider": "gemini"},
            {
                "value": "gemini-1.5-pro",
                "label": "Google Gemini 1.5 Pro",
                "provider": "gemini",
            },
            {
                "value": "gemini-2.0-flash-lite",
                "label": "Google Gemini 2.0 Flash Lite",
                "provider": "gemini",
            },
            {
                "value": "claude-3-opus-20240229",
                "label": "Anthropic Claude 3 Opus",
                "provider": "anthropic",
            },
            {
                "value": "claude-3-sonnet-20240229",
                "label": "Anthropic Claude 3 Sonnet",
                "provider": "anthropic",
            },
            {
                "value": "claude-3-haiku-20240307",
                "label": "Anthropic Claude 3 Haiku",
                "provider": "anthropic",
            },
            {
                "value": "deepseek-chat",
                "label": "DeepSeek Chat",
                "provider": "deepseek",
            },
        ]

        # Mark which models are available based on API keys
        available_models = []
        for model in all_models:
            model_copy = model.copy()
            model_copy["available"] = api_keys.get(model["provider"], False)
            available_models.append(model_copy)

        return jsonify(available_models)

    except Exception as e:
        print(f"Error retrieving available models: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Add a route to override model for a specific processing job
@app.route("/api/transcripts/process/model", methods=["POST"])
def process_with_model():
    """Process a transcript with a specific model override"""
    try:
        data = request.json
        youtube_url = data.get("url")
        model = data.get("model")

        if not youtube_url or not model:
            return jsonify({"error": "URL and model are required"}), 400

        # Create a copy of the request data for processing
        process_data = data.copy()

        # Add model override
        if "config" not in process_data:
            process_data["config"] = {}
        if "ai" not in process_data["config"]:
            process_data["config"]["ai"] = {}

        process_data["config"]["ai"]["model"] = model

        # Forward to the regular processing endpoint
        return process_transcript(process_data)

    except Exception as e:
        print(f"Error in model override processing: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n========== YouTube Transcript Processor API ==========")
    print(f"STARTED AT: {timestamp}")
    print(f"Server running at: http://localhost:5001")
    print(f"Test the API at: http://localhost:5001/api/test")
    print(f"======================================================\n")
    sys.stdout.flush()  # Force flush the output
    app.run(debug=True, host="0.0.0.0", port=5001)
