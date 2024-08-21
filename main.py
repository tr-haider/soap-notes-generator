import time
import streamlit as st
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from src.auth import google
from pvrecorder import PvRecorder
from src import prompts
from src.database.crud import create_user,get_user_by_email,create_notes,create_patients,get_notes_of_user
from src.database.connection import connect_to_db
import base64
from src.files.bucket import upload_file_to_s3,read_file_from_url,upload_recording_to_s3
from src.transcriptions.transcribe import transcribe
connection, cursor = connect_to_db()

recorder = PvRecorder(device_index=-1, frame_length=512)
# Load environment variables
load_dotenv()
# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
google_icon_path = os.path.abspath("assets/icons8-google-48.png")
# Function to save uploaded file
def uploaded_file_info(uploaded_file):
    content = uploaded_file.read()
    file_info =  {
            "name": uploaded_file.name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size": len(uploaded_file.read()),
            "content": content
    }
    return file_info
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
            st.error("You have exceeded the rate limit for GPT-3.5 Turbo. Please try again later.")
        elif "context length" in error_message.lower():
            st.error(
                "Please reduce the length of your input. As a guideline, try to limit your input to approximately 8,000 words or about 16 pages of text. If possible, summarize the content yourself before submitting it for processing.")
        else:
            st.error(f"An error occurred with OpenAI: {e}")
        return None

# Function to get patient name
def get_patient_name(text):
    start = text.find("The patient,")
    if start != -1:
        start += len("The patient,")
        end = text.find(",", start)
        if end != -1:
            name = text[start:end].strip()
            return name
    return None


def load_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


