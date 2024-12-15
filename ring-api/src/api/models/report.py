from pydantic import BaseModel


class ShareableReport(BaseModel):
    view_url: str
