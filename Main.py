from fastapi import FastAPI, Request
import requests, subprocess, os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

GITHUB_TOKEN = os.getenv("github_token")
OPENAI_API_KEY = os.getenv("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")
REPO_OWNER = os.getenv("MaverixSri10")
REPO_NAME = os.getenv("Internal_PR_Review_Agent")

# ---------- Step 1: Fetch PR data ----------
def fetch_pr_data(pr_number):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{1}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    res = requests.get(url, headers=headers)
    return res.json() if res.status_code == 200 else None

# ---------- Step 2: Fetch PR diff ----------
def fetch_pr_diff(diff_url):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    res = requests.get(diff_url, headers=headers)
    return res.text if res.status_code == 200 else None

# ---------- Step 3: Static analysis ----------
def run_semgrep(path="."):
    result = subprocess.run(["semgrep", "--config=auto", path],
                            capture_output=True, text=True)
    return result.stdout.strip()

def run_pip_audit():
    result = subprocess.run(["pip-audit", "--json"],
                            capture_output=True, text=True)
    return result.stdout.strip()

# ---------- Step 4: Combine everything ----------
def create_review_prompt(pr_data, diff_text, semgrep_report, pip_audit_report):
    title = pr_data.get("title", "")
    author = pr_data.get("user", {}).get("login", "")
    body = pr_data.get("body", "")
    pr_number = pr_data.get("number", "")
    return f"""
GitHub Pull Request Review
--------------------------
PR #{pr_number} by {author}: {title}

Description:
{body}

Code Diff:
{diff_text[:1200]}

Semgrep Results:
{semgrep_report[:1200]}

pip-audit Results:
{pip_audit_report[:1200]}

Please generate a concise technical code review covering:
- Bugs or security flaws
- Code smells or bad practices
- Suggestions for improvement
- Any dependency risks
"""

# ---------- Step 5: Get AI review ----------
def generate_ai_review(prompt):
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a strict senior code reviewer."},
                  {"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600
    )
    return response["choices"][0]["message"]["content"].strip()

# ---------- Step 6: Post comment on PR ----------
def post_github_comment(pr_number, comment):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment}
    requests.post(url, headers=headers, json=data)

# ---------- Step 7: Webhook endpoint ----------

@app.get("/")
async def root():
    return {"message": "✅ FastAPI is running on localhost!"}

async def github_webhook(request: Request):
    payload = await request.json()
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")

    # Run only for opened or updated PRs
    if action in ["opened", "synchronize"] and pr_number:
        print(f"🔔 PR Triggered: #{pr_number}")

        pr_data = fetch_pr_data(pr_number)
        diff_text = fetch_pr_diff(pr.get("diff_url"))
        semgrep_report = run_semgrep()
        pip_audit_report = run_pip_audit()

        prompt = create_review_prompt(pr_data, diff_text, semgrep_report, pip_audit_report)
        review = generate_ai_review(prompt)

        post_github_comment(pr_number, review)
        print(f"✅ Review comment posted on PR #{pr_number}")

    return {"status": "done"}

