from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def home():
    return {"status": "app is running"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("Webhook ontvangen:", data)
    return {"status": "ok", "received": data}