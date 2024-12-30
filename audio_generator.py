import argparse
import os
import shutil
import sys
import subprocess
import requests
import json
import time
from pathlib import Path

try:
    import pyperclip
except ImportError:
    pyperclip = None

# Configuration
VOICE_ID = "OJtLHqR5g0hxcgc27j7C"
OUTPUT_DIR = Path.home() / "assistant" / "audio"
MODEL_ID = "eleven_multilingual_v2"
API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

def show_usage():
    usage = """
Usage: python elevenlabs_text_to_speech.py [OPTIONS] [TEXT]

Options:
  -p, --play         Play the audio file immediately after generation
  -f, --file FILE    Read text from specified file
  -c, --clipboard    Use the text from the clipboard
  -h, --help         Show this help message
  -d, --debug        Enable debug output

Input methods:
  1. Direct text input as argument
  2. Specified file with -f option
  3. TextToSpeech.md file (default if no other input provided)
  4. Standard input (pipe or redirect)
  5. Clipboard with -c option
"""
    print(usage)

def check_dependencies(debug=False):
    required_commands = ["mpv"]
    missing_deps = []
    for cmd in required_commands:
        if not shutil.which(cmd):
            missing_deps.append(cmd)
    if missing_deps:
        print(f"Error: Missing required dependencies: {' '.join(missing_deps)}")
        print("Please install them using your package manager.")
        sys.exit(1)
    if debug:
        print("All dependencies are satisfied.")

def create_output_dir():
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: Failed to create output directory: {OUTPUT_DIR}")
        sys.exit(1)

def get_text_content(args):
    text_content = ""
    if args.clipboard:
        if not pyperclip:
            print("Error: pyperclip module not installed. Install it using 'pip install pyperclip'.")
            sys.exit(1)
        try:
            text_content = pyperclip.paste()
        except Exception as e:
            print("Error: Failed to read from clipboard.")
            sys.exit(1)
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text_content = f.read()
        except Exception as e:
            print(f"Error: Failed to read file {args.file}")
            sys.exit(1)
    elif not sys.stdin.isatty():
        text_content = sys.stdin.read()
    elif Path("TextToSpeech.md").is_file():
        try:
            with open("TextToSpeech.md", 'r', encoding='utf-8') as f:
                text_content = f.read()
        except Exception as e:
            print("Error: Failed to read TextToSpeech.md")
            sys.exit(1)
    elif args.text:
        text_content = args.text
    else:
        print("Error: No input text provided")
        show_usage()
        sys.exit(1)

    if not text_content.strip():
        print("Error: Input text is empty")
        sys.exit(1)

    return text_content

def generate_speech(text_content, debug=False):
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY", ""),
        "Content-Type": "application/json"
    }

    if not headers["xi-api-key"]:
        print("Error: ELEVENLABS_API_KEY environment variable is not set or is empty")
        sys.exit(1)

    payload = {
        "text": text_content,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    if debug:
        print("Debug: Request JSON:")
        print(json.dumps(payload, indent=4))
        print("Debug: Making API call to ElevenLabs...")

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        if debug:
            print(f"Debug: HTTP Response Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: API request failed with HTTP code {response.status_code}")
            try:
                error_content = response.json()
                print("Error response:")
                print(json.dumps(error_content, indent=4))
            except:
                print(response.text)
            return None
        return response.content
    except Exception as e:
        print(f"Error: Failed to make API request: {e}")
        return None

def save_audio(content):
    timestamp = int(time.time())
    output_file = OUTPUT_DIR / f"{timestamp}_speech.mp3"
    try:
        with open(output_file, 'wb') as f:
            f.write(content)
        return output_file
    except Exception as e:
        print(f"Error: Failed to save audio file: {e}")
        return None

def play_audio(file_path):
    try:
        subprocess.run(["mpv", str(file_path)], check=True)
    except Exception as e:
        print("Error: Failed to play audio file")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('text', nargs='?', help='Direct text input as argument')
    parser.add_argument('-p', '--play', action='store_true', help='Play the audio file immediately after generation')
    parser.add_argument('-f', '--file', help='Read text from specified file')
    parser.add_argument('-c', '--clipboard', action='store_true', help='Use the text from the clipboard')
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')

    args = parser.parse_args()

    if args.help:
        show_usage()
        sys.exit(0)

    check_dependencies(debug=args.debug)
    create_output_dir()

    text_content = get_text_content(args)

    if args.debug:
        print("Debug: Input text content:")
        print(text_content)

    audio_content = generate_speech(text_content, debug=args.debug)
    if not audio_content:
        print("Error: Speech generation failed")
        sys.exit(1)

    output_file = save_audio(audio_content)
    if not output_file:
        print("Error: Failed to save audio file")
        sys.exit(1)

    print(f"Success! Audio file saved as: {output_file}")

    if args.play:
        print("Playing audio...")
        play_audio(output_file)

if __name__ == '__main__':
    main()