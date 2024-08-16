import mysql.connector
from src.configs import env
import streamlit as st
def connect_to_db():
    try :
        # Creating connection
        connection = mysql.connector.connect(
        host=env.DB_HOST,
        user=env.DB_USER,
        password=env.DB_PASSWORD,
        database=env.DB_NAME
        )
        # Create a cursor object
        cursor = connection.cursor()
        return connection, cursor
    except mysql.connector.Error as e:
        st.error(f"Error while creating connection to database : {e}")





