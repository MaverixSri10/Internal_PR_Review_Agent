from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    print("Received webhook:", payload)
    if payload.get("action") in ["opened", "synchronize"]:
        print("PR Triggered")
    return {"status": "ok"}
