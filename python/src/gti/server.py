from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .client import Client, GenerateImageResult
from .errors import CodexError


DEFAULT_OUTPUT_DIR = Path.cwd() / "server-generated"


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    provider: str = "private-codex"
    dry_run: bool = False
    debug: bool = False


class GenerateResponse(BaseModel):
    mode: str
    warnings: list[str]
    response_id: str | None = None
    session_id: str | None = None
    saved_path: str | None = None
    image_url: str | None = None
    revised_prompt: str | None = None
    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None


def _make_output_path(output_dir: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return output_dir / f"image-{timestamp}-{uuid.uuid4().hex[:10]}.png"


def _result_to_response(result: GenerateImageResult, output_dir: Path) -> GenerateResponse:
    image_url = None
    if result.saved_path:
        saved_path = Path(result.saved_path).resolve()
        try:
            relative = saved_path.relative_to(output_dir.resolve())
        except ValueError:
            relative = None
        if relative is not None and len(relative.parts) == 1:
            image_url = f"/api/images/{relative.name}"

    return GenerateResponse(
        mode=result.mode,
        warnings=result.warnings,
        response_id=result.response_id,
        session_id=result.session_id,
        saved_path=result.saved_path,
        image_url=image_url,
        revised_prompt=result.revised_prompt,
        request=result.request,
        response=result.response,
    )


def create_app(
    *,
    client_factory: Callable[..., Client] = Client,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> FastAPI:
    app = FastAPI(title="GPT2-imagen server", version="0.2.0")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return INDEX_HTML

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/generate", response_model=GenerateResponse)
    async def generate(payload: GenerateRequest) -> GenerateResponse:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=422, detail="Prompt is required.")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = _make_output_path(output_dir)

        def run_generation() -> GenerateImageResult:
            client = client_factory(provider=payload.provider)
            return client.generate_image(
                prompt=prompt,
                model=payload.model,
                output_path=str(output_path),
                dry_run=payload.dry_run,
                debug=payload.debug,
                debug_dir=str(output_dir / "debug") if payload.debug else None,
            )

        try:
            result = await run_in_threadpool(run_generation)
        except CodexError as error:
            status = getattr(error, "status", 502) or 502
            raise HTTPException(
                status_code=status,
                detail={"message": str(error), "code": error.code},
            ) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        return _result_to_response(result, output_dir)

    @app.get("/api/images/{filename}")
    async def get_image(filename: str) -> FileResponse:
        if not re.match(r"^image-[A-Za-z0-9-]+\.png$", filename):
            raise HTTPException(status_code=404, detail="Image not found.")

        image_path = (output_dir / filename).resolve()
        try:
            image_path.relative_to(output_dir.resolve())
        except ValueError as error:
            raise HTTPException(status_code=404, detail="Image not found.") from error

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found.")

        return FileResponse(image_path, media_type="image/png")

    return app


app = create_app()


INDEX_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GPT2-imagen</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f3ee;
      --surface: #fffdf8;
      --ink: #141412;
      --muted: #6b675f;
      --line: #ddd7cb;
      --accent: #0f766e;
      --accent-ink: #ffffff;
      --danger: #a33a2c;
      --code: #24211d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    main {
      min-height: 100svh;
      display: grid;
      grid-template-columns: minmax(320px, 480px) minmax(0, 1fr);
    }
    aside {
      border-right: 1px solid var(--line);
      padding: 32px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      background: var(--surface);
    }
    .brand {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      line-height: 1.1;
      font-weight: 760;
    }
    .status {
      min-width: 72px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      text-align: center;
      color: var(--muted);
      font-size: 12px;
    }
    label {
      display: block;
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 650;
    }
    textarea, input, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      color: var(--ink);
      font: inherit;
      outline: none;
    }
    textarea {
      min-height: 180px;
      resize: vertical;
      padding: 14px;
      line-height: 1.45;
    }
    input, select {
      height: 42px;
      padding: 0 12px;
    }
    textarea:focus, input:focus, select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .toggle {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
    }
    .toggle input { width: 18px; height: 18px; }
    button {
      height: 46px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: var(--accent-ink);
      cursor: pointer;
      font: inherit;
      font-weight: 720;
      transition: transform 160ms ease, opacity 160ms ease;
    }
    button:hover { transform: translateY(-1px); }
    button:disabled {
      cursor: wait;
      opacity: 0.62;
      transform: none;
    }
    .hint {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin: 0;
    }
    section {
      padding: 32px;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      gap: 20px;
      min-width: 0;
    }
    .result-head {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
    }
    h2 {
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
    }
    .meta {
      color: var(--muted);
      font-size: 13px;
      text-align: right;
    }
    .preview {
      min-height: 420px;
      border: 1px dashed #c9c0b2;
      border-radius: 8px;
      display: grid;
      place-items: center;
      overflow: hidden;
      background:
        linear-gradient(45deg, rgba(20, 20, 18, 0.04) 25%, transparent 25%),
        linear-gradient(-45deg, rgba(20, 20, 18, 0.04) 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, rgba(20, 20, 18, 0.04) 75%),
        linear-gradient(-45deg, transparent 75%, rgba(20, 20, 18, 0.04) 75%);
      background-size: 28px 28px;
      background-position: 0 0, 0 14px, 14px -14px, -14px 0;
    }
    .preview img {
      display: block;
      max-width: min(100%, 900px);
      max-height: calc(100svh - 220px);
      object-fit: contain;
      opacity: 0;
      transform: scale(0.985);
      animation: reveal 260ms ease forwards;
    }
    .empty {
      max-width: 360px;
      color: var(--muted);
      text-align: center;
      line-height: 1.5;
    }
    pre {
      margin: 0;
      max-height: 210px;
      overflow: auto;
      border-radius: 8px;
      background: var(--code);
      color: #f8f3ea;
      padding: 14px;
      font-size: 12px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .error { color: var(--danger); }
    @keyframes reveal {
      to { opacity: 1; transform: scale(1); }
    }
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); padding: 22px; }
      section { padding: 22px; }
      .row { grid-template-columns: 1fr; }
      .preview { min-height: 320px; }
      .result-head { align-items: start; flex-direction: column; }
      .meta { text-align: left; }
    }
  </style>
