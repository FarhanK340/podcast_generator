FROM python:3.10.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000"]