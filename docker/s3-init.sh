#!/bin/sh
# Runs inside the LocalStack container once S3 is ready (awslocal = aws CLI pointed at LocalStack).
# Same setup you would do once in the AWS console for a real bucket.
set -e

for bucket in supportflow-documents supportflow-documents-test; do
  awslocal s3api create-bucket --bucket "$bucket" >/dev/null 2>&1 || true

  # Browsers upload straight to S3 (presigned POST), so S3 itself must allow our frontend origin.
  awslocal s3api put-bucket-cors --bucket "$bucket" --cors-configuration '{
    "CORSRules": [{
      "AllowedOrigins": ["http://localhost:3000", "http://127.0.0.1:3000"],
      "AllowedMethods": ["POST", "GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }]
  }'
  echo "S3 bucket ready: $bucket"
done
