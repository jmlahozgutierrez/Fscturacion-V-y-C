import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide")

st.title("🧪 TEST Google Sheets")

# ─────────────────────────────────────────
# CONEXIÓN
# ─────────────────────────────────────────
@st.cache_resource
def test_connection():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )

    client = gspread.authorize(creds)

    spreadsheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
    )

    return spreadsheet

# ─────────────────────────────────────────
# EJECUCIÓN
# ─────────────────────────────────────────
try:
    spreadsheet = test_connection()

    st.success("✅ Conectado correctamente")

    # Ver hojas disponibles
    hojas = [ws.title for ws in spreadsheet.worksheets()]
    st.write("📄 Hojas detectadas:", hojas)

    # Seleccionar hoja
    hoja = st.selectbox("Selecciona hoja", hojas)

    sheet = spreadsheet.worksheet(hoja)

    # Mostrar datos RAW
    data = sheet.get_all_records()
    st.write("📊 DATA (get_all_records):", data)

    # Mostrar valores crudos
    raw = sheet.get_all_values()
    st.write("📋 RAW (get_all_values):", raw)

    st.write(f"🔢 Nº filas detectadas: {len(data)}")

except Exception as e:
    st.error("❌ Error de conexión")
    st.write(e)
