# import argparse
import os
import sys
import re
import tempfile
import requests
from dotenv import load_dotenv
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs


def generate_script_grok(topic: str, llm_model: str) -> str:

    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
        "model": llm_model
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        sys.exit(1)


def parse_script(script_text: str) -> list[dict]:
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


def generate_and_combine_audio_from_segments(
        dialogue_segments: dict,
        host_voice_id: str,
        guest_voice_id: str,
        output_audio_path: str) -> None:

    load_dotenv()
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio_segments = []

    for idx, line in enumerate(dialogue_segments):
        speaker = line["speaker"]
        text = line["text"]
        voice_id = host_voice_id if speaker == "HOST" else guest_voice_id

        try:
            print(f"Generating audio for {speaker} line {idx + 1}...")
            audio_stream = client.text_to_speech.convert(
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                optimize_streaming_latency=1,
                text=text
            )

            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tf:
                for chunk in audio_stream:
                    tf.write(chunk)
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

    final_audio.export(output_audio_path,
                       format=output_audio_path.split('.')[-1])
    print(f"Final audio saved to {output_audio_path}")
