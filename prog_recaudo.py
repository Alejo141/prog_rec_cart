import streamlit as st
import pandas as pd
from io import BytesIO
import locale
import platform
import os
import unidecode  # type: ignore

# Configuración inicial de la app
st.set_page_config(page_title="Recaudo y Cartera", page_icon="📊", layout="wide")

# Título principal
st.title("📊 Captura de Datos")

# Menú de selección
opcion = st.sidebar.selectbox("Selecciona una opción:", ["Inicio", "Recaudo", "Cartera"])

# ------------------- FUNCIONES GENERALES -------------------
def generar_xlsx(df1, df2, df3, df4, df5):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, sheet_name='Datos_Cruzados', index=False)
        df2.to_excel(writer, sheet_name='Resumen_Recaudo', startrow= 1, startcol=1, index=False)
        df3.to_excel(writer, sheet_name='Resumen_Recaudo', startrow= 1, startcol=7, index=False)
        df4.to_excel(writer, sheet_name='Resumen_Recaudo', startrow= 1, startcol=10, index=False)
        df5.to_excel(writer, sheet_name='Resumen_Recaudo', startrow= 1, startcol=16, index=False)
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

    col3, col4, col5 = st.columns(3)

    with col3:
        archivo_provision = st.file_uploader("📂 Cargar archivo Excel - Provisión", type=["xlsx"])
    with col4:
        archivo_siigo = st.file_uploader("📂 Cargar archivo Excel - Siigo", type=["xlsx"])
    with col5:
        archivo_acumulado = st.file_uploader("📂 Cargar archivo Excel - Acumulado", type=["xlsx"])


    if archivo_liquidacion and archivo_ordenes and archivo_provision:
        # Cargar los datos en DataFrames
        df_liqui = pd.read_excel(archivo_liquidacion)
        df_ordenes = pd.read_excel(archivo_ordenes)
        df_provision = pd.read_excel(archivo_provision)
        df_siigo = pd.read_excel(archivo_siigo)
        df_acumulado = pd.read_excel(archivo_acumulado)

        # Normalizar nombres de columnas
        df_liqui.columns = df_liqui.columns.str.strip().str.upper()
        df_ordenes.columns = df_ordenes.columns.str.strip().str.upper()
        df_provision.columns = df_provision.columns.str.strip().str.upper()
        df_siigo.columns = df_siigo.columns.str.strip().str.upper()
        df_acumulado.columns = df_acumulado.columns.str.strip().str.upper()


        columnas_liqui = ["DOCUMENTO", "CÓDIGO PROYECTO", "FECHA", "FORMA DE PAGO", 
                          "CÓDIGO PUNTO DE SERVICIO", "VALOR MOVILIZADO", "VALOR COMISIÓN", 
                          "IVA", "TOTAL LIQUIDACIÓN", "ANO"]
        columnas_ordenes = ["NUMERO_ORDEN", "IDENTIFICACION", "NOMBRES", "APELLIDO1", "APELLIDO2", "FACTURA"]
        columnas_provision = ["NUI", "CC", "PROYECTO"]
        columnas_siigo = ["CÓDIGO CONTABLE", "CUENTA CONTABLE", "COMPROBANTE", "SECUENCIA", "FECHA ELABORACIÓN", 
                          "IDENTIFICACIÓN", "NOMBRE DEL TERCERO", "DESCRIPCIÓN", "CENTRO DE COSTO", "DÉBITO"]
        columnas_acumulado = ["MEDIO DE PAGO","MEDIO DE RECAUDO","FECHA", "MES", "AÑO", "CÓDIGO PUNTO DE SERVICIO", "ORDEN DE SERVICIO", "VALOR MOVILIZADO","VALOR COMISIÓN",
                              "IVA", "TOTAL LIQUIDACIÓN", "NUI", "CEDULA", "NOMBRE", "FACTURA", "MUNICIPIO","VALIDADO","COMPROBANTE CONTABLE"]

        df_liqui = df_liqui[[col for col in columnas_liqui if col in df_liqui.columns]]
        df_ordenes = df_ordenes[[col for col in columnas_ordenes if col in df_ordenes.columns]]
        df_provision = df_provision[[col for col in columnas_provision if col in df_provision.columns]]
        df_siigo = df_siigo[[col for col in columnas_siigo if col in df_siigo.columns]]
        df_acumulado = df_acumulado[[col for col in columnas_acumulado if col in df_acumulado.columns]]

        if all(col in df_ordenes.columns for col in ["NOMBRES", "APELLIDO1", "APELLIDO2"]):
            df_ordenes["NOMBRE_COMPLETO"] = (
                df_ordenes["NOMBRES"].fillna('').apply(lambda x: unidecode.unidecode(x)) + " " +
                df_ordenes["APELLIDO1"].fillna('').apply(lambda x: unidecode.unidecode(x)) + " " +
                df_ordenes["APELLIDO2"].fillna('').apply(lambda x: unidecode.unidecode(x))
            ).str.strip()

        df1, df2, df3, df4, df5 = len(df_liqui), len(df_ordenes), len(df_provision), len(df_siigo), len(df_acumulado)

        #st.write("Base inicial Acumulada")
        #st.dataframe(df_acumulado)

        df_siigo['DESCRIPCIÓN'] = df_siigo['DESCRIPCIÓN'].str.replace(r'-\s+', '-', regex=True)
        df_siigo[['FACTURA', 'IDENTIFICACION']] = df_siigo['DESCRIPCIÓN'].str.extract(r'^FV-\d+-(\d+)\s+(\d+)')
        #st.dataframe(df_siigo[['FACTURA', 'IDENTIFICACION']])

        #st.dataframe(df_siigo)

        if df1 == df2:
            df_merged = df_liqui.merge(df_ordenes, left_on="DOCUMENTO", right_on="NUMERO_ORDEN", how="inner")

            #st.success("✅ Datos cruzados correctamente.")
            df_merged = df_merged.drop(columns=["NOMBRES", "APELLIDO1", "APELLIDO2"]).reset_index(drop=True)

            if "IDENTIFICACION" in df_merged.columns and "NUI" in df_provision.columns:
                df_total = df_merged.merge(df_provision, left_on="IDENTIFICACION", right_on="NUI", how="inner")

                df_total["FACTURA"] = df_total["FACTURA"].astype(str).str.replace(r"FE ", "", regex=True)

                # Establecer localización en español según el sistema operativo
                sistema = platform.system()
                try:
                    if sistema == "Windows":
                        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
                except locale.Error:
                    st.warning("⚠️ No se pudo establecer la localización en español. El nombre del mes podría mostrarse en inglés.")

                # 📅 Separar FECHA en AÑO y MES (en español)
                # Crear diccionario de meses en español (en mayúsculas)
                meses_es = {
                    'JANUARY': 'ENERO',
                    'FEBRUARY': 'FEBRERO',
                    'MARCH': 'MARZO',
                    'APRIL': 'ABRIL',
                    'MAY': 'MAYO',
                    'JUNE': 'JUNIO',
                    'JULY': 'JULIO',
                    'AUGUST': 'AGOSTO',
                    'SEPTEMBER': 'SEPTIEMBRE',
                    'OCTOBER': 'OCTUBRE',
                    'NOVEMBER': 'NOVIEMBRE',
                    'DECEMBER': 'DICIEMBRE'
                }
                
                # Convertir a datetime y extraer año y mes en español
                df_total['FECHA'] = pd.to_datetime(df_total['FECHA'], errors='coerce')
                df_total['AÑO'] = df_total['FECHA'].dt.year
                df_total['MES'] = df_total['FECHA'].dt.strftime('%B').str.upper().map(meses_es)

                st.success("✅ Cruce total correcto.")
                st.dataframe(df_total)

