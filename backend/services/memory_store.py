from backend.services.vector_store_lance import (
    write_memory as lancedb_write_memory,
    recall_memory as lancedb_recall_memory,
)


class ConversationMemory:
    """
    Stores short-term, in-session conversation memory.
    This stays in RAM (not persisted).
    """
    def __init__(self):
        self.sessions = {}  # session_id → list of turns

    def add_message(self, session_id: str, user_msg: str, assistant_msg: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append({
            "user": user_msg,
            "assistant": assistant_msg
        })

        # Keep only last 5 turns
        self.sessions[session_id] = self.sessions[session_id][-5:]

    def get_history(self, session_id: str):
        return self.sessions.get(session_id, [])


# ============================
# 🔥 Long-Term Memory (LanceDB)
# ============================

def write_memory(user_msg: str, assistant_msg: str):
    """
    Persist memory to LanceDB.
    """
    text = f"User said: {user_msg}\nAssistant replied: {assistant_msg}"
    return lancedb_write_memory(text)


def recall_memory(query: str) -> str:
    """
    Retrieve best-matching memory snippet from LanceDB.
    """
    result = lancedb_recall_memory(query)
    return result or ""