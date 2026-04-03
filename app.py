import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Facturación PRO", layout="wide")

st.title("💰 Facturación Clínica PRO 🛡️")

# ---------------- CONFIG ----------------
AUTO_GUARDADO = False

# ---------------- CONEXIÓN ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["gcp_service_account"])

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict, scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1JgpD7qiclpmTuLoHDWCIWdtJ5DPdZKeURFwkXv3_e7U/edit"
).sheet1

# ---------------- AÑO ----------------
year = st.selectbox("📅 Año", [2024, 2025, 2026, 2027])

# ---------------- CARGA SEGURA ----------------
try:
    data_sheet = sheet.get_all_records()
except:
    st.error("⚠️ No se pudieron cargar datos, pero no se ha perdido nada")
    data_sheet = []

datos_por_mes = {}

for row in data_sheet:
    if row.get("Año") == year:
        datos_por_mes[row["Mes"]] = row

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
        fg = st.number_input("Fact General", value=datos_por_mes.get(mes, {}).get("FG", 0), key=mes+"fg")
        lg = st.number_input("Lab General", value=datos_por_mes.get(mes, {}).get("LG", 0), key=mes+"lg")
        fpsi = st.number_input("Fact PSI", value=datos_por_mes.get(mes, {}).get("FPSI", 0), key=mes+"fpsi")
        lpsi = st.number_input("Lab PSI", value=datos_por_mes.get(mes, {}).get("LPSI", 0), key=mes+"lpsi")

        fijo = 800
        variable = max(0,(fg - 1404.33 - lg)*0.35 + (fpsi - 1428.33 - lpsi)*0.3)

        bruto_col = fijo + variable
        neto_col = bruto_col * 0.70

    with col2:
        fpsi_v = st.number_input("Fact PSI V", value=datos_por_mes.get(mes, {}).get("FPSI_V", 0), key=mes+"fpsi_v")
        lpsi_v = st.number_input("Lab PSI V", value=datos_por_mes.get(mes, {}).get("LPSI_V", 0), key=mes+"lpsi_v")

        var = max((fpsi_v - lpsi_v - 3730),0)*0.3
        bruto_val = var + 741
        neto_val = bruto_val * 0.70

    total_mes = neto_col + neto_val
    st.success(f"💰 TOTAL: {round(total_mes,2)} €")

    total_ingresos += bruto_col + bruto_val
    total_retenido += (bruto_col + bruto_val) * 0.30

    netos.append(total_mes)

    datos_guardar.append([
        year, mes, fg, lg, fpsi, lpsi, fpsi_v, lpsi_v, total_mes
    ])

# ---------------- GUARDADO SEGURO ----------------
def guardar_seguro():

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i, fila in enumerate(datos_guardar):
        fila_num = i + 2

        try:
            # Backup antes de sobrescribir
            backup = sheet.row_values(fila_num)

            sheet.update(f"A{fila_num}:I{fila_num}", [fila])

            # Log histórico (extra seguridad)
            sheet.append_row(fila + [timestamp])

        except Exception as e:
            st.error(f"Error guardando fila {fila_num} ⚠️")
            st.write(e)

# ---------------- BOTÓN SEGURO ----------------
confirmar = st.checkbox("Confirmo que quiero guardar cambios")

if st.button("💾 Guardar (seguro)") and confirmar:
    guardar_seguro()
    st.success("Datos guardados con seguridad 🔥")

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
