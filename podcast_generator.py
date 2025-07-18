# import argparse
import os
import sys
import re
import tempfile
import requests
from dotenv import load_dotenv
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")



def generate_script_grok(topic: str, llm_model: str) -> str:


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


def parse_script(script_text: str) -> list[dict[str, str]]:
    print("Parsing script...")
    
    lines = script_text.strip().splitlines()
    segments = []

    for idx, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith("HOST:"):
            segments.append({"speaker": "host", "text": line[5:].strip()})
        elif line.startswith("GUEST:"):
            segments.append({"speaker": "guest", "text": line[6:].strip()})
        else:
            print(f"Warning: Line {idx} is not labeled correctly and was skipped.")

    if not segments:
        raise ValueError("No valid HOST or GUEST lines found in the script.")
    if len(segments) < 6:
        print(f"Warning: Expected at least 6 lines of dialogue, but got {len(segments)}.")

    return segments


def generate_and_combine_audio_from_segments(
        dialogue_segments: list[dict[str, str]],
        host_voice_id: str,
        guest_voice_id: str,
        output_audio_path: str) -> None:

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
