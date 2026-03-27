from app_condupro.sheets import obtener_asistencias, limpiar_sheet
from app_condupro.database import get_connection

def actualizar_asistencias():
    # 1. Obtener datos de Google Sheets
    df = obtener_asistencias()

    if df.empty:
        print("⚠️ No hay datos nuevos en la hoja de cálculo.")
        return {"mensaje": "Sin datos para procesar"}

    print("📊 Datos recibidos (Primeras filas):")
    print(df.head())

    # 2. Limpieza extrema de nombres de columnas
    # Quitamos espacios al inicio/final y pasamos todo a minúsculas
    df.columns = df.columns.str.strip().str.lower()
    
    # 3. Identificar la columna de correo (Buscamos 'correo' o usamos la posición 2)
    columna_correo = None
    for col in df.columns:
        if "correo" in col:
            columna_correo = col
            break
    
    if not columna_correo:
        # Si no encuentra la palabra 'correo', usa la tercera columna por defecto
        columna_correo = df.columns[2]
        print(f"🔎 Columna por nombre no hallada, usando posición 2: '{columna_correo}'")
    else:
        print(f"✅ Procesando columna: '{columna_correo}'")

    # 4. Agrupar y contar asistencias por correo
    try:
        conteo = df.groupby(columna_correo).size()
    except Exception as e:
        print(f"❌ Error al agrupar datos: {e}")
        return {"mensaje": "Error en procesamiento de datos"}

    # 5. Conexión a Base de Datos y Actualización
    try:
        conn = get_connection()
        cursor = conn.cursor()

        print(f"Updating {len(conteo)} usuarios en la base de datos...")

        for correo, cantidad in conteo.items():
            # Ejecutamos el UPDATE sumando la nueva cantidad a la existente
            cursor.execute("""
                UPDATE usuarios 
                SET asistencias = asistencias + %s 
                WHERE correo = %s
            """, (int(cantidad), str(correo).strip()))

        conn.commit()
        print(f"{cursor.rowcount} filas actualizadas en MySQL.")
        
        cursor.close()
        conn.close()

        # 6. Limpiar la hoja de Google Sheets (Solo si la DB se actualizó con éxito)
        limpiar_sheet()
        print("🧹 Google Sheet limpiado con éxito.")

    except Exception as e:
        print(f"❌ Error de Base de Datos: {e}")
        return {"mensaje": f"Error en DB: {e}"}

    print("🚀 Proceso de asistencias finalizado correctamente.")
    return {"mensaje": "Asistencias cargadas y sheet limpio"}