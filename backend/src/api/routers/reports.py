"""
Reports API router
"""

import os
import json
import boto3
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel
from botocore.exceptions import ClientError, NoCredentialsError
from uuid import uuid4

from ...database.connection import get_db
from ..services.sighting_service import SightingService
from ..services.ringing_service import RingingService

router = APIRouter()

# S3 Configuration
S3_BUCKET = "vogelring-data"
S3_REGION = os.getenv("AWS_REGION", "eu-central-1")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")


class ShareableReportRequest(BaseModel):
    """Request model for creating shareable reports"""

    days: int
    html: str


class ReportMetadata(BaseModel):
    """Response model for a generated report"""

    view_url: str


def get_s3_client():
    """Get S3 client with error handling"""
    try:
        return boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not configured")


@router.post("/report/shareable", response_model=ReportMetadata)
async def create_shareable_report(request: ShareableReportRequest):
    """Generate a shareable report and upload to S3"""
    s3_client = get_s3_client()
    report_uuid = str(uuid4())
    validity_date = datetime.now() + timedelta(days=request.days)
    s3_key = f"reports/{report_uuid}/expires={validity_date.strftime('%Y-%m-%d')}/report.html"
    s3_client.put_object(
        Bucket="vogelring-reports",
        Key=s3_key,
        Body=request.html.encode("utf-8"),
        ContentType="text/html",
        Tagging=f"retention={request.days}",
    )
    # Make the object public
    s3_client.put_object_acl(
        Bucket="vogelring-reports",
        Key=s3_key,
        ACL="public-read",
    )

    return ReportMetadata(
        view_url=f"https://vogelring-reports.s3.amazonaws.com/{s3_key}"
    )


@router.get("/report/presigned-url")
async def get_presigned_download_url(
    s3_key: str = Query(..., description="S3 key of the report file"),
    expiry_hours: int = Query(
        24, ge=1, le=168, description="URL expiry in hours (max 7 days)"
    ),
):
    """Generate a new presigned URL for an existing report"""

    try:
        s3_client = get_s3_client()

        # Check if object exists
        try:
            s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise HTTPException(status_code=404, detail="Report not found")
            raise

        # Generate new presigned URL
        download_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=expiry_hours * 3600,
        )

        return {
            "download_url": download_url,
            "expires_at": (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
            "s3_key": s3_key,
        }

    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate presigned URL: {str(e)}"
        )


@router.get("/report/list")
async def list_reports(
    prefix: str = Query("reports/", description="S3 prefix to list reports from"),
    max_results: int = Query(
        100, ge=1, le=1000, description="Maximum number of reports to return"
    ),
):
    """List available reports in S3"""

    try:
        s3_client = get_s3_client()

        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=max_results
        )

        reports = []
        if "Contents" in response:
            for obj in response["Contents"]:
                # Get object metadata
                try:
                    head_response = s3_client.head_object(
                        Bucket=S3_BUCKET, Key=obj["Key"]
                    )
                    metadata = head_response.get("Metadata", {})

                    reports.append(
                        {
                            "s3_key": obj["Key"],
                            "title": metadata.get("title", "Unknown"),
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"].isoformat(),
                            "created_at": metadata.get("created_at"),
                            "expires_at": metadata.get("expires_at"),
                        }
                    )
                except ClientError:
                    # Skip objects we can't access
                    continue

        return {
            "reports": reports,
            "total_count": len(reports),
            "truncated": response.get("IsTruncated", False),
        }

    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.delete("/report/{report_id}")
async def delete_report(report_id: str):
    """Delete a report from S3"""

    try:
        s3_client = get_s3_client()
        s3_key = f"reports/{report_id}.json"

        # Check if object exists
        try:
            s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise HTTPException(status_code=404, detail="Report not found")
            raise

        # Delete the object
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

        return {"message": f"Report {report_id} deleted successfully"}

    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete report: {str(e)}"
        )
