import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("TEST GUARDADO")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).sheet1

if st.button("Guardar TEST"):
    sheet.append_row(["TEST", "FUNCIONA"])
    st.success("He guardado algo 🔥")
