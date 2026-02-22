import hashlib

def hash_question(question: str) -> str:
  return hashlib.sha256(question.encode("utf-8")).hexdigest()