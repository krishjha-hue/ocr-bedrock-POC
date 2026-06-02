# Setup Guide

Step-by-step instructions to run the OCR Model Playground locally against your own AWS account.

Total time: about 15 minutes if you already have the AWS CLI, longer on first-time setup.

---

## 1. Install prerequisites

### Python 3.10 or newer

Check your version:

```bash
python3 --version
```

If you don't have it:

- **macOS**: `brew install python@3.12` (install Homebrew from https://brew.sh if needed)
- **Ubuntu / Debian**: `sudo apt update && sudo apt install python3 python3-venv python3-pip`
- **Windows**: download from https://www.python.org/downloads/ and check "Add Python to PATH"

### AWS CLI (recommended)

Used to configure credentials and verify Bedrock access.

- **macOS**: `brew install awscli`
- **Linux**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- **Windows**: https://awscli.amazonaws.com/AWSCLIV2.msi

Verify:

```bash
aws --version
```

---

## 2. Enable Bedrock model access

Model access is per-account, per-region and must be requested through the Bedrock console. This is a one-time step.

1. Sign in to the AWS Console
2. Switch region to **Asia Pacific (Mumbai) — `ap-south-1`** (top-right region picker)
3. Open the **Amazon Bedrock** service
4. Left sidebar → **Model access**
5. Click **Modify model access** (top-right)
6. Tick the checkboxes for these models (recommended default set):
   - **Claude Sonnet 4.5** (Anthropic)
   - **Nova Pro** (Amazon)
   - **Nova 2 Lite** (Amazon)
   - **Mistral Large 3** (Mistral)

   Optionally enable additional models to try (shown under "Additional models" in the UI):
   - Claude Opus 4.5, Claude Opus 4.7, Claude Sonnet 4.6, Claude Haiku 4.5
   - Qwen3-VL 235B
   - Moonshot Kimi K2.5
   - Google Gemma 3 27B
7. Click **Next**, review, then **Submit**

Most models are granted within a minute. Anthropic models may occasionally require a short use-case form; fill it and resubmit.

> **Important**: Model access is regional. If you want to run in another region, repeat this in that region.

---

## 3. Configure AWS credentials

The app uses the standard AWS SDK credential chain, so any of these work. Pick whichever matches how you normally authenticate.

### Option A: Long-term access keys (simplest for testing)

1. In the AWS Console, go to **IAM** → **Users** → your user → **Security credentials**
2. Create an access key, choose "Command Line Interface (CLI)", and save the key and secret
3. In your terminal:

```bash
aws configure
# AWS Access Key ID     : <paste access key>
# AWS Secret Access Key : <paste secret>
# Default region name   : ap-south-1
# Default output format : json
```

### Option B: IAM Identity Center / SSO (recommended for orgs)

```bash
aws configure sso
# follow the prompts to authenticate in your browser

# Once set up, log in whenever your session expires:
aws sso login --profile <your-profile-name>
export AWS_PROFILE=<your-profile-name>
```

### Option C: Environment variables

```bash
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_SESSION_TOKEN=<token>          # only if using temporary credentials
export AWS_REGION=ap-south-1
```

### Required IAM permissions

The credentials need to allow these Bedrock actions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:Converse",
        "bedrock:ListFoundationModels",
        "bedrock:ListInferenceProfiles"
      ],
      "Resource": "*"
    }
  ]
}
```

The AWS managed policy **AmazonBedrockFullAccess** covers this if you prefer not to author a custom policy.

---

## 4. Verify credentials and Bedrock access

Before running the app, sanity-check everything:

```bash
aws sts get-caller-identity
# Should print your account ID, user/role ARN, and user ID.
```

```bash
aws bedrock list-foundation-models --region ap-south-1 --query 'modelSummaries[?contains(inputModalities, `IMAGE`)].modelId' --output text
# Should print a list of image-capable model IDs available to you.
```

If these two commands succeed you're ready to run the app.

---

## 5. Install and run the app

```bash
# From the v2-poc directory:

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\Activate.ps1          # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Set region if not already in ~/.aws/config.
# BEDROCK_REGION overrides AWS_REGION just for this app, which is safer if you
# normally work in another region for AWS work.
export BEDROCK_REGION=ap-south-1

# Start the server
uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

You should see the UI with the 4 models listed on the left. Claude Sonnet 4.5 is pre-selected.

---

## 6. Try a first run

1. Click **Choose file** and upload a scanned document or license (PNG / JPEG, under 4 MB)
2. Confirm **Claude Sonnet 4.5** is checked. Add any other models if desired
3. (Optional) Edit the system or user prompt in the textareas
4. Click **Run**

