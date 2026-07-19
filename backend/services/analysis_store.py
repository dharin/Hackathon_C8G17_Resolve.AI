from config.settings import ANALYSES_DIR
from models.upload_analysis import UploadAnalysisResult


def save_analysis(result: UploadAnalysisResult) -> None:
    path = ANALYSES_DIR / f"{result.analysis_id}.json"
    path.write_text(result.model_dump_json(), encoding="utf-8")


def load_analysis(analysis_id: str) -> UploadAnalysisResult | None:
    path = ANALYSES_DIR / f"{analysis_id}.json"
    if not path.exists():
        return None
    return UploadAnalysisResult.model_validate_json(path.read_text(encoding="utf-8"))
