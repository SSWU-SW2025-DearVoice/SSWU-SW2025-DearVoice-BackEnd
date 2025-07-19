import boto3
from django.conf import settings

def generate_presigned_url(file_field, expires_in=3600):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, 'AWS_REGION', 'ap-northeast-2')
    )
    bucket = file_field.storage.bucket_name
    key = file_field.name
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expires_in
    )
    return url