def is_hinglish(text: str) -> bool:
    hindi_words = [
        "kya", "kaise", "batao", "bata", "hai", "tha", "hun", "hona",
        "matlab", "kyu", "ka", "ki", "ho", "bhai", "dost", "mujhe",
        "samjha", "samjhao"
    ]
    score = sum(1 for w in hindi_words if w in text.lower())
    return score >= 1