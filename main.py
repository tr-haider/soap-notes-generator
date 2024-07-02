import streamlit as st
import openai
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF
from moviepy.editor import VideoFileClip
from datetime import datetime
# Load environment variables
load_dotenv()

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Directory to save uploaded files
UPLOAD_DIR = Path("./uploaded-notes")
UPLOAD_DIR.mkdir(exist_ok=True)

# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    save_path = UPLOAD_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    file_info = {
        "name": uploaded_file.name,
        "path": save_path,
        "size": str(round(int(uploaded_file.size),2)),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return file_info

# Function to read text from a txt file
def read_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# Function to extract text from XLSX
def extract_text_from_xlsx(xlsx_path):
    df = pd.read_excel(xlsx_path)
    text = df.to_string(index=False)
    return text

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text
def extract_text_from_audio(audio_file):
    transcription = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcription.text


# Function to extract text from video
def extract_text_from_video(video_path):
    video_path_str = str(video_path)
    # Extract audio from video
    video = VideoFileClip(video_path_str)
    audio_path = video_path.with_suffix(".wav")
    video.audio.write_audiofile(audio_path)

    # Transcribe audio to text
    text = extract_text_from_audio(audio_path)
    return text

# Function to query OpenAI GPT-4 for summarization
def query_openai(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except openai.OpenAIError as e:
        error_message = str(e)
        if "rate limit" in error_message.lower():
            st.error("You have exceeded the rate limit for GPT-4. Please try again later.")
        elif "context length" in error_message.lower():
            st.error(
                "Please reduce the length of your input. As a guideline, try to limit your input to approximately 8,000 words or about 16 pages of text. If possible, summarize the content yourself before submitting it for processing.")
        else:
            st.error(f"An error occurred with OpenAI: {e}")
        return None


def run_summarizer_app():
    try:
        # Streamlit App
        st.markdown(
            """
            <style>
                .stButton button {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 24px;
                    text-align: center;
                    font-size: 16px;
                    margin: 4px 2px;
                    transition: 0.3s;
                    border-radius: 12px;
                }
                .stButton button:hover {
                    background-color: #45a049;
                }
                #MainMenu {visibility: hidden;}
            </style>
            """,
            unsafe_allow_html=True
        )

        st.title("Meeting Notes Summarizer")
        summary_type = st.text_input("Specify the type of summary you need (e.g., action items, conclusions)")

        # Sidebar for uploading multiple files
        st.sidebar.title("Upload Meeting Notes")
        uploaded_files = st.sidebar.file_uploader("Upload files",
                                                  type=["txt", "xlsx", "pdf", "mp3", "wav", "mp4", "mkv", "avi"],
                                                  accept_multiple_files=True)

        files_info = []
        for uploaded_file in uploaded_files:
            file_info = save_uploaded_file(uploaded_file)
            files_info.append(file_info)

        selected_file = st.sidebar.selectbox(
            "Select a file to view details",
            files_info,
            format_func=lambda x: x['name']
        )

        if selected_file:
            st.sidebar.write(f"**Timestamp:** {selected_file['timestamp']}")
            st.sidebar.write(f"**File Size:** {selected_file['size']} bytes")
            st.sidebar.write(f"**Original File Name:** {selected_file['name']}")

        if st.button("Summarize") and selected_file:
            file_extension = selected_file["name"].split('.')[-1]
            if file_extension == "txt":
                notes_text = read_text_file(selected_file["path"])
            elif file_extension == "xlsx":
                notes_text = extract_text_from_xlsx(selected_file["path"])
            elif file_extension == "pdf":
                notes_text = extract_text_from_pdf(selected_file["path"])
            elif file_extension in ["mp3", "wav"]:
                notes_text = extract_text_from_audio(selected_file["path"])
            elif file_extension in ["mp4", "mkv", "avi"]:
                notes_text = extract_text_from_video(selected_file["path"])
            else:
                st.error("Unsupported file type")
                return

            with st.spinner('Summarizing...'):
                prompt = f"Summarize in points the following meeting notes with a focus on {summary_type}:\n\n{notes_text}\n\nSummary:"
                summary = query_openai(prompt)

                # Tabs for Transcription and Summary
                tab1, tab2 = st.tabs(["Extracted Text", "Summary"])

                with tab1:
                    st.write(notes_text)

                with tab2:
                    if summary:
                        st.write(summary)
                    else:
                        st.write("Could not generate summary for this file.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

run_summarizer_app()
