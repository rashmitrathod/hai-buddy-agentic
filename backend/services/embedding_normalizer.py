import numpy as np

def normalize_embedding(emb):
    """
    Accepts emb in any of these forms:
    - Python list
    - float list
    - numpy array
    - OpenAI embedding object
    Returns: Python list[float32]
    """
    try:
        arr = np.array(emb, dtype=np.float32)
        return arr.tolist()
    except Exception:
        # fallback: try manual conversion
        return [float(x) for x in emb]