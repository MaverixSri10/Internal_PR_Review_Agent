from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def webhook_listener(request: Request):
    payload = await request.json()
    action = payload.get("action")
    pr_info = payload.get("pull_request", {})

    print(f"PR Triggered: {action}")
    print(f"Title: {pr_info.get('title')}")
    print(f"URL: {pr_info.get('html_url')}")
    return {"status": "received"}
