from pydantic import BaseModel


class ShareableReport(BaseModel):
    pre_signed_s3_upload_url: str
    pre_signed_cloudfront_share_url: str
