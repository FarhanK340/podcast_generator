# 🐳 FastAPI Podcast Generator - Dockerization Execution Log

## Part 1: Dockerfile and .dockerignore

### Dockerfile Contents:

```code
FROM python:3.10.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### .dockerignore Contents:

```code
.env
**pycache**/
.pyc
venv/
generated*audios/*.mp3
generated*audios/*.wav
generated_scripts/*.txt
```

### Observation:

- Files like `.env`, `__pycache__`, and output files are excluded to reduce image size and protect secrets.
- Only necessary files are included in the final Docker image.

---

## Part 2: Building the Docker Image

### Docker Build Command:

```bash
docker build -t my-podcast-api:v1.0 .
```

### Image Build Output:

- Image built successfully: `my-podcast-api:v1.0`
- Observed caching during `COPY requirements.txt` and `pip install` steps.

#### Output:

```txt
(podcastenv) farhankashif@administrator-HP-EliteBook-840-G3:~/Desktop/self/podcast_generator$ docker build -t my-podcast-api:v1.0 .
[+] Building 97.1s (11/11) FINISHED                                                                                                                                              docker:default
 => [internal] load build definition from Dockerfile                                                                                                                                       0.0s
 => => transferring dockerfile: 284B                                                                                                                                                       0.0s
 => [internal] load metadata for docker.io/library/python:3.10.12-slim                                                                                                                     0.0s
 => [internal] load .dockerignore                                                                                                                                                          0.0s
 => => transferring context: 137B                                                                                                                                                          0.0s
 => [1/6] FROM docker.io/library/python:3.10.12-slim                                                                                                                                       0.1s
 => [internal] load build context                                                                                                                                                          0.0s
 => => transferring context: 13.15kB                                                                                                                                                       0.0s
 => [2/6] WORKDIR /app                                                                                                                                                                     0.6s
 => [3/6] RUN apt-get update && apt-get install -y ffmpeg                                                                                                                                 62.3s
 => [4/6] COPY requirements.txt .                                                                                                                                                          0.1s
 => [5/6] RUN pip install -r requirements.txt                                                                                                                                             30.1s
 => [6/6] COPY . .                                                                                                                                                                         0.1s
 => exporting to image                                                                                                                                                                     3.9s
 => => exporting layers                                                                                                                                                                    3.8s
 => => writing image sha256:8ba404a978cf4d1c21cca1eb1ee2b4b5d4f1cf02c2a4c0121a47b9586c5ddb32                                                                                               0.0s
 => => naming to docker.io/library/my-podcast-api:v1.0                                                                                                                                     0.0s
```

### Image Check:

```bash
docker images
```

#### Output:

```txt
REPOSITORY                           TAG            IMAGE ID       CREATED          SIZE
my-podcast-api                       v1.0           8ba404a978cf   17 minutes ago   816MB
```

---

## Part 3: Running the Docker Container

### Initial Run:

```bash
docker run -d -p 8000:8000 --name podcast-api-container my-podcast-api:v1.0
```

#### Output:

```txt
7f8be7917021307c54bdcc1d7c1e679f7d67562811bc8b0bd1ba431f12a83285
```

### Container Check:

```bash
docker ps
```

#### Output:

```txt
CONTAINER ID   IMAGE                 COMMAND                  CREATED          STATUS          PORTS                                         NAMES
7f8be7917021   my-podcast-api:v1.0   "uvicorn main_api:ap…"   17 minutes ago   Up 17 minutes   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp   podcast-api-container
```

### Re-run with Env Variables:

```bash
docker stop podcast-api-container
docker rm podcast-api-container

docker run -d -p 8000:8000
-e GROQ_API_KEY="<`<api-key>`>"
-e ELEVENLABS_API_KEY="<`<api-key>`>"
--name podcast-api-container my-podcast-api:v1.0
```

#### Output:

- Gives the container ID as output showing successful running of the container.

```txt
2e7ace0c57a2ad90d38f89a820c9a630488b4678d1779516ce235aa6b3849d67
```

### Observation:

- Environment variables are passed securely via `-e`.

---

## Part 4: Testing the Containerized API

### Accessing Swagger UI:

- Opened `http://localhost:8000/docs` in browser.
- FastAPI docs loaded successfully.

### API Test:

- Submitted request to `/generate_podcast` with topic: `Python as a programming language`
- Response received with app/ path inside container.

- Request Data:

```json
{
  "topic": "Python as a progamming language",
  "llm_model": "llama3-8b-8192",
  "llm_provider": "grok",
  "host_voice": "21m00Tcm4TlvDq8ikWAM",
  "guest_voice": "AZnzlk1XvdvUeBnXmlld",
  "output_audio_filename": "docker_test_podcast.mp3",
  "output_script_filename": "docker_podcast_script.txt"
}
```

- Response body:

```json
{
  "success": true,
  "audio_filename": "docker_test_podcast.mp3",
  "script_filename": "docker_podcast_script.txt"
}
```

Checking in the container directory by opening its interactive shell

```bash
docker exec -it 2e7 /bin/sh
$ cd /app
$ ls
Dockerfile           README.md    docker_podcast_script.txt  example-execution-outputs.txt  generated_scripts  podcast.mp3           podcast_script.txt
Output_fast_api.txt  __pycache__  docker_test_podcast.mp3    generated_audios               main_api.py        podcast_generator.py  requirements.txt
```

The ls shows the generated files in the container.

### Observation:

- Output files not visible on host machine.

---

## Part 5: Volume Mount for Data Persistence

### Create `outputs` folder:

```bash
mkdir docker_outputs/
```

### Run with Volume Mount:

```bash
docker stop podcast-api-container
docker rm podcast-api-container

docker run -d -p 8000:8000
-e OPENAI_API_KEY="<`<your-api-key>`>"
-e ELEVENLABS_API_KEY="<`<your-api-key>`>"
-v "$(pwd)/docker_outputs:/app/docker_outputs"
--name podcast-api-container my-podcast-api:v1.0
```

- Container Id returned

```txt
6db13f49318482d96c0602a0c844afc63eb49f189a48ecb2bb76a45599bef582
```

### Test:

- Request Body:

```json
{
  "topic": "C++ as a programming language",
  "llm_model": "llama3-8b-8192",
  "llm_provider": "grok",
  "host_voice": "21m00Tcm4TlvDq8ikWAM",
  "guest_voice": "AZnzlk1XvdvUeBnXmlld",
  "output_audio_filename": "docker_test_podcast.mp3",
  "output_script_filename": "docker_test_podcast_script.txt"
}
```

- Response Body:

```json
{
  "success": true,
  "audio_filename": "docker_test_podcast.mp3",
  "script_filename": "docker_test_podcast_script.txt"
}
```

### Observation:

- Audio and text files now appear in `docker_outputs/` on host machine.
- Volume mapping enables persistent, shareable data access.

---

## Part 6: Cleanup

### Stop and Remove Container:

```bash
docker stop podcast-api-container
docker rm podcast-api-container
```

### Optional Image Removal:

```bash
docker rmi my-podcast-api:v1.0
```

---

## Reflections & Learnings

### What are Docker Images and Containers?

- **Image**: A snapshot of an application environment that is reusable and portable, to avoid any 'it works on my machine' issues.
- **Container**: A running instance of an image that is lightweight and isolated.

### Dockerfile Purpose:

- Automates the steps to set up an environment.
- Ensures consistent deployment across systems.

### EXPOSE vs -p:

- `EXPOSE 8000`: Declares the container will use port 8000.
- `-p 8000:8000`: Maps container port 8000 to host port 8000.

### Volume Mounting Importance:

- Without `-v`, files stay inside the container and are lost on deletion.
- With `-v`, files persist on the host and are accessible even after container removal.

### Challenges Faced:

- e.g., Slow base image download, solved by pulling manually
- e.g., Files not saving on host, solved via volume mapping
- e.g., Environment variables not loading until passed explicitly
  
---
