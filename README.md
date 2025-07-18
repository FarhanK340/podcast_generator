# AI Podcast Generator

Generate short podcasts using AI—powered by Groq's LLM and ElevenLabs text-to-speech!

---

## 1. Set Up the Project

Make sure Python 3.9+ is installed.

Clone the repo and install dependencies:

```bash
git clone https://github.com/your-username/ai-podcast-generator.git
cd ai-podcast-generator
pip install -r requirements.txt
```

## 2. Create a .env file

`
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id
`

## 3. Run the FastAPI Server

```bash
uvicorn podcast_generator.main:app --reload
```

This will start the app at:

`http://127.0.0.1:8000`

## 4. Test the API

Visit:
`http://127.0.0.1:8000/docs`

Use the Swagger UI to test your API interactively by uploading a topic. The API will return a podcast audio file and transcript.

## Project Structure

```
podcast_generator/
│
├── main_api.py             # FastAPI app entry point
├── podcast_generator.py    # LLM script and audio generation logic
├── requirements.txt        # List of requirements.txt
├── generated_audios/       # List of old generated audio files
├── generated_scripts/      # List of old generated script files
└── .env                    # Your API keys (not committed)
└── README.md                    # Readme file for executing the project
```