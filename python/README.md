# god-tibo-imagen

Python SDK for sending image-generation requests to Codex's private ChatGPT-authenticated backend path.

> WARNING: This is **not** a supported public API integration. It depends on private Codex request behavior that may change without notice.

## Installation

```bash
pip install god-tibo-imagen
```

## Usage

```python
from gti import Client

client = Client(provider="private-codex")
result = client.generate_image(
    prompt="flat blue square icon",
    model="gpt-5.4",
    output_path="./out.png"
)
print(result.saved_path)
```

### Image input

You can provide existing images as additional context alongside your text prompt. Images are embedded as base64 data URLs and sent with the request.

```python
# single image
result = client.generate_image(
    prompt="Make this cat wear a hat",
    model="gpt-5.4",
    output_path="./cat-hat.png",
    image_paths="./cat.png"
)

# multiple images
result = client.generate_image(
    prompt="Combine these two styles",
    model="gpt-5.4",
    output_path="./combined.png",
    image_paths=["./style-a.png", "./style-b.png"]
)
```

Supported formats: `png`, `jpg`/`jpeg`, `gif`, `webp`.

### Dry run

```python
result = client.generate_image(
    prompt="flat blue square icon",
    dry_run=True
)
print(result["mode"])  # "dry-run"
```

## FastAPI test server

Install the server extras:

```bash
pip install -e '.[server]'
```

Run the local web UI:

```bash
uvicorn gti.server:app --host 127.0.0.1 --port 8310 --reload
```

Open `http://127.0.0.1:8310` and submit a prompt. Generated PNG files are written to `./server-generated/` and served back through `/api/images/{filename}`.

API example:

```bash
curl -sS http://127.0.0.1:8310/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"flat blue square icon","model":"gpt-5.4","dry_run":true}'
```
