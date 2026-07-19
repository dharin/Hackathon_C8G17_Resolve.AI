from functools import lru_cache

from fastembed import TextEmbedding

# fastembed ships ONNX builds of both configured embedding models, so no
# torch/GPU dependency is needed for the hackathon deployment.
_MODEL_ALIASES = {
    "BAAI/bge-small-en": "BAAI/bge-small-en",
    "nomic-embed-text": "nomic-ai/nomic-embed-text-v1.5",
}


class Embedder:
    """Thin wrapper around the configured embedding model so callers never
    depend on which model/backend is active — see RAG_EMBEDDING_MODEL.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en") -> None:
        self.model_name = model_name
        self._model = _load_model(_MODEL_ALIASES.get(model_name, model_name))

    @property
    def dimension(self) -> int:
        return len(next(self._model.embed(["dimension probe"])))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self._model.query_embed(text)).tolist()


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)