###############################################################################################################################################
                
                #st.write("Base para agregar al Acumulado")
                df_organizable = df_total.copy()
                df_para_agregar = df_organizable[["FECHA", "MES", "AÑO", "CÓDIGO PUNTO DE SERVICIO", "NUMERO_ORDEN", "VALOR MOVILIZADO","VALOR COMISIÓN",
                                                  "IVA", "TOTAL LIQUIDACIÓN", "NUI", "CC", "NOMBRE_COMPLETO", "FACTURA", "PROYECTO"]]
                # Agregar columna con valor fijo
                # Insertar columna al inicio (posición 0)
                df_para_agregar.insert(0, "MEDIO DE PAGO", "EFECTY")
                df_para_agregar.insert(1, "MEDIO DE RECAUDO", "")
                df_para_agregar.insert(16, "VALIDADO", "")
                df_para_agregar.insert(17, "COMPROBANTE CONTABLE", "")
                
                # Renombrar columnas de df_para_agregar para que coincidan con las de df_acumulado
                df_para_agregar = df_para_agregar.rename(columns={
                    "NUMERO_ORDEN": "ORDEN DE SERVICIO",
                    "CC": "CEDULA",
                    "NOMBRE_COMPLETO": "NOMBRE",
                    "PROYECTO": "MUNICIPIO"
                })
                #st.dataframe(df_para_agregar)

                st.subheader("📋 Base Unida Acumulada")
                # Asegurar que ambos DataFrames tengan el mismo número de columnas
                min_cols = min(df_acumulado.shape[1], df_para_agregar.shape[1])
                df_acumulado = df_acumulado.iloc[:, :min_cols]
                df_para_agregar = df_para_agregar.iloc[:, :min_cols]

                df_unido = pd.concat([df_para_agregar,df_acumulado], axis=0, ignore_index=True)
                st.dataframe(df_unido)

                st.subheader("Totales:")
                st.write("Acumulada:", len(df_acumulado))
                st.write("Agregar:", len(df_para_agregar))
                st.write("Unida:", len(df_unido))

