django-cached-s3-storage
========================

This package contains a CachedS3BotoStorage to be used with django-compressor and S3.

Code copied from https://github.com/jezdez/django_compressor/issues/100.

Example settings:
::

	DEFAULT_FILE_STORAGE = 'cached_s3_storage.MediaRootS3BotoStorage'
	STATICFILES_STORAGE = 'cached_s3_storage.StaticRootS3BotoStorage'
	COMPRESS_STORAGE = 'cached_s3_storage.CachedRootS3BotoStorage'

	AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
	AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
	AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
	AWS_PRELOAD_METADATA = True
	AWS_IS_GZIPPED = True
	AWS_QUERYSTRING_AUTH = False

	from django.utils.http import http_date
	from time import time
	max_age = 31536000
	AWS_HEADERS = {
		'x-amz-acl': 'public-read',
		'Expires': http_date(time() + max_age),
		'Cache-Control': 'public, max-age=' + str(max_age)
	}