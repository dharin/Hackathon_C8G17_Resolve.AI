import config.settings  # noqa: F401  (loads .env before anything reads os.environ)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.me import router as me_router

app = FastAPI(title="DevOps Incident Analysis Suite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
