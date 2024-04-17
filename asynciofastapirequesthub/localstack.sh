#!/bin/bash
export AWS_ACCESS_KEY_ID=foo
export AWS_SECRET_ACCESS_KEY=bar

echo "Create SQS queues..."
awslocal sqs create-queue --queue-name ProviderHubApiDLQueuelocal
awslocal sqs create-queue --queue-name ProviderHubApiJobsQueuelocal

echo "Create S3 buckets..."
awslocal s3api create-bucket --bucket provider-hub-api-jobs-local


echo "All Queues"
awslocal sqs list-queues

echo "All Buckets:"
awslocal s3api list-buckets
