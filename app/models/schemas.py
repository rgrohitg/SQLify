from pydantic import BaseModel


# Schema for feedback submission
class FeedbackRequest(BaseModel):
    request_id: str
    rating: int  # 1 to 5
    message: str = None


# Schema for NLP to SQL conversion request
class NLPQueryRequest(BaseModel):
    query: str


# Schema for NLP to SQL conversion response
class NLPQueryResponse(BaseModel):
    query: str
    formatted_data: str
