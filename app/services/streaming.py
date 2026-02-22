from app.schemas.chat import ChatRequest
from app.utils.hashing import hash_question

class ChatStreaming():
  def get_chat_stream(chat_request: ChatRequest):
    question_hash = hash_question(chat_request.question)