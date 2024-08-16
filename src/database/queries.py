from datetime import datetime

query_for_get_table_names = "SELECT table_name FROM information_schema.tables WHERE table_schema = %s"
def query_for_create_user(table_name):
    # SQL query for insertion
    return f"INSERT INTO {table_name} (name, email, created_at, updated_at) VALUES ( %(name)s, %(email)s, %(created_at)s, %(updated_at)s )"

def query_for_finding_user_by_email(table_name):
    return f"SELECT * FROM {table_name} WHERE email = %s"

def query_for_create_notes(table_name):
    # SQL query for insertion
    return f"INSERT INTO {table_name} (extracted_text, summary, soap_notes, file_path, user_id, patient_id, created_at, updated_at, deleted_at) VALUES ( %(extracted_text)s, %(summary)s, %(soap_notes)s,%(file_path)s, %(user_id)s , %(patient_id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s )"

def query_for_create_patients(table_name):
    # SQL query for insertion
    return f"INSERT INTO {table_name} (name, visited_at, created_at, updated_at) VALUES ( %(name)s, %(visited_at)s, %(created_at)s, %(updated_at)s )"

def query_for_finding_notes(table_name):

    return f"SELECT * FROM {table_name} WHERE extracted_text = %s"

def query_for_finding_notes_of_user(table_name):
    table_name = f"`{table_name}`"
    return f"""
            SELECT {table_name}.id, extracted_text, summary, soap_notes, file_path,patients.name as name
            FROM {table_name} 
            LEFT JOIN patients ON patients.id = {table_name}.patient_id 
            WHERE {table_name}.user_id = %s
        """