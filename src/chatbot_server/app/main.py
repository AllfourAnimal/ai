from fastapi import FastAPI

app = FastAPI(title="Chatbot Server")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "chatbot_server",
        "message": "Chatbot server is running.",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
