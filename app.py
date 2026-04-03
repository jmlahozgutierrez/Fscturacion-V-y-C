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

# ---------------- CONEXIÓN ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["gcp_service_account"]), scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).worksheet("Hoja 1")

# ---------------- ASEGURAR CABECERA ----------------
headers = ["Año","Mes","FG","LG","FPSI","LPSI","FPSI_V","LPSI_V","TOTAL"]

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

# ---------------- HELPERS ----------------
def parse_euro(value: str) -> float:
    """
    Convierte entradas tipo:
    242,45
    9.053,57
    9053.57
    9053
    a float válido.
    """
    if value is None:
        return 0.0

    s = str(value).strip()
    if s == "":
        return 0.0

    # Quitar espacios
    s = s.replace(" ", "")

    # Si lleva coma, asumimos formato español:
    # quitamos puntos de miles y cambiamos coma por punto decimal
    if "," in s:
        s = s.replace(".", "")
        s = s.replace(",", ".")
    else:
        # Si no lleva coma, dejamos el punto como decimal
        pass

    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0

def format_euro(value) -> str:
    try:
        return f"{float(value):.2f}".replace(".", ",")
    except Exception:
        return "0,00"

def money_input(label: str, default_value: float, key: str) -> float:
    txt = st.text_input(label, value=format_euro(default_value), key=key)
    return parse_euro(txt)

# ---------------- VARIABLES ----------------
meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

total_ingresos = 0
total_retenido = 0
netos = []
datos_guardar = []

# ---------------- LOOP ----------------
for mes in meses:

    st.header(f"📅 {mes}")

    col1, col2 = st.columns(2)

    with col1:
        fg = money_input(
            "Fact General €",
            datos_por_mes.get(mes, {}).get("FG", 0),
            key=f"{year}_{mes}_fg"
        )

        lg = money_input(
            "Lab General €",
            datos_por_mes.get(mes, {}).get("LG", 0),
            key=f"{year}_{mes}_lg"
        )

        fpsi = money_input(
            "Fact PSI €",
            datos_por_mes.get(mes, {}).get("FPSI", 0),
            key=f"{year}_{mes}_fpsi"
        )

        lpsi = money_input(
            "Lab PSI €",
            datos_por_mes.get(mes, {}).get("LPSI", 0),
            key=f"{year}_{mes}_lpsi"
        )

        # OJO: esta fórmula es la que tenías; luego la ajustamos con el contrato bueno
        fijo = 800
        variable = max(0, (fg - 1404.33 - lg) * 0.35 + (fpsi - 1428.33 - lpsi) * 0.30)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

    with col2:
        fpsi_v = money_input(
            "Fact PSI V €",
            datos_por_mes.get(mes, {}).get("FPSI_V", 0),
            key=f"{year}_{mes}_fpsi_v"
        )

        lpsi_v = money_input(
            "Lab PSI V €",
            datos_por_mes.get(mes, {}).get("LPSI_V", 0),
            key=f"{year}_{mes}_lpsi_v"
        )

        # OJO: misma idea, luego afinamos cuando tengas la hoja de variables
        var = max((fpsi_v - lpsi_v - 3730), 0) * 0.30
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

    total_mes = round(neto_col + neto_val, 2)
    st.success(f"💰 TOTAL: {total_mes:.2f} €")

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
        total_mes
    ])

# ---------------- GUARDAR ----------------
if st.button("💾 Guardar"):

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

# ---------------- GRÁFICA ----------------
df = pd.DataFrame({
    "Mes": meses,
    "Cobro": netos
})

st.line_chart(df.set_index("Mes"))
