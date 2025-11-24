from fastapi import FastAPI, Request
import requests, subprocess, os, json
from fastapi.responses import FileResponse
from dotenv import load_dotenv



load_dotenv()

app = FastAPI()


# --- GitHub credentials ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}


# 1 Webhook Trigger - PR opened

@app.get("/webhook")
async def webhook_verify():
    return {"status": "webhook GET OK"}


@app.post("/webhook")
async def webhook(request: Request):
    raw_body = await request.body()
    print("\n RAW PAYLOAD:", raw_body.decode())

    try:
        payload = await request.json()
    except:
        print(" Could not parse JSON")
        return {"status": "invalid json"}

    print(" Parsed JSON:", payload)

    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        print(f" Ignored action: {action}")
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo_full_name = payload["repository"]["full_name"]
    pr_number = pr["number"]
    diff_url = pr["diff_url"]

    print(f"\n PR Triggered for {repo_full_name} #{pr_number}")
    print(" Diff URL:", diff_url)

    # Step 2: Fetch PR diff
    diff_text = fetch_pr_diff(diff_url)
    print(" DIFF RECEIVED")

    # Step 3: Static analysis
    semgrep_results = run_semgrep()
    pip_audit_results = run_pip_audit()
    print(" Static analysis completed")

    # Step 4: Build prompt
    review_prompt = create_review_prompt(diff_text, semgrep_results, pip_audit_results)

    # Step 5: AI Review
    ai_review = generate_ai_review(review_prompt)
    print(" AI Review Generated")

    # Step 6: Post to GitHub PR
    post_review_comment(repo_full_name, pr_number, ai_review)
    print(" Review Posted to GitHub")

    return {"status": "review completed"}



# 2️ Fetch PR diff
def fetch_pr_diff(diff_url):
    response = requests.get(diff_url, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    else:
        return f"Error fetching diff: {response.status_code}"


# 3 Static Analysis - Semgrep
def run_semgrep():
    try:
        result = subprocess.run(
            ["semgrep", "--config", "p/ci", "--json"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


# 3️.1 Static Analysis - pip-audit
def run_pip_audit():
    try:
        result = subprocess.run(
            ["pip-audit", "-f", "json"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


# 4️ Combine Results
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


# 5️ LLM Integration (Openrouter)

def generate_ai_review(prompt: str):
    api_key = os.getenv("OPEN_ROUTER_KEY")
    if not api_key:
        return "ERROR: Missing OPENROUTER_API_KEY in .env"

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "PR Review Agent"
    }

    payload = {
        "model": "mistralai/mistral-small-3.1-24b-instruct:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    # If LLM fails, return error string instead of crashing FastAPI
    if response.status_code != 200:
        return f"LLM ERROR: {response.status_code} - {response.text}"

    data = response.json()

    if "choices" not in data:
        return f"INVALID LLM RESPONSE: {data}"

    return data["choices"][0]["message"]["content"]



# 6️ Post Comments to GitHub
def post_review_comment(repo_full_name, pr_number, review_body):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    data = {"body": review_body}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(" Review comment posted successfully!")
    else:
        print(f" Failed to post comment: {response.text}")



