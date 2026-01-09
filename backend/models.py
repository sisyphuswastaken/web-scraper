from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, Any

class ProcessRequest(BaseModel):
    url: HttpUrl
    options: Optional[Dict[str, Any]] = None

class ArticleInfo(BaseModel):
    title: str
    url: str
    authors: List[str]
    publish_date: Optional[str]

class Stats(BaseModel):
    chunks: int
    raw_entities: int
    entities: int
    relationships: int
    nodes: int
    edges: int

class GraphResponse(BaseModel):
    success: bool
    graph: Dict[str, Any]  # JSON graph data
    article_info: Dict[str, Any]
    stats: Dict[str, Any]
    message: Optional[str] = None

class ArticleResponse(BaseModel):
    success: bool
    url: str
    title: str
    text: str
    authors: List[str]
    publish_date: Optional[str]