Within a few seconds you'll see one card per selected model, with:

- The parsed JSON (auto-extracted from the model output)
- The raw output (click the "Raw output" tab)
- Latency in milliseconds
- Input and output token counts

If 2 or more models returned valid JSON, a **Field agreement** heatmap appears above the cards. Green cells are fields where all models returned the same value; yellow cells are disagreements worth reviewing.

---

## Troubleshooting

### `NoCredentialsError` or `Unable to locate credentials`

Your terminal session doesn't see your AWS credentials.
- Confirm `aws sts get-caller-identity` works in the same terminal you run uvicorn in
- If using SSO, run `aws sso login` and `export AWS_PROFILE=<name>`

### `AccessDeniedException` on one model

That model is not enabled for your account in this region. Go back to **Bedrock → Model access** and enable it, then refresh the browser.

### `ValidationException: The provided model identifier is invalid`

This is Bedrock's (confusing) way of saying **you haven't been granted model access** for this model in this region. Go to **Bedrock → Model access** in the correct region, enable the model, and retry. Despite the word "invalid", the model ID is fine.

### `ValidationException: temperature is deprecated for this model`

Some newer Anthropic reasoning models (Opus 4.7, Opus 4.6, Sonnet 4.6) reject the `temperature` parameter. The app already handles this automatically for known models. If you hit this with a model you added manually in `models.py`, add its ID substring to `_NO_TEMPERATURE_SUBSTRINGS` at the top of `app.py`.

### `ResourceNotFoundException: Model marked as Legacy`

You haven't used this model in 30+ days and AWS has disabled it for your account. Swap it in `models.py` for a current model (the defaults are all current).

### `ThrottlingException` or `ServiceQuotaExceededException`

Bedrock has per-account, per-region rate limits. Run fewer models in parallel, or request a quota increase via AWS Support.

### The UI says "region: us-east-1" (or anything other than Mumbai)

The backend resolves the region in this priority order:

1. `BEDROCK_REGION` environment variable (app-specific override)
2. `AWS_REGION` environment variable (global AWS default)
3. Fallback to `ap-south-1`

If your shell has `AWS_REGION=us-east-1` set (common if you usually work in Virginia), it overrides the code default. Fix with either:

```bash
# Option A: set a Bedrock-specific region just for this app
export BEDROCK_REGION=ap-south-1

# Option B: change your shell's AWS_REGION (affects all AWS commands in this shell)
export AWS_REGION=ap-south-1

# Either way, restart uvicorn in the SAME terminal so it picks up the change.
```

Verify in the browser: the region badge in the top-right should read `region: ap-south-1` in the default (white/grey) style. If it's yellow, the backend is on a different region than the app expects.

### The server starts but the browser can't connect

- Make sure nothing else is using port 8000 (`lsof -i :8000` on macOS/Linux)
- Try `http://127.0.0.1:8000` instead of `localhost`
- If you're on a restrictive corporate network, some firewalls block `127.0.0.1` binds; try `uvicorn app:app --host 0.0.0.0 --port 8000`

### Image upload fails with 413

Your image is over 4 MB. Downscale it:

```bash
# macOS (sips)
sips -Z 2000 input.png --out output.png

# Cross-platform (ImageMagick)
magick input.png -resize 2000x2000\> output.png
```

### Models return wrong fields or hallucinate

- Try different models using the checkboxes. Claude Sonnet 4.5 is usually the strongest starting point
- Preprocess the image first: deskew, increase contrast, upscale low-res scans
- Shorten or clarify the prompt if a specific field is being confused
- Check the **Raw output** tab to see what the model actually returned

---

## Stopping and cleaning up

- Stop the server with `Ctrl+C` in the terminal
- Deactivate the virtual environment: `deactivate`
- To remove everything: `rm -rf .venv`

The app makes no AWS changes beyond invoking Bedrock models. There are no S3 uploads, no persistent state, and no logs sent anywhere. All image bytes stay in memory for the duration of the request.

---

## Pricing note

Bedrock bills per input + output token. For a single license-sized image (~1500 input tokens, ~150 output tokens):

- Claude Sonnet 4.5: roughly US$0.005 per run
- Nova Pro: roughly US$0.001 per run
- Nova 2 Lite: roughly US$0.0003 per run
- Mistral Large 3: roughly US$0.003 per run

Running all four on the same image costs under 1 US cent. Exact prices are published at https://aws.amazon.com/bedrock/pricing/ and vary by region.
