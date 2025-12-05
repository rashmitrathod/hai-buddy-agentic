import os
import uuid
import numpy as np
import pyarrow as pa
import lancedb

from backend.services.embedding_utils import get_single_embedding
from backend.services.embedding_normalizer import normalize_embedding
from backend.services.vector_store_lance import get_transcript_table


# ---------------------------------------------------------
# Local LanceDB path (works on Windows VM + Cloud Run)
# ---------------------------------------------------------
DB_PATH = os.path.join(os.getcwd(), "lancedb")
os.makedirs(DB_PATH, exist_ok=True)

# Single LanceDB client
db = lancedb.connect(DB_PATH)


# ---------------------------------------------------------
# 1. TRANSCRIPT TABLE
# ---------------------------------------------------------
def get_transcript_table():
    """
    LanceDB table for transcript chunks.
    Schema:
      video (string)
      chunk_index (int32)
      chunk (string)
      embedding (list<float32>)
    """
    schema = pa.schema([
        ("video", pa.string()),
        ("chunk_index", pa.int32()),
        ("chunk", pa.string()),
        ("embedding", pa.list_(pa.float32())),
    ])

    table_name = "transcripts"

    if table_name not in db.table_names():
        print("Creating LanceDB transcripts table...")
        return db.create_table(table_name, schema=schema)

    return db.open_table(table_name)


# ---------------------------------------------------------
# 2. MEMORY TABLE
# ---------------------------------------------------------
def get_memory_table():
    """
    Long-term memory table:
      text (string)
      embedding (list<float32>)
    """
    schema = pa.schema([
        ("text", pa.string()),
        ("embedding", pa.list_(pa.float32())),
    ])

    table_name = "memory"

    if table_name not in db.table_names():
        print("Creating LanceDB memory table...")
        return db.create_table(table_name, schema=schema)

    return db.open_table(table_name)


# ---------------------------------------------------------
# 3. INSERT TRANSCRIPT CHUNK
# ---------------------------------------------------------
def insert_transcript_chunk(video: str, chunk_index: int, chunk: str, embedding: list):
    table = get_transcript_table()

    row = {
        "video": video,
        "chunk_index": int(chunk_index),
        "chunk": chunk,
        "embedding": embedding,
    }

    table.add([row])


# ---------------------------------------------------------
# 4. QUERY TRANSCRIPT CHUNKS
# ---------------------------------------------------------
def query_chunks(question: str, top_k: int = 5):
    """
    Vector search for most relevant transcript chunks.
    Returns list[str] of chunks.
    """
    table = get_transcript_table()

    # ---- 1. Get embedding (Python list) ----
    raw_emb = get_single_embedding(question)

    # ---- 2. Normalize embedding for LanceDB ----
    query_emb = normalize_embedding(raw_emb)

    try:
        # ---- 3. Perform vector search ----
        qb = table.search(query_emb).limit(top_k)

        # LanceDB → Arrow table
        arrow_tbl = qb.to_arrow()

        # ---- 4. Extract chunks safely ----
        if "chunk" not in arrow_tbl.column_names:
            print("LanceDB error: 'chunk' column missing")
            return []

        chunks = arrow_tbl["chunk"].to_pylist()

        return chunks

    except Exception as e:
        print("LanceDB transcript search error:", e)
        return []

# ---------------------------------------------------------
# 5. WRITE MEMORY
# ---------------------------------------------------------
def write_memory(user_msg: str, assistant_msg: str):
    """
    Store conversation pair into LanceDB memory.
    """
    table = get_memory_table()

    text = f"User said: {user_msg}\nAssistant replied: {assistant_msg}"
    emb = get_single_embedding(text).astype(np.float32)

    row = {
        "text": text,
        "embedding": emb.tolist()
    }

    table.add([row])
    return True


# ---------------------------------------------------------
# 6. RECALL MEMORY
# ---------------------------------------------------------
def recall_memory(query: str):
    """
    Retrieve the most relevant memory snippet using vector search.
    """
    table = get_memory_table()
    q_emb = get_single_embedding(query).astype(np.float32)

    try:
        results = (
            table.search(q_emb)
            .limit(1)
            .select(["text"])
            .to_list()
        )
    except Exception as e:
        print("LanceDB memory search error:", e)
        return ""

    if not results:
        return ""

    return results[0]["text"]


# ---------------------------------------------------------
# 7. Optional: wipe DB (for debugging)
# ---------------------------------------------------------
def clear_all_data():
    """Deletes local LanceDB folder."""
    import shutil
    shutil.rmtree(DB_PATH, ignore_errors=True)
    os.makedirs(DB_PATH, exist_ok=True)
    print("LanceDB data cleared.")