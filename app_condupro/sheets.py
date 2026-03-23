import gspread
import pandas as pd
import os

def obtener_asistencias():

    dir_proyecto = r"C:\Users\Personal\Documents\ConduPro\app_condupro"
    ruta_json = os.path.join(dir_proyecto, "credentials.json")
    ruta_token = os.path.join(dir_proyecto, "authorized_user.json")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    gc = gspread.oauth(
        credentials_filename=ruta_json,
        authorized_user_filename=ruta_token,
        scopes=scopes
    )

    spreadsheet_id = "12AUWmfjZFANoajFb6IChKXv79EItFa6GmFhsbflaCQc"
    sheet = gc.open_by_key(spreadsheet_id).sheet1

    datos = sheet.get_all_records()

    return pd.DataFrame(datos)


# 🔥 ESTA ES LA QUE TE FALTA
def limpiar_sheet():

    dir_proyecto = r"C:\Users\Personal\Documents\ConduPro\app_condupro"
    ruta_json = os.path.join(dir_proyecto, "credentials.json")
    ruta_token = os.path.join(dir_proyecto, "authorized_user.json")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    gc = gspread.oauth(
        credentials_filename=ruta_json,
        authorized_user_filename=ruta_token,
        scopes=scopes
    )

    spreadsheet_id = "12AUWmfjZFANoajFb6IChKXv79EItFa6GmFhsbflaCQc"
    sheet = gc.open_by_key(spreadsheet_id).sheet1

    # 🔥 SOLO BORRAR FILAS DESPUÉS DEL HEADER
    sheet.resize(rows=1)

    print("🧹 Datos limpiados, encabezados conservados")