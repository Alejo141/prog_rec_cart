import streamlit as st
import pandas as pd
from io import BytesIO
import os
import unidecode  # type: ignore # Librería para eliminar tildes

# Configuración inicial de la app
st.set_page_config(page_title="Recaudo y Cartera", page_icon="📊", layout="wide")

# Título principal
st.title("📊 Captura de Datos")

# Menú de selección
opcion = st.sidebar.selectbox("Selecciona una opción:", ["Inicio", "Recaudo", "Cartera"])

# ------------------- FUNCIONES GENERALES -------------------
def generar_xlsx(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
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

    # Columnas para organizar los inputs
    col1, col2, col3 = st.columns(3)

    # Subir archivos
    with col1:
        archivo_liquidacion = st.file_uploader("📂 Cargar archivo Excel - Liquidación", type=["xlsx"])
    with col2:
        archivo_ordenes = st.file_uploader("📂 Cargar archivo Excel - Órdenes", type=["xlsx"])
    with col3:
        archivo_provision = st.file_uploader("📂 Cargar archivo Excel - Provisión", type=["xlsx"])

    if archivo_liquidacion and archivo_ordenes and archivo_provision:
        # Cargar los datos
        df_liqui = pd.read_excel(archivo_liquidacion)
        df_ordenes = pd.read_excel(archivo_ordenes)
        df_provision = pd.read_excel(archivo_provision)

        # Definir las columnas esperadas
        columnas_liqui = ["Documento", "Código Proyecto", "Fecha", "Forma de Pago", 
                        "Código Punto de Servicio", "Valor Movilizado", "Valor Comisión", 
                        "IVA", "Total Liquidación", "ano"]
        columnas_ordenes = ["NUMERO_ORDEN", "IDENTIFICACION", "NOMBRES", "APELLIDO1", 
                            "APELLIDO2", "FACTURA"]
        columnas_provision = ["NUI", "CC", "PROYECTO"]

        # Filtrar solo las columnas que existen en los DataFrames
        df_liqui = df_liqui[[col for col in columnas_liqui if col in df_liqui.columns]]
        df_ordenes = df_ordenes[[col for col in columnas_ordenes if col in df_ordenes.columns]]
        df_provision = df_provision[[col for col in columnas_provision if col in df_provision.columns]]

        # Mostrar tamaños de las bases
        df1, df2, df3 = len(df_liqui), len(df_ordenes), len(df_provision)

        if df1 == df2:
            # Estandarizar nombres de columnas (eliminar espacios en blanco)
            df_liqui.columns = df_liqui.columns.str.strip().str.upper()
            df_ordenes.columns = df_ordenes.columns.str.strip().str.upper()
            df_provision.columns = df_provision.columns.str.strip().str.upper()

            # Mostrar nombres de columnas para depuración
            #st.write("Columnas en df_liqui:", df_liqui.columns.tolist())
            #st.write("Columnas en df_ordenes:", df_ordenes.columns.tolist())
            #st.write("Columnas en df_provision:", df_provision.columns.tolist())

            # Cruzar los datos por "DOCUMENTO" y "NUMERO_ORDEN"
            if "DOCUMENTO" in df_liqui.columns and "NUMERO_ORDEN" in df_ordenes.columns:
                df_merged = df_liqui.merge(df_ordenes, left_on="DOCUMENTO", right_on="NUMERO_ORDEN", how="inner")
                st.success("✅ Datos cruzados correctamente entre Liquidación y Órdenes.")
                #st.dataframe(df_merged)

                # Cruzar con Provisión por "IDENTIFICACION" y "NUI"
                if "IDENTIFICACION" in df_merged.columns and "NUI" in df_provision.columns:
                    df_total = df_merged.merge(df_provision, left_on="IDENTIFICACION", right_on="NUI", how="inner")
                    st.success("✅ Cruce total correcto con Provisión.")
                    st.dataframe(df_total)

                    # Descargar resultado
                    xlsx = generar_xlsx(df_total)
                    st.download_button(label="📥 Descargar Excel", data=xlsx, file_name="datos_cruzados.xlsx", 
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.error("❌ No se encontraron las columnas 'IDENTIFICACION' o 'NUI'. Verifique los archivos.")
            else:
                st.error("❌ No se encontraron las columnas 'DOCUMENTO' o 'NUMERO_ORDEN'. Verifique los archivos.")
        else:
            st.warning("⚠️ Las bases de datos cargadas no tienen la misma cantidad de registros. Revise antes de continuar.")

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