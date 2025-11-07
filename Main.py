from fastapi import FastAPI, Request
import requests, os, subprocess, json, tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

# ------------------------
# STEP 1: PR Trigger
# ------------------------
@app.post("/pr_trigger")
async def pr_trigger(request: Request):
    payload = await request.json()
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    if action in ["opened", "synchronize", "reopened"]:
        pr_number = pr["number"]
        repo_full_name = repo["full_name"]
        print(f"PR Triggered: {repo_full_name} #{pr_number}")

        # STEP 2: Fetch PR data
        diff_data = fetch_pr_diff(repo_full_name, pr_number)

        # STEP 3: Run Static Analysis
        analysis_results = run_static_analysis(repo_full_name)

        # STEP 4: Generate review prompt
        prompt = generate_review_prompt(diff_data, analysis_results)

        # STEP 5: Invoke AI Reviewer (Mock Copilot SDK)
        ai_review = invoke_copilot_agent(prompt)

        # STEP 6: Post review comments to PR
        post_review_comment(repo_full_name, pr_number, ai_review)

        return {"status": "PR reviewed successfully"}
    else:
        return {"message": f"Ignored PR action: {action}"}


# ------------------------
# STEP 2: Fetch PR Data
# ------------------------
def fetch_pr_diff(repo_full_name: str, pr_number: int):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }
    url = f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    return response.text if response.status_code == 200 else ""


# ------------------------
# STEP 3: Static Analysis
# ------------------------
def run_static_analysis(repo_full_name: str):
    """
    Run Semgrep and pip-audit (Python example)
    """
    results = {}

    try:
        # 1️⃣ Semgrep
        semgrep_cmd = ["semgrep", "--config", "p/ci", "--json"]
        semgrep_output = subprocess.run(
            semgrep_cmd, capture_output=True, text=True, check=False
        )
        results["semgrep"] = json.loads(semgrep_output.stdout or "{}")
    except Exception as e:
        results["semgrep_error"] = str(e)

    try:
        # 2️⃣ pip-audit
        pip_audit_cmd = ["pip-audit", "-f", "json"]
        pip_output = subprocess.run(
            pip_audit_cmd, capture_output=True, text=True, check=False
        )
        results["pip_audit"] = json.loads(pip_output.stdout or "[]")
    except Exception as e:
        results["pip_audit_error"] = str(e)

    return results


# ------------------------
# STEP 4: Generate Prompt
# ------------------------
def generate_review_prompt(diff_data, analysis_results):
    """
    Combine diff + static analysis results into one structured prompt
    """
    semgrep_findings = analysis_results.get("semgrep", {}).get("results", [])
    pip_findings = analysis_results.get("pip_audit", [])

    prompt = f"""
    You are an AI code reviewer. Review the following code changes:
    ---- CODE DIFF ----
    {diff_data[:1000]}  # truncated for safety
    -------------------

    Static Analysis Findings:
    SEMGREP: {json.dumps(semgrep_findings[:5], indent=2)}
    PIP-AUDIT: {json.dumps(pip_findings[:5], indent=2)}

    Please provide clear, concise review comments for improvement.
    """
    return prompt


# ------------------------
# STEP 5: Invoke Copilot Agent SDK (Mock)
# ------------------------
def invoke_copilot_agent(prompt: str):
    """
    Placeholder for GitHub Copilot Agent SDK (AI Review).
    In real use: send `prompt` to Copilot Agent SDK API.
    """
    print("Invoking Copilot Agent with prompt...")
    # For POC, simulate AI feedback:
    ai_response = """
    - Consider adding input validation in function `process_data`.
    - Unused import detected in utils.py.
    - Dependency `requests` is outdated, upgrade recommended.
    """
    return ai_response


# ------------------------
# STEP 6: Post Comments to PR
# ------------------------
def post_review_comment(repo_full_name, pr_number, ai_feedback):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    comment = {
        "body": f" **AI Review Summary:**\n{ai_feedback}"
    }

    url = f"{GITHUB_API}/repos/{repo_full_name}/issues/{pr_number}/comments"
    response = requests.post(url, headers=headers, json=comment)

    if response.status_code == 201:
        print("💬 AI review comment posted successfully!")
    else:
        print("Failed to post review comment:", response.text)
