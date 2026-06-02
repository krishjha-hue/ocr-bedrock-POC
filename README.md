# OCR Model Playground

A lightweight web app to compare Amazon Bedrock vision models side by side on the same image and prompt. Built for evaluating OCR accuracy on mixed-language documents (English, Hindi / Devanagari), printed and handwritten.

## What it does

- Upload an image (license, ID card, scanned document, handwritten form)
- Pick one or more Bedrock models via checkboxes
- Edit the system and user prompt inline
- Click Run: all selected models are called in parallel
- See results side by side: parsed JSON, raw text, latency, token usage
- Automatic field-level agreement heatmap when 2 or more models return JSON

## What you need

- Python 3.10 or newer
- An AWS account with Amazon Bedrock access
- Model access enabled in the Bedrock console for the models you want to test (see [SETUP.md](SETUP.md))
- A terminal (macOS Terminal, Linux shell, Windows PowerShell or WSL)

## Quick start

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\activate              # Windows PowerShell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure AWS credentials (see SETUP.md for details)
aws configure
export BEDROCK_REGION=ap-south-1     # Mumbai region (app-specific override)

# 4. Start the app
uvicorn app:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

Full setup walk-through, including AWS credentials and Bedrock model access, is in [SETUP.md](SETUP.md).

## Sample images

Five sample documents are included in `samples/` to try immediately after setup:

- `license_01.png`, `license_02.png` — agricultural input licenses (the main demo target)
- `image_01.png`, `image_05.png`, `image_06.png` — ID document scans

Upload any of these in step 1 of the UI to see the models side by side.

## Files

| File                  | Purpose                                               |
| --------------------- | ----------------------------------------------------- |
| `app.py`            | FastAPI server; calls Bedrock via the Converse API    |
| `models.py`         | Registry of Bedrock models shown in the UI            |
| `prompts.py`        | Default system + user prompts (edit to your use case) |
| `static/index.html` | Single-page UI                                        |
| `requirements.txt`  | Python dependencies                                   |
| `SETUP.md`          | Step-by-step setup including AWS credentials          |
| `MODELS.md`         | Why these four models and how to swap them            |

## Default models

Four models are pre-configured under "Recommended for Hindi OCR" for a spread across providers in Mumbai (`ap-south-1`):

1. **Claude Sonnet 4.5** — recommended default, strongest on Devanagari and handwriting
2. **Amazon Nova Pro** — AWS-native multimodal, decent on printed Hindi
3. **Amazon Nova 2 Lite** — next-gen Nova Lite, newer architecture
4. **Mistral Large 3 (675B)** — Mistral's largest vision model

An additional 7 models (Claude Opus 4.5 / 4.7, Sonnet 4.6, Haiku 4.5, Qwen3-VL 235B, Kimi K2.5, Gemma 3 27B) are available under an **Additional models** section in the UI for deeper benchmarking.

See [MODELS.md](MODELS.md) to swap models or explore alternatives.

## Region

Defaults to `ap-south-1` (Mumbai). The app resolves the region in this order:

1. `BEDROCK_REGION` (app-specific override; recommended)
2. `AWS_REGION` (global AWS default)
3. Fallback to `ap-south-1`

Override with:

```bash
export BEDROCK_REGION=us-east-1      # for example
```

If you change regions, check [MODELS.md](MODELS.md) — some inference profile IDs are region-specific.

## Known limits

- Inline image upload is capped at 4 MB (Bedrock's hard limit on base64-encoded inline bytes is ~3.75 MB)
- Supported formats: PNG, JPEG, WEBP, GIF
- One image per run (batch mode not implemented)
- Temperature is fixed at 0 for reproducibility
- Models not enabled in your account will return an error card; other models in the same run are unaffected

## Run the Server

```
BEDROCK_REGION=ap-south-1 .venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
```


## License

Internal proof of concept. Not for redistribution without approval.
