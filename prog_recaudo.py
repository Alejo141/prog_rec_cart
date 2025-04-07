import streamlit as st
import pandas as pd
from io import BytesIO
import os
import unidecode  # type: ignore

# Configuración inicial de la app
st.set_page_config(page_title="Recaudo y Cartera", page_icon="📊", layout="wide")

# Título principal
st.title("📊 Captura de Datos")

# Menú de selección
opcion = st.sidebar.selectbox("Selecciona una opción:", ["Inicio", "Recaudo", "Cartera"])

# ------------------- FUNCIONES GENERALES -------------------
def generar_xlsx(df1, df2, df3):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, sheet_name='Datos_Cruzados', index=False)
        df2.to_excel(writer, sheet_name='Resumen_Recaudo', startrow= 1, startcol=1, index=False)
        df3.to_excel(writer, sheet_name='Resumen_Recaudo', startrow= 1, startcol=5, index=False)
    output.seek(0)
    return output

def generar_csv(df):
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    return output

# ------------------- SECCIÓN DE FACTURACIÓN -------------------
if opcion == "Recaudo":
    st.subheader("📄 Procesamiento de Recaudo")

    # Columnas para cargar archivos
    col1, col2 = st.columns(2)

    with col1:
        archivo_liquidacion = st.file_uploader("📂 Cargar archivo Excel - Liquidación", type=["xlsx"])
    with col2:
        archivo_ordenes = st.file_uploader("📂 Cargar archivo Excel - Órdenes", type=["xlsx"])

    col3, col4 = st.columns(2)

    with col3:
        archivo_provision = st.file_uploader("📂 Cargar archivo Excel - Provisión", type=["xlsx"])
    with col4:
        archivo_siigo = st.file_uploader("📂 Cargar archivo Excel - Siigo", type=["xlsx"])

    if archivo_liquidacion and archivo_ordenes and archivo_provision:
        # Cargar los datos en DataFrames
        df_liqui = pd.read_excel(archivo_liquidacion)
        df_ordenes = pd.read_excel(archivo_ordenes)
        df_provision = pd.read_excel(archivo_provision)
        df_siigo = pd.read_excel(archivo_siigo)

        # Normalizar nombres de columnas
        df_liqui.columns = df_liqui.columns.str.strip().str.upper()
        df_ordenes.columns = df_ordenes.columns.str.strip().str.upper()
        df_provision.columns = df_provision.columns.str.strip().str.upper()
        df_siigo.columns = df_siigo.columns.str.strip().str.upper()

        columnas_liqui = ["DOCUMENTO", "CÓDIGO PROYECTO", "FECHA", "FORMA DE PAGO", 
                          "CÓDIGO PUNTO DE SERVICIO", "VALOR MOVILIZADO", "VALOR COMISIÓN", 
                          "IVA", "TOTAL LIQUIDACIÓN", "ANO"]
        columnas_ordenes = ["NUMERO_ORDEN", "IDENTIFICACION", "NOMBRES", "APELLIDO1", "APELLIDO2", "FACTURA"]
        columnas_provision = ["NUI", "CC", "PROYECTO"]
        columnas_siigo = ["CÓDIGO CONTABLE", "CUENTA CONTABLE", "COMPROBANTE", "SECUENCIA", "FECHA ELABORACIÓN", 
                          "IDENTIFICACIÓN", "NOMBRE DEL TERCERO", "DESCRIPCIÓN", "CENTRO DE COSTO", "DÉBITO"]

        df_liqui = df_liqui[[col for col in columnas_liqui if col in df_liqui.columns]]
        df_ordenes = df_ordenes[[col for col in columnas_ordenes if col in df_ordenes.columns]]
        df_provision = df_provision[[col for col in columnas_provision if col in df_provision.columns]]
        df_siigo = df_siigo[[col for col in columnas_siigo if col in df_siigo.columns]]

        if all(col in df_ordenes.columns for col in ["NOMBRES", "APELLIDO1", "APELLIDO2"]):
            df_ordenes["NOMBRE_COMPLETO"] = (
                df_ordenes["NOMBRES"].fillna('').apply(lambda x: unidecode.unidecode(x)) + " " +
                df_ordenes["APELLIDO1"].fillna('').apply(lambda x: unidecode.unidecode(x)) + " " +
                df_ordenes["APELLIDO2"].fillna('').apply(lambda x: unidecode.unidecode(x))
            ).str.strip()

        df1, df2, df3, df4 = len(df_liqui), len(df_ordenes), len(df_provision), len(df_siigo)

        #st.dataframe(df_siigo)

        df_siigo[['FACTURA', 'IDENTIFICACION']] = df_siigo['DESCRIPCIÓN'].str.extract(r'^(FV\S*)\s+(\S+)')
        st.dataframe(df_siigo[['FACTURA', 'IDENTIFICACION']])

        st.dataframe(df_siigo)

        if df1 == df2:
            df_merged = df_liqui.merge(df_ordenes, left_on="DOCUMENTO", right_on="NUMERO_ORDEN", how="inner")

            st.success("✅ Datos cruzados correctamente.")
            df_merged = df_merged.drop(columns=["NOMBRES", "APELLIDO1", "APELLIDO2"]).reset_index(drop=True)

            if "IDENTIFICACION" in df_merged.columns and "NUI" in df_provision.columns:
                df_total = df_merged.merge(df_provision, left_on="IDENTIFICACION", right_on="NUI", how="inner")

                st.success("✅ Cruce total correcto.")
                st.dataframe(df_total)

                col1, col2 = st.columns(2)
                with col1:
                    sum_val_movil = df_total.groupby('CC')["VALOR MOVILIZADO"].sum().reset_index()
                    st.dataframe(sum_val_movil)

                with col2:
                    sum_siigo = df_siigo.groupby('CC')["VALOR MOVILIZADO"].sum().reset_index()
                    #st.dataframe(sum_val_movil)

                # Descargar resultado con dos hojas
                xlsx = generar_xlsx(df_total, sum_val_movil, sum_siigo)
                st.download_button(
                    label="📥 Descargar Excel",
                    data=xlsx,
                    file_name="datos_cruzados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("⚠️ No se encontraron las columnas 'IDENTIFICACION' o 'NUI' para realizar el segundo cruce.")
        else:
            st.warning("⚠️ Las bases de datos cargadas no tienen la misma cantidad de registros. Por favor, validar antes de cargar.")


# ------------------- SECCIÓN DE FACTURACIÓN -------------------

# ------------------- SECCIÓN DE CARTERA -------------------
elif opcion == "Cartera":
    st.subheader("💰 Procesamiento de Cartera")

    archivo = st.file_uploader("📂 Cargar archivo Excel", type=["xlsx"])

    if archivo is not None:
        df = pd.read_excel(archivo)

        # Obtener el nombre del archivo
        nombre_archivo = archivo.name  

        # Definir las columnas a filtrar
        columnas_deseadas = ["NUMERO_ORDEN", "IDENTIFICACION", "NOMBRES", "APELLIDO1", "APELLIDO2", "FACTURA"]
        columnas_presentes = [col for col in columnas_deseadas if col in df.columns]

        # Filtrar columnas
        df_filtrado = df[columnas_presentes]

        # Agregar el nombre del archivo como una nueva columna
        #df_filtrado.insert(0, "nombre_archivo", nombre_archivo)

        # Reemplazar valores vacíos o NaN con "NA"
        df_filtrado.fillna("NA", inplace=True)

        # Limpieza de datos
        if "Fecha" in df_filtrado.columns:
            df_filtrado["Fecha"] = pd.to_datetime(df_filtrado["Fecha"], errors='coerce').dt.strftime('%d-%m-%Y').fillna("NA")

        st.success("✅ Archivo procesado correctamente.")
        st.dataframe(df_filtrado)

        # Botones de descarga
        xlsx = generar_xlsx(df_filtrado)
        st.download_button(label="📥 Descargar Excel", data=xlsx, file_name="facturacion_procesada.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        csv = generar_csv(df_filtrado)
        st.download_button(label="📥 Descargar CSV", data=csv, file_name="facturacion_procesada.csv", mime="text/csv")

# ------------------- PANTALLA INICIO -------------------
else:
    st.write("👈 Usa el menú de la izquierda para seleccionar una opción.")
    st.markdown("""
        ### 📌 Instrucciones:
        - Selecciona una opción en el menú lateral.
        - Sube un archivo **Excel** con los datos requeridos.
        - Descarga los resultados en **Excel** o **CSV**.
    """)