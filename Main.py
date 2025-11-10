from fastapi import FastAPI, Request
import requests, subprocess, os, json
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- GitHub credentials ---
GITHUB_TOKEN = os.getenv("GIT_HUB")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# =============================
# 1️⃣ Webhook Trigger - PR opened
# =============================
@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    action = payload.get("action")
    
    # Trigger only when PR is opened or synchronized
    if action not in ["opened", "synchronize"]:
        return {"message": "Ignored action."}

    pr = payload["pull_request"]
    repo_full_name = payload["repository"]["full_name"]
    pr_number = pr["number"]
    diff_url = pr["diff_url"]

    print(f"🚀 PR Triggered for {repo_full_name} #{pr_number}")

    # Step 2️⃣ Fetch PR diff
    diff_text = fetch_pr_diff(diff_url)
    
    # Step 3️⃣ Run Static Analysis
    semgrep_results = run_semgrep()
    pip_audit_results = run_pip_audit()

    # Step 4️⃣ Combine results into review prompt
    review_prompt = create_review_prompt(diff_text, semgrep_results, pip_audit_results)

    # Step 5️⃣ Send to LLM (Copilot/AI)
    ai_review = generate_ai_review(review_prompt)

    # Step 6️⃣ Post Comments to GitHub PR
    post_review_comment(repo_full_name, pr_number, ai_review)

    return {"message": "AI PR Review Completed ✅"}


# =============================
# 2️⃣ Fetch PR diff
# =============================
def fetch_pr_diff(diff_url):
    response = requests.get(diff_url, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    else:
        return f"Error fetching diff: {response.status_code}"


# =============================
# 3️⃣ Static Analysis - Semgrep
# =============================
def run_semgrep():
    try:
        result = subprocess.run(
            ["semgrep", "--config", "p/ci", "--json"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


# =============================
# 3️⃣ Static Analysis - pip-audit
# =============================
def run_pip_audit():
    try:
        result = subprocess.run(
            ["pip-audit", "-f", "json"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


# =============================
# 4️⃣ Combine Results
# =============================
def create_review_prompt(diff, semgrep_results, pip_audit_results):
    prompt = f"""
    You are an AI code reviewer.

    Here is the PR diff:
    {diff}

    Here are static analysis findings from Semgrep:
    {semgrep_results}

    Here are dependency issues from pip-audit:
    {pip_audit_results}

    Generate a concise, professional PR review with:
    - High-level feedback
    - Inline comment suggestions
    - Security and style issues
    """
    return prompt


# =============================
# 5️⃣ LLM Integration (Copilot / OpenAI)
# =============================
def generate_ai_review(prompt):
    # Use OpenAI or GitHub Copilot Agent SDK
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message["content"]


# =============================
# 6️⃣ Post Comments to GitHub
# =============================
def post_review_comment(repo_full_name, pr_number, review_body):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    data = {"body": review_body}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print("✅ Review comment posted successfully!")
    else:
        print(f"❌ Failed to post comment: {response.text}")