###############################################################################################################################################


                col1, col2 = st.columns(2)

                # Estandarizar nombres de columnas (en mayúsculas y sin espacios)
                df_total.columns = df_total.columns.str.upper().str.strip()
                df_siigo.columns = df_siigo.columns.str.upper().str.strip()

                with col1:
                    sum_val_movil = df_total.groupby("CC")["VALOR MOVILIZADO"].sum().reset_index()
                    sum_total_val_movil = df_total["VALOR MOVILIZADO"].sum()
                    
                    # Agregar fila de total
                    total_row = pd.DataFrame([["TOTAL GENERAL", sum_total_val_movil]], columns=["CC", "VALOR MOVILIZADO"])
                    sum_val_movil = pd.concat([sum_val_movil, total_row], ignore_index=True)
                    
                    #st.dataframe(sum_val_movil)

                with col2:
                    sum_siigo = df_siigo.groupby('IDENTIFICACION')["DÉBITO"].sum().reset_index()
                    sum_total_siigo = df_siigo["DÉBITO"].sum()
                    
                    # Agregar fila de total
                    total_row_siigo = pd.DataFrame([["TOTAL GENERAL", sum_total_siigo]], columns=["IDENTIFICACION", "DÉBITO"])
                    sum_siigo = pd.concat([sum_siigo, total_row_siigo], ignore_index=True)
                    
                    #st.dataframe(sum_siigo)

###############################################################################################################################################
                
                st.subheader("Diferencias Efecty vs Siigo", divider="blue")
                
                # Convertir claves a string antes del merge
                sum_val_movil["CC"] = sum_val_movil["CC"].astype(str)
                sum_siigo["IDENTIFICACION"] = sum_siigo["IDENTIFICACION"].astype(str)

                # Merge usando columnas diferentes
                solo_df1 = sum_val_movil.merge(
                    sum_siigo,
                    left_on='CC',
                    right_on='IDENTIFICACION',
                    how='left',
                    suffixes=('_df_sum_val_movil', '_df2_sum_siigo')
                )
                # Calcular diferencias entre VALOR MOVILIZADO y DÉBITO
                solo_df1["DIFERENCIA_EFECTY_SIIGO"] = solo_df1["VALOR MOVILIZADO"] - solo_df1["DÉBITO"]
                #solo_df1["DIFERENCIA_SIIGO_EFECTY"] = solo_df1["DÉBITO"] - solo_df1["VALOR MOVILIZADO"]

                st.dataframe(solo_df1)           

                # Filtrar los que no están en sum_siigo
                no_en_sum_siigo = solo_df1[solo_df1["DÉBITO"].isna()]
                resultado_1 = no_en_sum_siigo[['CC', 'VALOR MOVILIZADO']]
                st.dataframe(resultado_1)

###############################################################################################################################################

                st.subheader("Diferencias Siigo vs Efecty", divider="blue")

                # Merge usando columnas diferentes
                solo_df2 = sum_siigo.merge(
                    sum_val_movil,
                    left_on='IDENTIFICACION',
                    right_on='CC',
                    how='left',
                    suffixes=('_df2_sum_siigo', '_df_sum_val_movil')
                )
                #solo_df2["DIFERENCIA_EFECTY_SIIGO"] = solo_df2["VALOR MOVILIZADO"] - solo_df2["DÉBITO"]
                solo_df2["DIFERENCIA_SIIGO_EFECTY"] = solo_df2["DÉBITO"] - solo_df2["VALOR MOVILIZADO"]

                st.dataframe(solo_df2)

                #Resultado o diferencias
                no_en_sum_val_movil = solo_df2[solo_df2['VALOR MOVILIZADO'].isna()]
                resultado_2 = no_en_sum_val_movil[['IDENTIFICACION', 'DÉBITO']]
                st.dataframe(resultado_2)


                # Descargar resultado con dos hojas
                xlsx = generar_xlsx(df_total, solo_df1, resultado_1, solo_df2, resultado_2)
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