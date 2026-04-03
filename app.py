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

creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

# 🔥 IMPORTANTE: nombre EXACTO de la pestaña
sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).worksheet("Hoja 1")

# ---------------- CARGAR DATOS ----------------
data_sheet = sheet.get_all_records()

datos_por_mes = {}

for row in data_sheet:
    if str(row.get("Año")) == str(year):
        datos_por_mes[row["Mes"]] = row

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
        fg = st.number_input("Fact General €",
                             value=float(datos_por_mes.get(mes, {}).get("FG", 0)),
                             step=0.01, format="%.2f",
                             key=mes+"fg")

        lg = st.number_input("Lab General €",
                             value=float(datos_por_mes.get(mes, {}).get("LG", 0)),
                             step=0.01, format="%.2f",
                             key=mes+"lg")

        fpsi = st.number_input("Fact PSI €",
                               value=float(datos_por_mes.get(mes, {}).get("FPSI", 0)),
                               step=0.01, format="%.2f",
                               key=mes+"fpsi")

        lpsi = st.number_input("Lab PSI €",
                               value=float(datos_por_mes.get(mes, {}).get("LPSI", 0)),
                               step=0.01, format="%.2f",
                               key=mes+"lpsi")

        fijo = 800
        variable = max(0,(fg - 1404.33 - lg)*0.35 + (fpsi - 1428.33 - lpsi)*0.3)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

    with col2:
        fpsi_v = st.number_input("Fact PSI V €",
                                 value=float(datos_por_mes.get(mes, {}).get("FPSI_V", 0)),
                                 step=0.01, format="%.2f",
                                 key=mes+"fpsi_v")

        lpsi_v = st.number_input("Lab PSI V €",
                                 value=float(datos_por_mes.get(mes, {}).get("LPSI_V", 0)),
                                 step=0.01, format="%.2f",
                                 key=mes+"lpsi_v")

        var = max((fpsi_v - lpsi_v - 3730),0)*0.3
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

    total_mes = neto_col + neto_val
    st.success(f"💰 TOTAL: {round(total_mes,2)} €")

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30

    netos.append(total_mes)

    datos_guardar.append([
        str(year), mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes
    ])

# ---------------- GUARDAR ----------------
if st.button("💾 Guardar"):

    data_sheet = sheet.get_all_records()

    for fila in datos_guardar:

        año = str(fila[0])
        mes = fila[1]

        fila_encontrada = None

        for i, row in enumerate(data_sheet):
            if str(row.get("Año")) == año and row.get("Mes") == mes:
                fila_encontrada = i + 2
                break

        try:
            if fila_encontrada:
                sheet.update(f"A{fila_encontrada}:I{fila_encontrada}", [fila])
            else:
                sheet.append_row(fila)

        except Exception as e:
            st.error(f"Error en {mes}")
            st.write(e)

    st.success("Guardado correcto 🔥")

# ---------------- IRPF ----------------
def calcular_irpf(base):
    impuesto = 0
    tramos = [(12450,0.19),(20200,0.24),(35200,0.30),(60000,0.37),(300000,0.45)]
    anterior = 0

    for limite, tipo in tramos:
        if base > limite:
            impuesto += (limite - anterior) * tipo
            anterior = limite
        else:
            impuesto += (base - anterior) * tipo
            return impuesto

    impuesto += (base - anterior) * 0.47
    return impuesto

irpf_real = calcular_irpf(total_ingresos)

st.header("📊 Hacienda")

st.metric("Ingresos", round(total_ingresos,2))
st.metric("Retenido", round(total_retenido,2))
st.metric("IRPF", round(irpf_real,2))

# ---------------- GRÁFICA ----------------
df = pd.DataFrame({
    "Mes": meses,
    "Cobro": netos
})

st.line_chart(df.set_index("Mes"))
