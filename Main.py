# main.py
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook_listener(request: Request):
    data = await request.json()
    if data.get("action") == "opened" and "pull_request" in data:
        pr = data["pull_request"]
        pr_number = pr["number"]
        repo_name = data["repository"]["full_name"]
        print(f"🎯 New PR #{pr_number} in {repo_name}")
        # Here you can trigger your analysis or Copilot review agent
    return {"status": "ok"}
