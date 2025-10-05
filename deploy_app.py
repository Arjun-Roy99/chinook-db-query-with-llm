from dotenv import load_dotenv
load_dotenv() #Load the env variables

import streamlit as st
import os
import sqlite3
import re
import pandas as pd
from google import genai

#Config our client connection using the GOOGLE API KEY from Streamlit secrets
client = genai.Client(api_key = st.secrets["GOOGLE_API_KEY"])

#Function to load Google Gemini Model and provide SQL query as response

def get_gemini_response(question, behavior_prompt):
    response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = [behavior_prompt[0], question]
    )
    return response.text

#Function to execute LLM query on SQL database

def read_sql_query(sql,db):
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    connection.commit()
    connection.close()

    return pd.DataFrame(rows, columns = columns)

#Function to identify if response is an SQL Query
def is_sql_query(text: str) -> bool:
    """
    Checks if a given string appears to be an SQL query.
    Returns True if yes, False otherwise.
    """
    if not text or not isinstance(text, str):
        return False

    # Common SQL command keywords
    sql_keywords = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER",
        "REPLACE", "TRUNCATE", "WITH", "GRANT", "REVOKE"
    ]

    # Check if any SQL keyword appears at the start (ignoring whitespace/comments)
    cleaned = text.strip().upper()

    # Basic pattern: start with a SQL keyword and contain at least one space
    pattern = r"^\s*(" + "|".join(sql_keywords) + r")\b"

    return bool(re.match(pattern, cleaned))

## Define Your Prompt - Generally longer and detailed prompts will give better results

behavior_prompt = [
    """
    You are an expert assistant that helps users query the Chinook music store database using SQL.

    The Chinook database has the following main tables and columns:
    1. The SQL table ARTIST and has the following columns with the datatypes ArtistId INTEGER, Name NVARCHAR(120).
    2. The SQL table ALBUM and has the following columns with the datatypes AlbumId INTEGER, Title NVARCHAR(160), ArtistId INTEGER.
    3. The SQL table TRACK and has the following columns with the datatypes TrackId INTEGER, Name NVARCHAR(200), AlbumId INTEGER, MediaTypeId INTEGER, GenreId INTEGER, Composer NVARCHAR(220), Milliseconds INTEGER, Bytes INTEGER, UnitPrice NUMERIC(10,2).
    4. The SQL table GENRE and has the following columns with the datatypes GenreId INTEGER, Name NVARCHAR(120).
    5. The SQL table MEDIATYPE and has the following columns with the datatypes MediaTypeId INTEGER, Name NVARCHAR(120).
    6. The SQL table PLAYLIST and has the following columns with the datatypes PlaylistId INTEGER, Name NVARCHAR(120).
    7. The SQL table PLAYLISTTRACK and has the following columns with the datatypes PlaylistId INTEGER, TrackId INTEGER.
    8. The SQL table CUSTOMER and has the following columns with the datatypes CustomerId INTEGER, FirstName NVARCHAR(40), LastName NVARCHAR(20), Company NVARCHAR(80), Address NVARCHAR(70), City NVARCHAR(40), State NVARCHAR(40), Country NVARCHAR(40), PostalCode NVARCHAR(10), Phone NVARCHAR(24), Fax NVARCHAR(24), Email NVARCHAR(60), SupportRepId INTEGER.
    9. The SQL table EMPLOYEE and has the following columns with the datatypes EmployeeId INTEGER, LastName NVARCHAR(20), FirstName NVARCHAR(20), Title NVARCHAR(30), ReportsTo INTEGER, BirthDate DATETIME, HireDate DATETIME, Address NVARCHAR(70), City NVARCHAR(40), State NVARCHAR(40), Country NVARCHAR(40), PostalCode NVARCHAR(10), Phone NVARCHAR(24), Fax NVARCHAR(24), Email NVARCHAR(60).
    10. The SQL table INVOICE and has the following columns with the datatypes InvoiceId INTEGER, CustomerId INTEGER, InvoiceDate DATETIME, BillingAddress NVARCHAR(70), BillingCity NVARCHAR(40), BillingState NVARCHAR(40), BillingCountry NVARCHAR(40), BillingPostalCode NVARCHAR(10), Total NUMERIC(10,2).
    11. The SQL table INVOICELINE and has the following columns with the datatypes InvoiceLineId INTEGER, InvoiceId INTEGER, TrackId INTEGER, UnitPrice NUMERIC(10,2), Quantity INTEGER.

    Rules:
    - If the user asks factual questions about the database schema or contents, explain them briefly (under 700 words).
    - If the user asks a question that requires data retrieval, return only the SQL query — no explanations, no formatting, and no markdown (no ``` or “SQL”).
    - If the user asks questions like:
        * "Who made you?"
        * "What project is this?"
        * "What are you for?"
        * "Tell me about yourself."
      then respond in natural language as:
        "I am a demo Streamlit app built by Arjun Roy to showcase how Google Gemini can translate natural language into SQL queries for the Chinook music database."
    - Never generate SQL for such meta-questions.
    """
]


#Creating a Streamlit App

st.set_page_config(page_title = "🎵 Chinook Database Explorer")
st.header("Gemini App to Query Chinook Database")

# Streamlit sidebar info card
with st.sidebar:
    st.title("🎵 Chinook LLM Query App")
    st.markdown("""
    **About this App**

    This demo Streamlit app lets users query the **Chinook Music Database** in plain English.  
    It uses **Google Gemini** to translate natural language into SQL queries and returns live results from the database.

    **Built by:** Arjun Roy  
    **Purpose:** Showcase project for LLM + SQL integration.  
    **Tech Stack:** Streamlit · Google Gemini · SQLite · Python

    ---
    💡 *Try asking:*
    - "Show me all albums by AC/DC"
    - "Which customers are from Brazil?"
    - "List the top 5 genres by number of tracks"
    """)


question = st.text_input("Enter your question: ", key = "input")
submit = st.button("Ask the question")

#If submit is clicked
if submit and question:
    response = get_gemini_response(question,behavior_prompt)

    if is_sql_query(response):
        st.write("*Generated SQL Query*")
        st.code(response, language = "sql")

        try:
            data = read_sql_query(response,"Chinook_Sqlite.sqlite")
            st.subheader("The Response is:")
            st.dataframe(data)
        except Exception as e:
            st.error(f"Error executing SQL : {e}")
    else:
        st.write(response)