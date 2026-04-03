import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación PRO", layout="wide")
st.title("💰 Facturación Clínica PRO")

# ---------------- AÑO ----------------
current_year = datetime.now().year
years = list(range(2024, current_year + 3))
year = st.selectbox("📅 Año", years, index=years.index(current_year))

# ---------------- CONEXIÓN GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["gcp_service_account"]),
    scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).worksheet("Hoja 1")

# ---------------- ASEGURAR CABECERA ----------------
headers = ["Año", "Mes", "FG", "LG", "FPSI", "LPSI", "FPSI_V", "LPSI_V", "TOTAL"]

first_row = sheet.row_values(1)
if first_row != headers:
    sheet.clear()
    sheet.append_row(headers)

# ---------------- CARGAR DATOS ----------------
try:
    data_sheet = sheet.get_all_records()
except Exception:
    data_sheet = []

datos_por_mes = {}
for row in data_sheet:
    if str(row.get("Año")) == str(year):
        datos_por_mes[row["Mes"]] = row

meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# ---------------- HELPERS ----------------
def parse_euro(value: str) -> float:
    s = str(value).strip()
    if not s:
        return 0.0

    s = s.replace(" ", "")

    # Si hay coma, interpretamos formato español
    if "," in s:
        s = s.replace(".", "")
        s = s.replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0


def display_euro(value) -> str:
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except Exception:
        return "0,00"


def init_text_state(key: str, value) -> None:
    if key not in st.session_state:
        st.session_state[key] = display_euro(value)


def money_text_input(label: str, key: str, default_value):
    init_text_state(key, default_value)
    return st.text_input(label, key=key)


# ---------------- INICIALIZAR ESTADO AL CAMBIAR DE AÑO ----------------
year_marker = f"_loaded_year_{year}"
if year_marker not in st.session_state:
    for mes in meses:
        st.session_state[f"{year}_{mes}_fg"] = display_euro(datos_por_mes.get(mes, {}).get("FG", 0))
        st.session_state[f"{year}_{mes}_lg"] = display_euro(datos_por_mes.get(mes, {}).get("LG", 0))
        st.session_state[f"{year}_{mes}_fpsi"] = display_euro(datos_por_mes.get(mes, {}).get("FPSI", 0))
        st.session_state[f"{year}_{mes}_lpsi"] = display_euro(datos_por_mes.get(mes, {}).get("LPSI", 0))
        st.session_state[f"{year}_{mes}_fpsi_v"] = display_euro(datos_por_mes.get(mes, {}).get("FPSI_V", 0))
        st.session_state[f"{year}_{mes}_lpsi_v"] = display_euro(datos_por_mes.get(mes, {}).get("LPSI_V", 0))
    st.session_state[year_marker] = True

# ---------------- FORM PRINCIPAL ----------------
total_ingresos = 0.0
total_retenido = 0.0
netos = []
datos_guardar = []

with st.form("facturacion_form"):
    for mes in meses:
        st.header(f"📅 {mes}")
        col1, col2 = st.columns(2)

        with col1:
            fg_txt = money_text_input("Fact General €", f"{year}_{mes}_fg", datos_por_mes.get(mes, {}).get("FG", 0))
            lg_txt = money_text_input("Lab General €", f"{year}_{mes}_lg", datos_por_mes.get(mes, {}).get("LG", 0))
            fpsi_txt = money_text_input("Fact PSI €", f"{year}_{mes}_fpsi", datos_por_mes.get(mes, {}).get("FPSI", 0))
            lpsi_txt = money_text_input("Lab PSI €", f"{year}_{mes}_lpsi", datos_por_mes.get(mes, {}).get("LPSI", 0))

        with col2:
            fpsi_v_txt = money_text_input("Fact PSI V €", f"{year}_{mes}_fpsi_v", datos_por_mes.get(mes, {}).get("FPSI_V", 0))
            lpsi_v_txt = money_text_input("Lab PSI V €", f"{year}_{mes}_lpsi_v", datos_por_mes.get(mes, {}).get("LPSI_V", 0))

        fg = parse_euro(fg_txt)
        lg = parse_euro(lg_txt)
        fpsi = parse_euro(fpsi_txt)
        lpsi = parse_euro(lpsi_txt)
        fpsi_v = parse_euro(fpsi_v_txt)
        lpsi_v = parse_euro(lpsi_v_txt)

        # Fórmulas actuales; luego ajustamos contratos
        fijo = 800
        variable = max(0, (fg - 1404.33 - lg) * 0.35 + (fpsi - 1428.33 - lpsi) * 0.30)
        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

        var_val = max((fpsi_v - lpsi_v - 3730), 0) * 0.30
        bruto_val = var_val + 741
        neto_val = bruto_val * 0.70

        total_mes = round(neto_col + neto_val, 2)
        st.success(f"💰 TOTAL: {display_euro(total_mes)} €")

        total_ingresos += bruto_col + bruto_val
        total_retenido += (bruto_col + bruto_val) * 0.30
        netos.append(total_mes)

        datos_guardar.append([
            str(year),
            mes,
            round(fg, 2),
            round(lg, 2),
            round(fpsi, 2),
            round(lpsi, 2),
            round(fpsi_v, 2),
            round(lpsi_v, 2),
            round(total_mes, 2)
        ])

    guardar = st.form_submit_button("💾 Guardar")

# ---------------- GUARDAR ----------------
if guardar:
    data_sheet = sheet.get_all_records()

    for fila in datos_guardar:
        año = fila[0]
        mes = fila[1]
        fila_encontrada = None

        for i, row in enumerate(data_sheet):
            if str(row.get("Año")) == año and row.get("Mes") == mes:
                fila_encontrada = i + 2
                break

        if fila_encontrada:
            sheet.update(f"A{fila_encontrada}:I{fila_encontrada}", [fila])
        else:
            sheet.append_row(fila)

    st.success("Guardado correcto 🔥")

# ---------------- RESUMEN ----------------
st.header("📊 Hacienda")
st.metric("Ingresos", round(total_ingresos, 2))
st.metric("Retenido", round(total_retenido, 2))

# ---------------- GRÁFICA ----------------
df = pd.DataFrame({
    "Mes": meses,
    "Cobro": netos
})
st.line_chart(df.set_index("Mes"))
