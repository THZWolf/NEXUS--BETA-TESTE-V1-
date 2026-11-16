"""Local avatar interface; no cloud model or remote telemetry is used."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

PERSONALITY_FILE = Path(
    os.environ.get(
        "NEXUS_PERSONALITY_FILE",
        "/etc/nexus-os/personality.json",
    )
)
LOCAL_SERVER_URL = os.environ.get("NEXUS_LOCAL_SERVER_URL", "http://127.0.0.1:8765")
THEMES = {
    "cyan": ("#55eeff", "#21d8ff88"),
    "violet": ("#c7a6ff", "#a976ff88"),
    "amber": ("#ffd166", "#ffb52e88"),
}

app = FastAPI(title="NEXU-OS Avatar", version="1.0.0")


class Message(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


def load_personality() -> dict[str, object]:
    try:
        profile = json.loads(PERSONALITY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot load avatar personality: {exc}") from exc
    if (
        not isinstance(profile, dict)
        or not isinstance(profile.get("name"), str)
        or not isinstance(profile.get("theme"), str)
        or profile.get("theme") not in THEMES
    ):
        raise RuntimeError("Avatar personality must contain a name and a supported theme.")
    return profile


@app.get("/", response_class=HTMLResponse)
def interface() -> str:
    profile = load_personality()
    name = str(profile["name"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    accent, glow = THEMES[str(profile["theme"])]
    return f"""<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{name} · NEXU-OS</title>
<style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#07121d;color:#d9f6ff;
font:16px system-ui,sans-serif}}main{{text-align:center;max-width:34rem;padding:2rem}}
.orb{{width:8rem;height:8rem;margin:0 auto 1.5rem;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,{accent} 18%,#1179a3 52%,#07121d 75%);
box-shadow:0 0 2rem {glow};animation:float 4s ease-in-out infinite}}
@keyframes float{{50%{{transform:translateY(-8px)}}}}@media(prefers-reduced-motion:reduce){{.orb{{animation:none}}}}
p{{color:#a9c8d5}}button{{background:#0e6079;color:white;border:0;border-radius:.5rem;padding:.7rem 1rem}}
input{{box-sizing:border-box;width:100%;margin:.5rem 0;padding:.7rem;border-radius:.5rem;border:1px solid #34778a;background:#0b1d2b;color:#fff}}
</style><main><div class="orb" aria-hidden="true"></div><h1>{name}</h1>
<p>Interface local do avatar. Mensagens são registradas neste dispositivo; não há modelo de linguagem incluído.</p>
<form id="message-form"><label for="message">Mensagem para registrar localmente</label>
<input id="message" maxlength="2000" required autocomplete="off">
<button type="submit">Enviar ao barramento local</button></form><p id="status" role="status" aria-live="polite"></p>
<script>
document.getElementById('message-form').addEventListener('submit', async (event) => {{
  event.preventDefault();
  const status = document.getElementById('status');
  status.textContent = 'Enviando…';
  try {{
    const response = await fetch('/api/message', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{text: document.getElementById('message').value}})
    }});
    if (!response.ok) throw new Error('Servidor local indisponível.');
    status.textContent = 'Mensagem armazenada no servidor local.';
  }} catch (error) {{
    status.textContent = error.message;
  }}
}});
</script>
</main></html>"""


@app.get("/health")
def health() -> dict[str, object]:
    try:
        profile = load_personality()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok", "avatar": profile["name"], "mode": "local"}


@app.post("/api/message", status_code=202)
def submit_message(message: Message) -> dict[str, object]:
    payload = json.dumps(
        {"event_type": "avatar.message", "payload": {"text": message.text}},
        ensure_ascii=True,
    ).encode("utf-8")
    request = Request(
        f"{LOCAL_SERVER_URL}/api/events",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="Local event server unavailable.") from exc
    return {"accepted": True, "event_id": result["id"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ai.avatar_core:app", host="127.0.0.1", port=8766, access_log=False)
