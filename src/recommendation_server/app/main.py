from fastapi import FastAPI

app = FastAPI(title="Recommendation Server")


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "recommendation_server",
        "message": "Recommendation server is running.",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
