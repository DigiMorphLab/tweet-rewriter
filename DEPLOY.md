# How to Deploy to Streamlit Community Cloud

Since this project uses **Streamlit**, the best way to deploy it for free is using **Streamlit Community Cloud**. 
(Vercel is not recommended for Streamlit apps because they require a persistent server connection which Vercel's serverless architecture does not support).

## Prerequisites

1. A [GitHub](https://github.com/) account.
2. A [Streamlit Community Cloud](https://streamlit.io/cloud) account (you can sign in with GitHub).

## Steps

### 1. Push Code to GitHub

1. Create a new repository on GitHub.
2. Push this project code to the repository.
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <YOUR_REPO_URL>
   git push -u origin main
   ```
   *(Note: `src/config.json` is ignored by `.gitignore` to protect your API keys. You will set them up securely in step 3).*

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Click **"New app"**.
3. Select your repository, branch (`main`), and the main file path: `src/app.py`.
4. Click **"Deploy!"**.

### 3. Configure Secrets (API Keys)

Once deployed, the app will likely show an error or empty fields because it doesn't have your API keys.

1. On your app dashboard in Streamlit Cloud, click the **Settings** (three dots) -> **Settings**.
2. Go to the **Secrets** tab.
3. Paste the content of your `src/config.json` into the editor, but in TOML format. 

**Example TOML for Secrets:**

```toml
[step1_extraction]
provider = "openrouter"
model = "deepseek/deepseek-chat-v3.1"
api_key = "sk-or-..."
base_url = "https://openrouter.ai/api/v1"

[step3_generation.primary]
provider = "openrouter"
model = "nousresearch/hermes-3-llama-3.1-405b:free"
api_key = "sk-or-..."
base_url = "https://openrouter.ai/api/v1"

[step3_generation.secondary]
provider = "openrouter"
model = "deepseek/deepseek-chat-v3-0324"
api_key = "sk-or-..."
base_url = "https://openrouter.ai/api/v1"

[step4_refinement]
threshold_score = 85

[step4_refinement.primary]
provider = "openrouter"
model = "x-ai/grok-code-fast-1"
api_key = "sk-or-..."
base_url = "https://openrouter.ai/api/v1"

[step4_refinement.secondary]
provider = "openrouter"
model = "openai/gpt-oss-120b"
api_key = "sk-or-..."
base_url = "https://openrouter.ai/api/v1"
```

4. Click **Save**. The app will restart automatically and use these keys.

## Why not Vercel?
Streamlit requires a persistent WebSocket connection to maintain the app state. Vercel uses "Serverless Functions" which are ephemeral (they shut down after a few seconds) and do not support persistent connections, causing Streamlit apps to break immediately.
