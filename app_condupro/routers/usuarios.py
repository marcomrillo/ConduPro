from fastapi import APIRouter
from app_condupro.database import get_connection

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.post("/")
def crear_usuario(nombre: str, correo: str, password: str, rol: str):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO usuarios (nombre, correo, password, rol)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (nombre, correo, password, rol))
    conn.commit()

    cursor.close()
    conn.close()

    return {"mensaje": "Usuario creado"}