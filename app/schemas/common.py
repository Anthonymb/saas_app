from typing import Generic, List, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class MessageResponse(BaseModel):
    message: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
