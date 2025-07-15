from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import default_storage
default_storage._wrapped = S3Boto3Storage()
