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

from ...database.connection import get_db
from ..services.sighting_service import SightingService
from ..services.ringing_service import RingingService

router = APIRouter()

# S3 Configuration
S3_BUCKET = "vogelring-data"
S3_REGION = os.getenv("AWS_REGION", "eu-central-1")


class ShareableReportRequest(BaseModel):
    """Request model for creating shareable reports"""
    title: str
    description: str | None = None
    filters: Dict[str, Any] | None = None
    include_sightings: bool = True
    include_ringings: bool = True
    expiry_days: int = 7  # How long the report should be accessible


class ReportMetadata(BaseModel):
    """Metadata for a generated report"""
    report_id: str
    title: str
    description: str | None
    created_at: str
    expires_at: str
    download_url: str
    file_size: int | None = None


def get_s3_client():
    """Get S3 client with error handling"""
    try:
        return boto3.client('s3', region_name=S3_REGION)
    except NoCredentialsError:
        raise HTTPException(
            status_code=500, 
            detail="AWS credentials not configured"
        )


@router.post("/report/shareable", response_model=ReportMetadata)
async def create_shareable_report(
    request: ShareableReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a shareable report and upload to S3"""
    
    try:
        # Generate unique report ID
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.title) % 10000:04d}"
        
        # Collect data based on filters
        report_data = {
            "metadata": {
                "report_id": report_id,
                "title": request.title,
                "description": request.description,
                "created_at": datetime.now().isoformat(),
                "filters": request.filters or {},
                "generated_by": "Vogelring API"
            },
            "data": {}
        }
        
        # Get sightings data if requested
        if request.include_sightings:
            sighting_service = SightingService(db)
            if request.filters:
                sightings = sighting_service.search_sightings(request.filters)
            else:
                sightings = sighting_service.get_sightings(limit=10000)  # Reasonable limit
            
            # Convert to serializable format
            sightings_data = []
            for sighting in sightings:
                sighting_dict = {
                    "id": str(sighting.id),
                    "species": sighting.species,
                    "ring": sighting.ring,
                    "date": sighting.date.isoformat() if sighting.date else None,
                    "place": sighting.place,
                    "lat": float(sighting.lat) if sighting.lat else None,
                    "lon": float(sighting.lon) if sighting.lon else None,
                    "melder": sighting.melder,
                    "comment": sighting.comment
                }
                sightings_data.append(sighting_dict)
            
            report_data["data"]["sightings"] = sightings_data
            report_data["metadata"]["sightings_count"] = len(sightings_data)
        
        # Get ringings data if requested
        if request.include_ringings:
            ringing_service = RingingService(db)
            if request.filters:
                ringings = ringing_service.search_ringings(request.filters)
            else:
                ringings = ringing_service.get_all_ringings(limit=10000)  # Reasonable limit
            
            # Convert to serializable format
            ringings_data = []
            for ringing in ringings:
                ringing_dict = {
                    "id": str(ringing.id),
                    "ring": ringing.ring,
                    "species": ringing.species,
                    "date": ringing.date.isoformat(),
                    "place": ringing.place,
                    "lat": float(ringing.lat),
                    "lon": float(ringing.lon),
                    "ringer": ringing.ringer,
                    "sex": ringing.sex,
                    "age": ringing.age
                }
                ringings_data.append(ringing_dict)
            
            report_data["data"]["ringings"] = ringings_data
            report_data["metadata"]["ringings_count"] = len(ringings_data)
        
        # Convert to JSON
        report_json = json.dumps(report_data, indent=2, ensure_ascii=False)
        report_bytes = report_json.encode('utf-8')
        
        # Upload to S3
        s3_client = get_s3_client()
        s3_key = f"reports/{report_id}.json"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=report_bytes,
            ContentType='application/json',
            Metadata={
                'title': request.title,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=request.expiry_days)).isoformat()
            }
        )
        
        # Generate presigned URL (max 7 days for S3 presigned URLs)
        presigned_expiry = min(request.expiry_days, 7) * 24 * 3600  # Convert to seconds
        
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=presigned_expiry
        )
        
        return ReportMetadata(
            report_id=report_id,
            title=request.title,
            description=request.description,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=request.expiry_days)).isoformat(),
            download_url=download_url,
            file_size=len(report_bytes)
        )
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload report to S3: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/report/presigned-url")
async def get_presigned_download_url(
    s3_key: str = Query(..., description="S3 key of the report file"),
    expiry_hours: int = Query(24, ge=1, le=168, description="URL expiry in hours (max 7 days)")
):
    """Generate a new presigned URL for an existing report"""
    
    try:
        s3_client = get_s3_client()
        
        # Check if object exists
        try:
            s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise HTTPException(status_code=404, detail="Report not found")
            raise
        
        # Generate new presigned URL
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=expiry_hours * 3600
        )
        
        return {
            "download_url": download_url,
            "expires_at": (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
            "s3_key": s3_key
        }
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


@router.get("/report/list")
async def list_reports(
    prefix: str = Query("reports/", description="S3 prefix to list reports from"),
    max_results: int = Query(100, ge=1, le=1000, description="Maximum number of reports to return")
):
    """List available reports in S3"""
    
    try:
        s3_client = get_s3_client()
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix,
            MaxKeys=max_results
        )
        
        reports = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # Get object metadata
                try:
                    head_response = s3_client.head_object(Bucket=S3_BUCKET, Key=obj['Key'])
                    metadata = head_response.get('Metadata', {})
                    
                    reports.append({
                        "s3_key": obj['Key'],
                        "title": metadata.get('title', 'Unknown'),
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "created_at": metadata.get('created_at'),
                        "expires_at": metadata.get('expires_at')
                    })
                except ClientError:
                    # Skip objects we can't access
                    continue
        
        return {
            "reports": reports,
            "total_count": len(reports),
            "truncated": response.get('IsTruncated', False)
        }
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )


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
            if e.response['Error']['Code'] == '404':
                raise HTTPException(status_code=404, detail="Report not found")
            raise
        
        # Delete the object
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        
        return {"message": f"Report {report_id} deleted successfully"}
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete report: {str(e)}"
        )