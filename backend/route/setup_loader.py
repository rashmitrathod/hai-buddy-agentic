from fastapi import APIRouter
from backend.services.load_transcripts_lance import load_and_index_transcripts

router = APIRouter()

@router.get("/setup")
def setup_transcripts():
    """
    Manually trigger transcript → embeddings → LanceDB indexing.
    Safe to run multiple times. Replaces old data for same video chunks.
    """
    try:
        count = load_and_index_transcripts()
        return {"status": "ok", "indexed_files": count}
    except Exception as e:
        print(f'Exception: {e}')
        return {"status": "error", "message": str(e)}