@st.cache(show_spinner=False)
def fetch_user_info(auth_code):
    token = google.get_token_from_code(auth_code)
    user_info = google.verify_id_token(token)
    return user_info
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
                .login-button img {
                    height: 24px;
                    width: 24px;
                    margin-right: 8px;
                  
                }
                #MainMenu {visibility: hidden;}
            </style>
            """,
            unsafe_allow_html=True
        )
        # Load the Google icon image
        google_icon_base64 = load_image(google_icon_path)
        if 'existing_file' not in st.session_state:
            st.session_state.existing_file = None

        if 'patient_name' not in st.session_state:
            st.session_state.patient_name = {}
        # Handle user session
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'patient_info' not in st.session_state:
            st.session_state.patient_info = None

        if 'reload' not in st.session_state:
            st.session_state.reload = False

        if 'user_found' not in st.session_state:
            st.session_state.user_ref = None

        # Real time transcription
        if 'start' not in st.session_state:
             st.session_state.start = True
        if 'stop' not in st.session_state:
             st.session_state.stop = True
        if 'pause' not in st.session_state:
             st.session_state.pause = True
        if 'resume' not in st.session_state:
             st.session_state.resume = True
        if 'audio' not in st.session_state:
             st.session_state.audio = []
        if 'recorded_audio_file' not in st.session_state:
             st.session_state.recorded_audio_file = None

        # Caching created summaries and SOAP notes
        if 'summaries' not in st.session_state:
                 st.session_state.summaries = {}
        if 'soap_notes' not in st.session_state:
                 st.session_state.soap_notes = {}
        if 'extracted_text' not in st.session_state:
                 st.session_state.extracted_text = {}
        if st.session_state.user_info:
            if st.sidebar.button("Logout"):
                st.session_state.user_info = None
                st.session_state.user_ref = None
                st.experimental_set_query_params()
                with st.spinner('Logging out....'):
                     time.sleep(3)
                     st.rerun()

        # s3 upload states
        if 'uploaded_file_name' not in st.session_state:
             st.session_state.uploaded_file_name = []
        if 'file_url' not in st.session_state:
             st.session_state.file_url = None

        if 'user_notes' not in st.session_state:
            st.session_state.user_notes = None
        if 'radio_options' not in st.session_state:
            st.session_state.radio_options = ["Upload files", "Real-time transcription"]
        if 'previous_meeting_option_added' not in st.session_state:
            st.session_state.previous_meeting_option_added = True
        if not st.session_state.user_info:
           pass
        elif st.session_state.previous_meeting_option_added:
            st.session_state.radio_options.append("Previous meetings")
            st.session_state.previous_meeting_option_added = False
        genre = st.sidebar.radio(
            "Please select : ",
            st.session_state.radio_options,
        )

        col1, col2 = st.columns([50, 1])

        with col1:
            st.title("Soap Notes Generator")
        with col2:
             if not st.session_state.user_info:
                auth_code = st.experimental_get_query_params().get('code')
                if auth_code:
                    auth_code = auth_code[0]
                    user_info = fetch_user_info(auth_code)
                    if user_info:
                        st.session_state.user_info = user_info
                        st.session_state.reload = False
                        st.experimental_set_query_params()
                        st.rerun()
                    else:
                        st.write("Failed to authenticate.")
                else:
                    auth_url = google.get_authorization_url()
                    login_button_css = f"""
                    <style>
                        .login-button {{
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background-color: white;
                            color: black;
                            border: none;
                            border-radius: 5px;
                            padding: 5px 20px;
                            width: 180px;
                            text-align: center;
                            text-decoration: none;
                            font-size: 16px;s
                            font-weight: bold;
                            margin-bottom: 10px;
                      }}
                      
                    </style>
                    <a href="{auth_url}" class="login-button"> <img src="data:image/png;base64,{google_icon_base64}" alt="Google icon">
                        Sign in with Google</a>
                    """

                    st.markdown(login_button_css, unsafe_allow_html=True)
             else:
                 pass

        # Sidebar for uploading multiple files
        if genre == "Upload files":
           if st.session_state.user_info:
                name = st.session_state.user_info['name']
                email = st.session_state.user_info['email']
                user = get_user_by_email(email,  cursor)
                if not user:
                    st.session_state.user_ref = create_user(name, email, connection, cursor)
                else:
                    st.session_state.user_ref = user
                    # Get saved record of user
                if st.session_state.user_info:
                        st.session_state.user_notes = get_notes_of_user(st.session_state.user_ref['id'], cursor)

           st.sidebar.title("Upload Meeting Notes")
           uploaded_files = st.sidebar.file_uploader("Upload files",
                                                  type=["txt", "xlsx", "pdf", "mp3", "wav", "mp4", "mkv", "avi"],
                                                  accept_multiple_files=True)
           files_info = []

           for uploaded_file in uploaded_files:
               file_info = uploaded_file_info(uploaded_file)
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
              st.session_state.clicked = True
              if  selected_file['name'] not in st.session_state.uploaded_file_name:
                  format = selected_file['name'].split('.')[-1]
              folder = ""
              if format == "txt" or format == "pdf" or format == "xlsx":
                folder += "text"
              elif format == "mp3" or format == "wav":
                folder += "audio"
              else:
                folder += "video"
              st.session_state.existing_file = selected_file['name']
              if st.session_state.existing_file not in st.session_state.extracted_text:
                if st.button("Summarize") and selected_file:
                 with st.spinner('Processing...'):
                    file_content = selected_file["content"]
                    file_extension = selected_file["name"].split('.')[-1]
                    file_name = selected_file['name']
                    if file_extension in ["txt", "xlsx", "pdf"]:
                        file_url = upload_file_to_s3(file_content,file_name, folder)
                        notes_text = read_file_from_url(file_url, file_extension)
                        st.session_state.file_url = file_url


                    elif file_extension in ["mp3", "wav"]:
                        job_name, format = f"{selected_file['name'].split('.')[0]}-{datetime.now().strftime('%d%m%Y%H%M%S')}-audio-job", \
                            selected_file['name'].split('.')[-1]
                        file_url = upload_file_to_s3(file_content,file_name, folder)
                        notes_text = transcribe(file_url, job_name, format)
                        st.session_state.file_url = file_url


                    elif file_extension in ["mp4", "mkv", "avi"]:
                        job_name, format = f"{selected_file['name'].split('.')[0]}-{datetime.now().strftime('%d%m%Y%H%M%S')}-video-job", \
                        selected_file['name'].split('.')[-1]
                        file_url = upload_file_to_s3(file_content,file_name, folder)
                        notes_text = transcribe(file_url, job_name, format)
                        st.session_state.file_url = file_url

                    else:
                        st.error("Unsupported file type")
                        return

                 with st.spinner('Summarizing...'):
                    summary_prompt = prompts.get_medical_summary_prompt(notes_text)
                    soap_notes_prompt = prompts.get_soap_notes_prompt(notes_text)
                    summary = query_openai(summary_prompt)
                    soap_notes = query_openai(soap_notes_prompt)
                    patient_name = get_patient_name(soap_notes)

                    if st.session_state.user_ref:
                        st.session_state.patient_info = create_patients(patient_name, connection, cursor)
                        create_notes(notes_text, summary, soap_notes, st.session_state.file_url,
                                     st.session_state.user_ref['id'], st.session_state.patient_info['id'], connection,
                                     cursor)

                    # Tabs for Transcription and Summary
                    tab1, tab2, tab3 = st.tabs(["Extracted Text", "Summary", "Soap Notes"])
                    st.session_state.extracted_text[st.session_state.existing_file] = notes_text
                    st.session_state.summaries[st.session_state.existing_file] = summary
                    st.session_state.soap_notes[st.session_state.existing_file] = soap_notes

                    with tab1:
                        st.write(notes_text)
                    with tab2:
                        if summary:
                            st.write(summary)
                        else:
                            st.write("Could not generate summary for this file.")
                    with tab3:
                        st.write(soap_notes)
                 st.session_state.clicked = False
              else:

                 tab1, tab2, tab3 = st.tabs(["Extracted Text", "Summary", "Soap Notes"])

                 with tab1:
                        st.write(st.session_state.extracted_text[st.session_state.existing_file])
                 with tab2:
                        if st.session_state.summaries[st.session_state.existing_file]:
                           st.write(st.session_state.summaries[st.session_state.existing_file])
                        else:
                           st.write("Could not generate summary for this file.")
                 with tab3:
                        st.write(st.session_state.soap_notes[st.session_state.existing_file])


        if genre == "Real-time transcription":
           st.sidebar.title("Real-Time Transcription")
           transcription = st.sidebar.checkbox("Enable Transcription")
           transcribed_text = ""
           if st.session_state.user_info :
            name = st.session_state.user_info['name']
            email = st.session_state.user_info['email']
            user = get_user_by_email(email,cursor)
            if not user:
               st.session_state.user_ref = create_user(name, email, connection, cursor)
            else:
                st.session_state. user_ref = user

           if transcription:
               if st.sidebar.button('Start 🔴'):
                  recorder.start()
                  while True:
                    frame = recorder.read()
                    st.session_state.audio.extend(frame)
               if st.sidebar.button('Pause ⏸'):
                 recorder.stop()
               if st.sidebar.button('Resume ⏯'):
                  recorder.start()
                  while True:
                    frame = recorder.read()
                    st.session_state.audio.extend(frame)
               if st.sidebar.button('Stop ⏹'):
                   recorder.stop()
                   if st.session_state.audio:
                       file_name = f"recording_{datetime.now().strftime('%d%m%Y%H%M%S')}.wav"
                       with st.spinner('Processing...'):
                           file_url = upload_recording_to_s3(st.session_state.audio, "recordings", file_name)
                           if file_url:
                               transcribed_text += transcribe(file_url, file_name.split('.')[0], 'wav')
                               st.session_state.file_url = file_url
                           else:
                               st.error('File upload failed.')
                   with st.spinner('Summarizing...'):
                        transcribed_text = transcribed_text  # extract_text_from_audio(st.session_state.recorded_audio_file)
                        summary_prompt = prompts.get_medical_summary_prompt(transcribed_text)
                        soap_notes_prompt = prompts.get_soap_notes_prompt(transcribed_text)
                        summary = query_openai(summary_prompt)
                        soap_notes = query_openai(soap_notes_prompt)
                        patient_name = get_patient_name(soap_notes)
                        if st.session_state.user_ref:
                            st.session_state.patient_info = create_patients(patient_name, connection, cursor)
                            create_notes(transcribed_text, summary, soap_notes, st.session_state.file_url,
                                         st.session_state.user_ref['id'], st.session_state.patient_info['id'],
                                         connection,
                                         cursor)
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
                   st.session_state.recorded_audio_file = None
                   st.session_state.audio = []
        if genre == "Previous meetings":
            if st.session_state.user_notes:
                user_notes_id_name = {}
                for note in st.session_state.user_notes:
                    if note['name'] is not None:
                        user_notes_id_name[note['id']] = {
                            'patient_name': note['name'],
                            'extracted_text': note['extracted_text'],
                            'summary': note['summary'],
                            'soap_notes': note['soap_notes']
                        }

                    # Map patient names to their IDs
                patient_names = {id: details['patient_name'] for id, details in user_notes_id_name.items()}

                # Create a list of tuples (ID, Name) for selectbox
                patient_name_options = [(id, name) for id, name in patient_names.items()]

                # Display the selectbox with patient names
                selected_patient_id = st.sidebar.selectbox(
                    'Previous meetings Record',
                    patient_name_options,
                    format_func=lambda x: x[1]  # Show the patient name in the selectbox
                )[0]  # Retrieve the selected ID

                # Use the selected ID to get the corresponding record
                selected_record = user_notes_id_name[selected_patient_id]
                if selected_record:
                    with col1:
                        # Tabs for Transcription and Summary
                        tab1, tab2, tab3 = st.tabs(["Extracted Text", "Summary", "Soap Notes"])
                        with tab1:
                            st.write(selected_record['extracted_text'])

                        with tab2:
                            if selected_record['summary']:
                                st.write(selected_record['summary'])
                            else:
                                st.write("Could not generate summary for this file.")
                        with tab3:
                            st.write(selected_record['soap_notes'])






    except Exception as e:
        st.error(f"An error occurred: {e}")



run_summarizer_app()