import uuid
from backend.services.embedding_utils import get_single_embedding
from backend.services.vector_store import get_memory_collection


class ConversationMemory:
    """
    Stores short-term memory (session-specific)
    """
    def __init__(self):
        self.sessions = {}  # session_id → list of message pairs

    def add_message(self, session_id: str, user_msg: str, assistant_msg: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append({
            "user": user_msg,
            "assistant": assistant_msg
        })

        # Keep last 5 turns only
        self.sessions[session_id] = self.sessions[session_id][-5:]

    def get_history(self, session_id: str):
        return self.sessions.get(session_id, [])


# ============================
# 🔥 Long-Term Memory Store
# ============================

def write_memory(user_msg: str, assistant_msg: str):
    """
    Store important info from a conversation turn in ChromaDB memory collection.
    """
    text = f"User said: {user_msg}\nAssistant replied: {assistant_msg}"

    embedding = get_single_embedding(text)
    memory_collection = get_memory_collection

    memory_id = f"mem_{uuid.uuid4()}"

    memory_collection.add(
        ids=[memory_id],
        metadatas=[{"type": "conversation_memory"}],
        documents=[text],
        embeddings=[embedding]
    )

    return True


def recall_memory(query: str) -> str:
    """
    Retrieve the most relevant memory snippet for this query.
    """
    embedding = get_single_embedding(query)
    memory_collection = get_memory_collection

    results = memory_collection.query(
        query_embeddings=[embedding],
        n_results=1
    )

    if results and results["documents"] and len(results["documents"][0]) > 0:
        return results["documents"][0][0]

    return ""