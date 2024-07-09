import streamlit as st
import openai
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF
from moviepy.editor import VideoFileClip
from datetime import datetime
from streamlit_mic_recorder import speech_to_text
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor,as_completed
import whisper

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
def create_chunks(wav_file):
    audio = AudioSegment.from_wav(wav_file)
    chunk_length_ms = 60000
    transcribed_text = ""
    chunk_file_names = []
    # create a directory to store the audio chunks.
    try:
        os.mkdir('audio_chunks')
    except(FileExistsError):
        pass
    os.chdir('audio_chunks')
    num_chunks = len(audio) // chunk_length_ms + 1
    for i in range(num_chunks):
        start_time = i * chunk_length_ms
        end_time = start_time + chunk_length_ms

        # Extract the chunk
        audio_chunk = audio[start_time:end_time]

        # export audio chunk and save it in the current directory.
        chunk_filename = f"chunk{i}.wav"
        audio_chunk.export(chunk_filename, bitrate='192k', format="wav")

        # Debug: Print information about the chunk
        print(f"Saving chunk{i}.wav: duration {len(audio_chunk)}ms")

        # get the name of the newly created chunk in the AUDIO_FILE variable for later use.
        chunk_file_names.append(chunk_filename)
    return chunk_file_names
def process_chunk(chunk):
    return extract_text_from_speech(chunk)
def extract_text_from_speech(audio_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    transcribed_text = result["text"]
    return transcribed_text

def convert_audio_to_wav(audio_file):
    audio = AudioSegment.from_file(audio_file)
    wav_file = audio_file.split(".")[0] + ".wav"
    audio.export(wav_file, format="wav")
    return wav_file

def extract_text_from_audio(audio_file):
    audio_file = str(audio_file)
    chunks = create_chunks(audio_file)
    num_workers = len(chunks)  # Adjust the number of workers as needed
    text = ""
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}

        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                text += future.result()
            except Exception as exc:
                print(f'Chunk {chunk} generated an exception: {exc}')

    return text

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

def get_soap_notes_prompt(notes_text):
    prompt = (
        f"""Create well-structured and effective SOAP notes with the following rules for the following patient visit. Include complete headings such as Subjective, Objective, Assessment, and Plan."
              Patient visit : \n\n{notes_text}\n\n
              Rules : 
              1. In Subjective section,follow these points : 
                 Document the patient's primary symptoms (e.g., fever, cough, sore throat).
                 Include the duration of symptoms.
                 Note any relevant exposure history, such as contact with sick individuals.
                 Record any other related symptoms (e.g., chills, muscle aches).
                 Mention any treatments the patient has been using (e.g., medications taken).

              2.In Objective section,summarize and cover the following points:
                Vital Signs: Record specific vital signs, such as temperature, respiratory rate, heart rate, and blood pressure.
                Physical Examination:
                   HEENT: Describe findings related to the head, eyes, ears, nose, and throat (e.g., erythema in the throat).
                   Respiratory: Note findings from lung examination (e.g., clear to auscultation bilaterally).
                   Cardiovascular: Document heart rate, rhythm, and any abnormal sounds (e.g., S1 and S2 normal).
                   Musculoskeletal: Include findings if relevant.
                   Neurological: Include findings if relevant.
                   Dermatological: Include findings if relevant.
                   Gastrointestinal: Include findings if relevant.
                   Diagnostic Tests and Labs: Note any relevant test results (e.g., N/A if no tests were done).

              3.In Assessment section,follow these points : 
                Assessment:
                      Identify the condition or diagnosis based on the subjective and objective data (e.g., Acute pharyngitis).
                      Note specific findings that support the diagnosis (e.g., erythema in the throat).

              4. In Plan section,follow these points :
                    Recommend any medications (e.g., continue taking Tylenol as needed).
                    Encourage adequate hydration and rest.
                    Advise on monitoring symptoms and provide guidance on follow-up if symptoms worsen or do not improve within a specified timeframe (e.g., 5-7 days).

              You can use this soap notes as example.The response format should be like that: 

              Subjective:

              The patient, John, presents with a chief complaint of fever, cough, and sore throat. He reports that these symptoms began two days ago. He denies being around anyone sick recently but mentions that he has been going to work. In addition to his primary symptoms, John also experiences chills and muscle itches. He states that his temperature at home reached 102 degrees Fahrenheit. He denies any shortness of breath or wheezing. John has been taking Tylenol a couple of times per day to manage his symptoms.

              Objective:

               - Vital Signs
                   - Temperature: 102 degrees Fahrenheit
                   - Respiratory rate, heart rate, blood pressure: N/A

               - Physical Examination
                  - HEENT: Erythema in the back of the throat
                  - Respiratory: Lungs clear to auscultation bilaterally
                  - Cardiovascular: Heart rate and rhythm regular, S1 and S2 normal
                  - Musculoskeletal: N/A
                  - Neurological: N/A
                  - Dermatological: N/A
                  - Gastrointestinal: N/A

               - Diagnostic Test Results and Labs
                  - N/A

              Assessment & Plan:

                 1. Acute pharyngitis:
                  - Erythema noted in the back of the throat
                 Plan:
                    - Continue taking Tylenol as needed for fever and pain relief
                    - Encourage adequate hydration and rest
                    - Monitor symptoms and return for follow-up if symptoms worsen or do not improve within 5-7 days

                 2. Fever:
                  - Patient reports a temperature of 102 degrees at home
                 Plan:
                  - Continue taking Tylenol as needed for fever and pain relief
                  - Encourage adequate hydration and rest
                  - Monitor temperature and return for follow-up if fever persists or worsens              

              """
    )
    return prompt
def get_medical_summary_prompt(notes_text):
    prompt = f"Summarize the following meeting notes according to medical and health :\n\n{notes_text}\n\nSummary:"
    return prompt

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

        st.sidebar.title("Real-Time Transcription")
        transcription = st.sidebar.checkbox("Enable Transcription")

        transcribed_text = ""
        if transcription:
            transcribed_text = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')

        if st.button("Summarize") and selected_file:
            with st.spinner('Processing...'):
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
                summary_prompt = get_medical_summary_prompt(notes_text)
                soap_notes_prompt = get_soap_notes_prompt(notes_text)
                summary = query_openai(summary_prompt)
                soap_notes = query_openai(soap_notes_prompt)
                # Tabs for Transcription and Summary
                tab1, tab2, tab3 = st.tabs(["Extracted Text", "Summary","Soap Notes"])

                with tab1:
                    st.write(notes_text)

                with tab2:
                    if summary:
                        st.write(summary)
                    else:
                        st.write("Could not generate summary for this file.")
                with tab3:
                    st.write(soap_notes)
        elif transcribed_text is not None and len(transcribed_text) > 0:
            summary_prompt = get_medical_summary_prompt(transcribed_text)
            soap_notes_prompt = get_soap_notes_prompt(transcribed_text)
            summary = query_openai(summary_prompt)
            soap_notes = query_openai(soap_notes_prompt)
            # Tabs for Transcription and Summary
            tab1, tab2, tab3 = st.tabs(["Extracted Text", "Summary", "Soap Notes"])

            with tab1:
                st.write(transcribed_text)

            with tab2:
                if summary:
                    st.write(summary)
                else:
                    st.write("Could not generate summary for this file.")
            with tab3:
                st.write(soap_notes)


    except Exception as e:
        st.error(f"An error occurred: {e}")



run_summarizer_app()