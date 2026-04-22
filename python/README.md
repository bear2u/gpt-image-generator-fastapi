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

You can provide an existing image as additional context alongside your text prompt. The image is embedded as a base64 data URL and sent with the request.

```python
result = client.generate_image(
    prompt="Make this cat wear a hat",
    model="gpt-5.4",
    output_path="./cat-hat.png",
    image_path="./cat.png"
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
