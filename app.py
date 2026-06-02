"""FastAPI server for the OCR model comparison playground.

Endpoints:
    GET  /                  -> serves the SPA
    GET  /api/models        -> list of available Bedrock models
    GET  /api/prompts       -> default system + user prompts
    POST /api/run           -> run one image against N models in parallel

The Converse API is used for all providers so we don't need per-provider
request shaping. Images are sent inline (base64) which works for files under
~3.75 MB; for bigger files we'd switch to S3 references.
"""
from __future__ import annotations
from dotenv import load_dotenv
from pathlib import Path
# Load environment variables from .env
load_dotenv(Path(__file__).resolve().parent / ".env")
import asyncio
import base64
import json
import os
import re
import time

from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from models import MODELS, get_model
from prompts import DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

AWS_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION") or "ap-south-1"
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB cap for inline bytes
SUPPORTED_FORMATS = {"png", "jpeg", "jpg", "gif", "webp"}

BASE_DIR = Path(__file__).parent

app = FastAPI(title="OCR Model Playground")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

_bedrock_config = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    read_timeout=120,
    connect_timeout=10,
)
_bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION, config=_bedrock_config)


# Some newer Anthropic reasoning/extended-thinking models reject `temperature`
# (and `top_p`). For these we omit them entirely. Everything else gets
# temperature=0 for determinism.
_NO_TEMPERATURE_SUBSTRINGS = (
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
)


def _inference_config_for(model_id: str) -> dict:
    cfg: dict = {"maxTokens": 2048}
    if not any(s in model_id for s in _NO_TEMPERATURE_SUBSTRINGS):
        # Note: Anthropic models on Bedrock reject temperature + topP together,
        # so we only send temperature.
        cfg["temperature"] = 0.0
    return cfg


# ---------- helpers ---------------------------------------------------------


def _image_format(filename: str, content_type: str | None) -> str:
    """Bedrock Converse expects format names like 'png' or 'jpeg'."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "jpg":
        ext = "jpeg"
    if ext in SUPPORTED_FORMATS:
        return ext
    if content_type:
        mime = content_type.split("/")[-1].lower()
        if mime == "jpg":
            mime = "jpeg"
        if mime in SUPPORTED_FORMATS:
            return mime
    raise HTTPException(400, f"Unsupported image format: {filename} ({content_type})")


def _extract_json(text: str) -> dict | list | None:
    """Best-effort JSON extraction from model output. Some models wrap in ``` or
    add prose despite instructions. Strip fences, then find the first {...} or [...] block.
    """
    if not text:
        return None
    cleaned = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


async def _run_one(
    model_id: str,
    image_bytes: bytes,
    image_fmt: str,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    """Call one model via Converse. Runs in a thread since boto3 is sync."""

    def _invoke() -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            resp = _bedrock.converse(
                modelId=model_id,
                system=[{"text": system_prompt}] if system_prompt else [],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"image": {"format": image_fmt, "source": {"bytes": image_bytes}}},
                            {"text": user_prompt},
                        ],
                    }
                ],
                # Note: Anthropic models on Bedrock reject temperature + topP together.
                # Sending only temperature=0 is enough for determinism.
                # Newer reasoning models reject temperature entirely; see
                # _inference_config_for().
                inferenceConfig=_inference_config_for(model_id),
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            text_parts = [
                c.get("text", "")
                for c in resp.get("output", {}).get("message", {}).get("content", [])
                if "text" in c
            ]
            raw_text = "\n".join(text_parts).strip()
            usage = resp.get("usage", {})
            return {
                "model_id": model_id,
                "ok": True,
                "latency_ms": elapsed_ms,
                "input_tokens": usage.get("inputTokens"),
                "output_tokens": usage.get("outputTokens"),
                "raw_text": raw_text,
                "parsed_json": _extract_json(raw_text),
                "error": None,
            }
        except ClientError as e:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "model_id": model_id,
                "ok": False,
                "latency_ms": elapsed_ms,
                "input_tokens": None,
                "output_tokens": None,
                "raw_text": "",
                "parsed_json": None,
                "error": f"{e.response.get('Error', {}).get('Code', 'ClientError')}: {e.response.get('Error', {}).get('Message', str(e))}",
            }
        except Exception as e:  # noqa: BLE001
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return {
                "model_id": model_id,
                "ok": False,
                "latency_ms": elapsed_ms,
                "input_tokens": None,
                "output_tokens": None,
                "raw_text": "",
                "parsed_json": None,
                "error": f"{type(e).__name__}: {e}",
            }

    return await asyncio.to_thread(_invoke)


# ---------- routes ----------------------------------------------------------


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/models")
async def list_models() -> dict[str, Any]:
    # Also report the effective boto3 region so the UI can surface any mismatch.
    try:
        effective_region = _bedrock.meta.region_name
    except Exception:  # noqa: BLE001
        effective_region = AWS_REGION
    return {
        "region": AWS_REGION,
        "effective_region": effective_region,
        "models": [
            {"id": m.id, "label": m.label, "provider": m.provider, "group": m.group, "notes": m.notes}
            for m in MODELS
        ],
    }


@app.get("/api/whoami")
async def whoami() -> dict[str, Any]:
    """Diagnostic endpoint: surfaces the effective AWS identity and region so
    customers can verify the app is talking to the intended account + region."""
    try:
        sts = boto3.client("sts", region_name=AWS_REGION, config=_bedrock_config)
        ident = sts.get_caller_identity()
        return {
            "configured_region": AWS_REGION,
            "boto3_region": _bedrock.meta.region_name,
            "account_id": ident.get("Account"),
            "arn": ident.get("Arn"),
            "user_id": ident.get("UserId"),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "configured_region": AWS_REGION,
            "boto3_region": _bedrock.meta.region_name,
            "error": f"{type(e).__name__}: {e}",
        }


@app.get("/api/prompts")
async def default_prompts() -> dict[str, str]:
    return {"system": DEFAULT_SYSTEM_PROMPT, "user": DEFAULT_USER_PROMPT}


@app.post("/api/run")
async def run(
    image: UploadFile = File(...),
    model_ids: str = Form(...),   # comma-separated
    system_prompt: str = Form(""),
    user_prompt: str = Form(...),
) -> JSONResponse:
    selected_ids = [m.strip() for m in model_ids.split(",") if m.strip()]
    if not selected_ids:
        raise HTTPException(400, "Pick at least one model.")
    for mid in selected_ids:
        if get_model(mid) is None:
            raise HTTPException(400, f"Unknown model id: {mid}")

    data = await image.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            413,
            f"Image is {len(data) // 1024} KB; max is {MAX_IMAGE_BYTES // 1024} KB. "
            "Downscale it or convert to JPEG before uploading.",
        )
    fmt = _image_format(image.filename or "", image.content_type)

    results = await asyncio.gather(
        *(_run_one(mid, data, fmt, system_prompt, user_prompt) for mid in selected_ids)
    )

    return JSONResponse(
        {
            "image_bytes_b64": base64.b64encode(data).decode("ascii"),
            "image_format": fmt,
            "filename": image.filename,
            "results": results,
        }
    )
