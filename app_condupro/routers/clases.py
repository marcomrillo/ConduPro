from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/clases", tags=["clases"])

@router.post("/")
def crear_clase(tipo: str, inicio: str, fin: str, profesor_id: int, creado_por: int):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO clases (tipo, fecha_hora_inicio, fecha_hora_fin, profesor_id, creado_por)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (tipo, inicio, fin, profesor_id, creado_por))
    conn.commit()

    cursor.close()
    conn.close()

    return {"mensaje": "Clase creada"}