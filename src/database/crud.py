from datetime import datetime
import src.database.queries as queries
import streamlit as st
def create_user(name, email, connection, cursor):
    try:
        data = {
            'name': name,
            'email': email,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }
        insert_query = queries.query_for_create_user('users')
        cursor.execute(insert_query, data)
        connection.commit()
        user_id = cursor.lastrowid
        data['id'] = user_id
        return data
    except Exception as e:
        st.error(f"An error occurred while creating the user: {e}")

def get_user_by_email(email, cursor):
    try:
        find_query = queries.query_for_finding_user_by_email('users')
        cursor.execute(find_query, (email,))
        user = cursor.fetchone()

        if user:
            column_names = cursor.column_names
            user_dict = {column_names[idx]: value for idx, value in enumerate(user)}
            return user_dict
        return None
    except Exception as e:
        st.error(f"An error occurred while fetching the user: {e}")

def create_notes(extracted_text, summary, soap_notes, file_url, user_id, patient_id, connection, cursor):
    try:
        data = {
            'extracted_text': extracted_text,
            'summary': summary,
            'soap_notes': soap_notes,
            'file_path': file_url,
            'user_id': user_id,
            'patient_id': patient_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'deleted_at': None
        }
        insert_query = queries.query_for_create_notes('notes')
        cursor.execute(insert_query, data)
        connection.commit()
        return data
    except Exception as e:
        st.error(f"An error occurred while creating the notes: {e}")


def create_patients(name, connection, cursor):
    try:
        data = {
            'name': name,
            'visited_at': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'deleted_at': None
        }
        insert_query = queries.query_for_create_patients('patients')
        cursor.execute(insert_query, data)
        connection.commit()
        patient_id = cursor.lastrowid
        data['id'] = patient_id
        return data
    except Exception as e:
        st.error(f"An error occurred while creating the patient: {e}")

def get_notes(extracted_text, patient_id, cursor):
    try:
        find_query = queries.query_for_finding_notes('notes')
        cursor.execute(find_query, (patient_id, extracted_text))
        notes = cursor.fetchone()

        if notes:
            return True
        return False
    except Exception as e:
        st.error(f"An error occurred while fetching the notes: {e}")

def get_notes_of_user(user_id, cursor):
    try:
        find_query = queries.query_for_finding_notes_of_user('notes')
        cursor.execute(find_query, (user_id,))
        notes = cursor.fetchall()

        if notes:
            column_names = [desc[0] for desc in cursor.description]
            notes_dict_list = [dict(zip(column_names, note)) for note in notes]
            return notes_dict_list
        return None
    except Exception as e:
        st.error(f"An error occurred while fetching the notes of the user: {e}")

