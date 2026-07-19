import config.settings  # noqa: F401  (loads .env before anything reads os.environ)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analyze import router as analyze_router
from api.me import router as me_router
from api.rag import router as rag_router
from api.upload import router as upload_router

app = FastAPI(title="DevOps Incident Analysis Suite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(rag_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