</head>
<body>
  <main>
    <aside>
      <div class="brand">
        <h1>GPT2-imagen</h1>
        <div class="status" id="status">ready</div>
      </div>

      <form id="form">
        <label for="prompt">Prompt</label>
        <textarea id="prompt" name="prompt" required>flat blue square icon, centered, clean png</textarea>

        <div class="row" style="margin-top: 14px;">
          <div>
            <label for="model">Model</label>
            <input id="model" name="model" value="gpt-5.4" />
          </div>
          <div>
            <label for="provider">Provider</label>
            <select id="provider" name="provider">
              <option value="private-codex">private-codex</option>
            </select>
          </div>
        </div>

        <label class="toggle" style="margin-top: 16px;">
          <input id="dryRun" name="dryRun" type="checkbox" />
          Dry run
        </label>

        <button id="submit" type="submit" style="margin-top: 18px; width: 100%;">Generate image</button>
      </form>

      <p class="hint">Live generation uses the local Codex ChatGPT session from <code>~/.codex/auth.json</code>. Dry run only validates request construction.</p>
    </aside>

    <section>
      <div class="result-head">
        <div>
          <h2>Result</h2>
          <p class="hint" id="message">No request has been sent yet.</p>
        </div>
        <div class="meta" id="meta"></div>
      </div>

      <div class="preview" id="preview">
        <div class="empty">Generated images appear here.</div>
      </div>

      <pre id="json">{}</pre>
    </section>
  </main>

  <script>
    const form = document.querySelector("#form");
    const statusEl = document.querySelector("#status");
    const messageEl = document.querySelector("#message");
    const metaEl = document.querySelector("#meta");
    const previewEl = document.querySelector("#preview");
    const jsonEl = document.querySelector("#json");
    const submitEl = document.querySelector("#submit");

    function setBusy(isBusy) {
      submitEl.disabled = isBusy;
      submitEl.textContent = isBusy ? "Generating..." : "Generate image";
      statusEl.textContent = isBusy ? "running" : "ready";
    }

    function showJson(payload) {
      jsonEl.textContent = JSON.stringify(payload, null, 2);
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      setBusy(true);
      messageEl.textContent = "Sending request...";
      messageEl.className = "hint";
      metaEl.textContent = "";

      const payload = {
        prompt: document.querySelector("#prompt").value,
        model: document.querySelector("#model").value || null,
        provider: document.querySelector("#provider").value,
        dry_run: document.querySelector("#dryRun").checked
      };

      try {
        const response = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        showJson(data);

        if (!response.ok) {
          throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail));
        }

        statusEl.textContent = data.mode;
        messageEl.textContent = data.image_url ? "Image generated." : "Dry run completed.";
        metaEl.textContent = [data.response_id, data.revised_prompt ? "revised prompt" : ""].filter(Boolean).join(" / ");

        if (data.image_url) {
          previewEl.innerHTML = "";
          const image = new Image();
          image.alt = "Generated image";
          image.src = `${data.image_url}?t=${Date.now()}`;
          previewEl.appendChild(image);
        } else {
          previewEl.innerHTML = "<div class=\\"empty\\">Dry run returned no image file.</div>";
        }
      } catch (error) {
        statusEl.textContent = "error";
        messageEl.textContent = error.message;
        messageEl.className = "hint error";
      } finally {
        setBusy(false);
      }
    });
  </script>
</body>
</html>
"""
