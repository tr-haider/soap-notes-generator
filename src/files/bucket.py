import sys
import os
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import requests
from io import BytesIO
import fitz  # PyMuPDF
import pandas as pd
import streamlit as st
import wave
import struct

# Go up two levels to include the `src` directory
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
from src.configs import env

s3_client = boto3.client(
    's3',
    aws_access_key_id = env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = env.AWS_SECRET_ACCESS_KEY,
    region_name = 'us-east-1'
)
response = s3_client.list_buckets()
buckets = response['Buckets']
bucket_name = [bucket for bucket in buckets if bucket['Name'] == "soap-notes-app"][0]['Name']

# Function to upload file content directly to S3
def upload_file_to_s3(file_content, file_name, folder_name, region_name='us-east-1'):
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        s3_file_path = f'{folder_name}/{current_time}-{file_name}'
        file_obj = BytesIO(file_content)
        s3_client.upload_fileobj(file_obj, bucket_name, s3_file_path)
        file_url = f'https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_file_path}'
        return file_url
    except NoCredentialsError:
        st.error('Credentials not available.')
    except PartialCredentialsError:
        st.error('Incomplete credentials.')
    except ClientError as e:
        st.error(f'An error occurred: {e}')
    return None


def upload_recording_to_s3(audio_frames, folder_name, file_name, region_name='us-east-1'):
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        s3_file_path = f'{folder_name}/{current_time}-{file_name}'
        # Prepare audio data for S3 upload
        file_obj = BytesIO()
        with wave.open(file_obj, 'wb') as f:
            f.setparams((1, 2, 16000, 512, "NONE", "NONE"))
            f.writeframes(struct.pack("h" * len(audio_frames), *audio_frames))

        # Reset file_obj's position to the beginning
        file_obj.seek(0)

        # Upload to S3
        s3_client.upload_fileobj(file_obj, bucket_name, s3_file_path)
        file_url = f'https://{bucket_name}.s3.{region_name}.amazonaws.com/{s3_file_path}'
        return file_url
    except NoCredentialsError:
        st.error('Credentials not available.')
    except PartialCredentialsError:
        st.error('Incomplete credentials.')
    except ClientError as e:
        st.error(f'An error occurred: {e}')
    return None


def read_file_from_url(file_url, file_type):
    """
    Reads the content of a file from a given URL based on the file type.

    Parameters:
        file_url (str): URL of the file to read.
        file_type (str): Type of the file ('txt', 'pdf', 'xlsx').

    Returns:
        str: Content of the file if successful, else None.
    """
    try:
        response = requests.get(file_url)
        response.raise_for_status()  # Check for HTTP errors

        if file_type == 'txt':
            return response.text

        elif file_type == 'pdf':
            pdf_content = BytesIO(response.content)
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            return text

        elif file_type == 'xlsx':
            xlsx_content = BytesIO(response.content)
            df = pd.read_excel(xlsx_content, sheet_name=None)
            text = ""
            for sheet_name, sheet_df in df.items():
                text += sheet_df.to_string(index=False)
            return text

        else:
            print(f'Unsupported file type: {file_type}')
            return None

    except requests.RequestException as e:
        print(f'An error occurred while fetching the file: {e}')
        return None



