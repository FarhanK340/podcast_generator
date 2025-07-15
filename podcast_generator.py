import argparse
import os
import sys
import re
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

import requests

# Load environment variables
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def validate_api_keys(provider):
    missing_keys = []
    if provider == "grok" and not GROQ_API_KEY:
        missing_keys.append("GROQ_API_KEY")
    if not ELEVENLABS_API_KEY:
        missing_keys.append("ELEVENLABS_API_KEY")
    if missing_keys:
        print(
            f"Error: Missing API keys: {', '.join(missing_keys)} in .env file.")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate an AI podcast.")
    parser.add_argument("--topic", "-t", required=True, help="Podcast topic")
    parser.add_argument("--output_audio_file",
                        default="podcast.mp3", help="Output audio file name")
    parser.add_argument("--output_script_file",
                        default="podcast_script.txt", help="Output script text file")
    parser.add_argument("--llm_model", default="gpt-4o",
                        help="LLM model to use")
    parser.add_argument("--llm_provider", default="grok",
                        choices=["grok"], help="LLM API provider")
    parser.add_argument("--host_voice", default="21m00Tcm4TlvDq8ikWAM",
                        help="Eleven Labs voice ID for host")
    parser.add_argument("--guest_voice", default="AZnzlk1XvdvUeBnXmlld",
                        help="Eleven Labs voice ID for guest")
    return parser.parse_args()


def generate_script_grok(topic, model):
    print("Generating script using Groq...")
    prompt = (
        f"Create a podcast script on the topic: '{topic}'.\n"
        "It must have exactly 6 lines: 3 lines by HOST and 3 lines by GUEST.\n"
        "Each line should be prefixed with either 'HOST:' or 'GUEST:'.\n"
        "Alternate turns starting with HOST. No other text. No intro or outro."
    )
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [
            {"role": "system", "content": "You are a professional podcast script writer."},
            {"role": "user", "content": prompt}
        ],
        "model": model
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        sys.exit(1)


def parse_script(script_text):
    print("Parsing script...")
    lines = script_text.strip().splitlines()
    parsed = []
    for line in lines:
        match = re.match(r"^(HOST|GUEST):\s*(.+)", line.strip())
        if match:
            speaker, text = match.groups()
            parsed.append({"speaker": speaker.upper(), "text": text.strip()})
    if len(parsed) != 6:
        print(f"Error: Expected 6 lines of dialogue, got {len(parsed)}.")
        sys.exit(1)
    return parsed


def save_script(script_text, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(script_text)
        print(f"Saved script to {filename}")
    except Exception as e:
        print(f"Error saving script: {e}")
        sys.exit(1)


def generate_audio(dialogue, host_voice, guest_voice, output_file):
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio_segments = []

    for idx, line in enumerate(dialogue):
        speaker = line["speaker"]
        text = line["text"]
        voice_id = host_voice if speaker == "HOST" else guest_voice

        try:
            print(f"Generating audio for {speaker} line {idx + 1}...")
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                optimize_streaming_latency=1,
                text=text
            )

            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tf:
                tf.write(audio_stream.read())
                tf.flush()
                segment = AudioSegment.from_file(tf.name, format="mp3")
                audio_segments.append(segment)

        except Exception as e:
            print(f"Error generating audio for {speaker} line {idx + 1}: {e}")
            continue

    if not audio_segments:
        raise RuntimeError("No audio segments generated.")

    print("Combining audio segments...")
    final_audio = audio_segments[0]
    for segment in audio_segments[1:]:
        final_audio += segment

    final_audio.export(output_file, format=output_file.split('.')[-1])
    print(f"Final audio saved to {output_file}")

def main():
    print("Starting AI Podcast Generation...")
    args = parse_args()
    validate_api_keys(args.llm_provider)

    script_text = generate_script_grok(args.topic, args.llm_model)

    save_script(script_text, args.output_script_file)

    parsed_script = parse_script(script_text)

    generate_audio(parsed_script, args.host_voice, args.guest_voice, args.output_audio_file)

if __name__ == "__main__":
    main()
