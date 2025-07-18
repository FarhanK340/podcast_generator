import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel

from podcast_generator import (
    generate_script_grok,
    parse_script,
    generate_and_combine_audio_from_segments,
)

app = FastAPI()

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY")


class PodcastRequest(BaseModel):
    topic: str
    llm_model: str = "llama3-8b-8192"
    llm_provider: str = "grok"
    host_voice: str = "21m00Tcm4TlvDq8ikWAM"
    guest_voice: str = "AZnzlk1XvdvUeBnXmlld"
    output_audio_filename: str = "podcast.mp3"
    output_script_filename: str = "podcast_script.txt"


class PodcastResponse(BaseModel):
    success: bool
    audio_filename: str
    script_filename: str


@app.post("/generate_podcast", response_model=PodcastResponse)
def generate_podcast(req: PodcastRequest):
    try:
        script_text = generate_script_grok(req.topic, req.llm_model)
        with open(req.output_script_filename, "w") as f:
            f.write(script_text)

        segments = parse_script(script_text)
        generate_and_combine_audio_from_segments(
            segments,
            host_voice_id=req.host_voice,
            guest_voice_id=req.guest_voice,
            output_audio_path=req.output_audio_filename
        )
        
        return PodcastResponse(
            success = True,
            audio_filename = req.output_audio_filename,
            script_filename = req.output_script_filename
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
