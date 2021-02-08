import json
import boto3


def lambda_handler(event, context):
    bucket = 'ncusg-s3storage'
    client = boto3.client('s3')
    response = client.list_objects_v2(
        Bucket=bucket,
        Prefix='Data_lake/',
        StartAfter='Data_lake/'
    )

    objects_to_delete = [{'Key': i['Key']} for i in response['Contents']]

    delete_response = client.delete_objects(
        Bucket=bucket,
        Delete={
            'Objects': objects_to_delete
        }
    )
    return {
        'statusCode': 200,
        'body': 'LGTM'
    }
