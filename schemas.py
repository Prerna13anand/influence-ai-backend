from pydantic import BaseModel
from datetime import datetime

class Post(BaseModel):
    id: int
    post_text: str
    created_at: datetime

    class Config:
        from_attributes = True # This tells Pydantic to read the data from a database object