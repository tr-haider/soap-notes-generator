import boto3
import time
import requests
from src.configs import env
import streamlit as st

transcribe_client = boto3.client(
    'transcribe',
    aws_access_key_id=env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1'
)
def transcribe(file_url, job_name, format):
    try:
        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_url},
            MediaFormat=format,  # Change this based on your audio format
            LanguageCode='en-US',
        )

        # Poll for job completion
        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
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