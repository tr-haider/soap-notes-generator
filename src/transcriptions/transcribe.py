import boto3
import time
import requests
import re
from src.configs import env
import streamlit as st

transcribe_client = boto3.client(
    'transcribe',
    aws_access_key_id=env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1'
)

def sanitize_job_name(job_name):
    """
    Sanitize job name to only contain characters allowed by AWS Transcribe:
    Pattern: ^[0-9a-zA-Z._-]+
    Replaces invalid characters with hyphens and removes consecutive hyphens.
    """
    # Replace any character that is not alphanumeric, period, underscore, or hyphen with a hyphen
    sanitized = re.sub(r'[^0-9a-zA-Z._-]', '-', job_name)
    # Replace multiple consecutive hyphens with a single hyphen
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    # Ensure it's not empty and doesn't exceed AWS limits (max 200 characters)
    if not sanitized:
        sanitized = 'transcription-job'
    return sanitized[:200]

def transcribe(file_url, job_name, format):
    try:
        # Sanitize job name to meet AWS Transcribe requirements
        sanitized_job_name = sanitize_job_name(job_name)
        
        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=sanitized_job_name,
            Media={'MediaFileUri': file_url},
            MediaFormat=format,  # Change this based on your audio format
            LanguageCode='en-US',
        )

        # Poll for job completion
        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=sanitized_job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            print('Waiting for transcription job to complete...')
            time.sleep(30)  # Wait 30 seconds before polling again

        # Check if job failed
        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'FAILED':
            st.error("Transcription job failed.")
            return None

        # Get the transcription result
        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']

        # Fetch the transcription result
        result = requests.get(transcript_uri)
        result.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        result_json = result.json()

        # Extract text from the JSON response
        transcript_text = result_json['results']['transcripts'][0]['transcript']
        return transcript_text

    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching the transcription result: {e}")
    except Exception as e:
        st.error(f"An error occurred during transcription: {e}")