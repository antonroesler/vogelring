import uuid
import boto3
from aws_lambda_powertools import Logger
from datetime import datetime, timedelta
from botocore.config import Config
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from api.models.report import ShareableReport
from api import conf
from api.utils import has_access


logger = Logger()
s3 = boto3.client("s3", config=Config(retries=dict(max_attempts=3)))


def rsa_signer(message):
    """Returns signed message using CloudFront private key from Parameter Store"""
    # Get private key from Parameter Store
    parameter_name = conf.CLOUDFRONT_PRIVATE_KEY_PARAM_NAME
    region = conf.AWS_REGION

    ssm_client = boto3.client("ssm", region_name=region, config=Config(retries=dict(max_attempts=3)))

    try:
        # Get the private key from Parameter Store (SecureString parameter)
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True,  # Important: decrypt the secure string
        )
        private_key_string = response["Parameter"]["Value"]

        # Load the private key
        private_key = serialization.load_pem_private_key(private_key_string.encode("utf-8"), password=None)

        print(f"Loaded private key from Parameter Store: {private_key}")

        # Sign the message with SHA-1 (required for CloudFront)
        return private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA1(),  # CloudFront requires SHA-1
        )
    except Exception as e:
        print(f"Error getting private key from Parameter Store: {str(e)}")
        raise


def post_shareable_report(days: int, html_content: str = None, user: str | None = None) -> ShareableReport:
    """Generate pre-signed URLs for S3 upload and CloudFront distribution"""

    if user is None:
        raise ValueError("User is required")

    if not has_access(user):
        raise ValueError("User does not have access")

    # Get environment variables
    bucket_name = conf.BUCKET
    cloudfront_domain = conf.CLOUDFRONT_DOMAIN
    key_pair_id = conf.CLOUDFRONT_KEY_PAIR_ID

    # Generate unique filename
    report_id = str(uuid.uuid4())
    s3_key = f"reports/{report_id}.html"

    try:
        # Generate pre-signed S3 URL for upload
        upload_shareable_report(bucket_name, s3_key, html_content)

        # Generate pre-signed CloudFront URL
        cloudfront_signer = CloudFrontSigner(key_pair_id, rsa_signer)

        # Set expiration for the CloudFront URL
        expire_date = datetime.utcnow() + timedelta(days=days)

        cloudfront_url = f"https://{cloudfront_domain}/{s3_key}"
        pre_signed_cloudfront_share_url = cloudfront_signer.generate_presigned_url(
            cloudfront_url, date_less_than=expire_date
        )

        return ShareableReport(view_url=pre_signed_cloudfront_share_url)

    except Exception as e:
        print(f"Error generating pre-signed URLs: {str(e)}")
        raise


def upload_shareable_report(bucket, key, content) -> ShareableReport:
    """Upload to s3"""
    logger.info("Uploading HTML content to S3")
    s3.put_object(Bucket=bucket, Key=key, Body=content.encode("utf-8"), ContentType="text/html")
