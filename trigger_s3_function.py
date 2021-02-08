import json
import pandas as pd
import boto3
import io


def lambda_handler(event, context):
    client = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    filename = key.split('/')[-1]
    response = client.get_object(
        Bucket=bucket,
        Key=key
    )
    df = pd.read_csv(response['Body'])
    df.dropna(inplace=True)
    # buffer = io.StringIO()
    # df.to_csv(buffer)
    # buffer.seek(0)
    # client.put_object(Body=buffer.getvalue(), Bucket=bucket, Key=f'data/{filename}')
    # Features to be used
    features = ['Rating', 'Reviews', 'Size', 'Installs',
                'Type', 'Category', 'Price', 'Content Rating', 'Genres']
    df = df.loc[:, features]

    # Function to convert categorical data
    def convert_category_like(s):
        temp_dict = {}
        for i, k in enumerate(s.unique()):
            temp_dict[k] = i
        return s.map(temp_dict).astype(int)
    # Function to convert size

    def convert_size(s):
        if s[-1] == 'M':
            ans = float(s[:-1])*1000000
        elif s[-1] == 'k':
            ans = float(s[:-1])*1000
        else:
            ans = None
        return ans

    # Convert categorical data
    df['Category_c'] = convert_category_like(df['Category'])
    df['Content Rating'] = convert_category_like(df['Content Rating'])
    df['Genres_c'] = convert_category_like(df['Genres'])

    # Convert string to numeric
    df['Reviews'] = df['Reviews'].astype('int64')
    # Convert Size
    df['Size'] = df['Size'].map(convert_size)
    # Some size value is "Varies with device", we fill those value with mean groupby categories
    df['Size'] = df.groupby('Category_c')['Size'].transform(
        lambda x: x.fillna(round(x.mean())))

    # Convert Installs to numeric
    df['Installs'] = df['Installs'].map(
        lambda x: int(x[:-1].replace(',', '')), )
    # Convert Type to binary
    df['Type'] = df['Type'].map(lambda x: 0 if x == 'Free' else 1)
    # Convert Price to numeric
    df['Price'] = df['Price'].map(lambda x: 0 if x == '0' else float(x[1:]))

    # split training data and testing data
    training_df = df.sample(frac=0.8, random_state=24)
    testing_df = df.drop(training_df.index)
    # upload training data
    buffer = io.StringIO()
    training_df.to_csv(buffer)
    buffer.seek(0)
    client.put_object(Body=buffer.getvalue(), Bucket=bucket,
                      Key=f'training_data/{filename}')
    # upload testing data
    buffer = io.StringIO()
    testing_df.to_csv(buffer)
    buffer.seek(0)
    client.put_object(Body=buffer.getvalue(), Bucket=bucket,
                      Key=f'testing_data/{filename}')
    return {
        'statusCode': 200,
        'body': 'LGTM'
    }
