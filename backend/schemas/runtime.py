from pydantic import BaseModel


class IngestionResponse(BaseModel):
    status: str
    source: str
    fetched: int
    stored: int
    duplicates: int
    cursor: str | None = None
    incident_links_created: int
