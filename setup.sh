#!/bin/bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
export BEDROCK_REGION=ap-south-1
uvicorn app:app --reload --port 8000
