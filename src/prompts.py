dummy_conversation_answer = """Subjective:

The patient, "patient_name" , reports are ambiguous. No specific chief complaint, history of present illness, or relevant information about their symptoms, feelings, and experiences were mentioned in the provided transcript.

Objective:

- Vital Signs
  - N/A

- Physical Examination
  - N/A

- Diagnostic Test Results and Labs
  - N/A

Assessment & Plan:

1. Inadequate information for diagnosis
- Plan: Schedule a follow-up appointment to obtain a detailed history, perform a physical examination, and discuss any specific concerns or symptoms the patient may have. Encourage the patient to provide more information about their health status during the next visit."""
def get_soap_notes_prompt(notes_text):
    prompt = (
        f"""
        Completely analyze the text first and check does there is conversation between doctor and patient regarding any health isssue.If there no such text regarding medical and health issue or some useless text,then simply answer in that format : {dummy_conversation_answer}
        Otherwise, Create well-structured and effective SOAP notes with the following rules for the following patient visit. Include complete headings such as Subjective, Objective, Assessment, and Plan."
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

              3.In Assessment & Plan section,follow these points : 
                 Assessment:
                      Identify the condition or diagnosis based on the subjective and objective data (e.g., Acute pharyngitis).
                      Note specific findings that support the diagnosis (e.g., erythema in the throat).

                 Plan :
                    Recommend any medications (e.g., continue taking Tylenol as needed).
                    Encourage adequate hydration and rest.
                    Advise on monitoring symptoms and provide guidance on follow-up if symptoms worsen or do not improve within a specified timeframe (e.g., 5-7 days).
                 
                 For each assessment,there is at least one plan
                
              4. Add patient_name if exist against that field and show it before Subjective on top of response like that : patient_name : "patient_name"
              
              Add the dates and medicines name that are mentioned by doctor or patient also.
              You can use this soap notes as example.The response format should be like that: 
              

              Subjective:

              The patient, "patient_name", presents with a chief complaint of fever, cough, and sore throat. He reports that these symptoms began two days ago. He denies being around anyone sick recently but mentions that he has been going to work. In addition to his primary symptoms, John also experiences chills and muscle itches. He states that his temperature at home reached 102 degrees Fahrenheit. He denies any shortness of breath or wheezing. John has been taking Tylenol a couple of times per day to manage his symptoms.

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
    prompt = f"Summarize the following meeting notes only according to medical and health issue if its discussed otherwise simply show 'No medical and health related information! ':\n\n{notes_text}\n\nSummary:"
    return prompt

def get_requirements_prompt(notes_text):
    prompt = f"Summarize the requirements from the following notes that is discusssed and desired by client! ':\n\n{notes_text}\n\nSummary:"
    return prompt
def get_ketpoints_prompt(notes_text):
    prompt = f"This is the transcription from a project meeting so can you take out the main points from this?! ':\n\n{notes_text}\n\nSummary:"
    return prompt