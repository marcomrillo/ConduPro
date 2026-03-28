from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app_condupro.database import get_connection
from app_condupro.asistencia import actualizar_asistencias
from pydantic import BaseModel
## python -m uvicorn app_condupro.main:app --reload

app = FastAPI()
templates = Jinja2Templates(directory="app_condupro/templates")
app.mount("/static", StaticFiles(directory="app_condupro/static"), name="static")


# ── HELPERS ─────────────────────────────────────

def get_clase_activa():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM clases
        WHERE estado IN ('en_espera', 'en_curso')
        ORDER BY fecha ASC, hora ASC
        LIMIT 1
    """)
    clase = cursor.fetchone()
    cursor.close()
    conn.close()
    return clase


def get_inscritos_count(clase_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT COUNT(*) as total FROM inscripciones WHERE clase_id=%s",
        (clase_id,)
    )
    total = cursor.fetchone()["total"]
    cursor.close()
    conn.close()
    return total


# ── INICIO ──────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


# ── LOGIN ────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def mostrar_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    correo: str = Form(...),
    password: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuario no existe"})

    if user["password"] != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Contraseña incorrecta"})

    if user["rol"] == "admin":
        return RedirectResponse(url=f"/admin?nombre={user['nombre']}", status_code=302)

    if user["rol"] == "profesor":
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM usuarios WHERE rol='estudiante'")
        estudiantes = cursor.fetchall()
        cursor.close()
        conn.close()

        clase = get_clase_activa()
        inscritos = get_inscritos_count(clase["id"]) if clase else 0

        return templates.TemplateResponse("profesor.html", {
            "request": request,
            "nombre": user["nombre"],
            "estudiantes": estudiantes,
            "clase": clase,
            "inscritos": inscritos
        })

    # Estudiante
    clase_proxima = get_clase_activa()
    ya_inscrito = False
    if clase_proxima:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM inscripciones WHERE estudiante_correo=%s AND clase_id=%s",
            (user["correo"], clase_proxima["id"])
        )
        ya_inscrito = cursor.fetchone() is not None
        cursor.close()
        conn.close()

    return templates.TemplateResponse("estudiante.html", {
        "request": request,
        "nombre": user["nombre"],
        "correo": user["correo"],
        "asistencias": user["asistencias"],
        "clase_proxima": clase_proxima,
        "ya_inscrito": ya_inscrito
    })


# ── REGISTRO ─────────────────────────────────────

@app.get("/registro", response_class=HTMLResponse)
def mostrar_registro(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


@app.post("/registrar", response_class=HTMLResponse)
def registrar(
    request: Request,
    nombre: str = Form(...),
    correo: str = Form(...),
    password: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return templates.TemplateResponse("registro.html", {"request": request, "error": "El correo ya está registrado"})

    cursor.execute(
        "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s, %s, %s, 'estudiante')",
        (nombre, correo, password)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse(url="/login", status_code=302)


# ── ADMIN ────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def panel_admin(
    request: Request,
    nombre: str = "Administrador",
    mensaje: str = None,
    error: str = None,
    mensaje_clase: str = None,
    error_clase: str = None
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol='estudiante'")
    total_estudiantes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol='profesor'")
    total_profesores = cursor.fetchone()["total"]

    cursor.execute("SELECT nombre, correo, rol, asistencias FROM usuarios ORDER BY rol, nombre")
    usuarios = cursor.fetchall()

    cursor.execute("SELECT nombre, correo FROM usuarios WHERE rol='profesor'")
    profesores = cursor.fetchall()

    cursor.close()
    conn.close()

    clase_activa = get_clase_activa()
    total_inscritos = get_inscritos_count(clase_activa["id"]) if clase_activa else 0

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "nombre": nombre,
        "total_estudiantes": total_estudiantes,
        "total_profesores": total_profesores,
        "total_inscritos": total_inscritos,
        "clase_activa": clase_activa,
        "usuarios": usuarios,
        "profesores": profesores,
        "mensaje": mensaje,
        "error": error,
        "mensaje_clase": mensaje_clase,
        "error_clase": error_clase,
    })


# ── CREAR USUARIO ────────────────────────────────

@app.get("/crear_usuario", response_class=HTMLResponse)
def mostrar_crear_usuario(request: Request):
    return templates.TemplateResponse("crear_usuario.html", {"request": request})


@app.post("/crear_usuario", response_class=HTMLResponse)
def crear_usuario(
    request: Request,
    nombre: str = Form(...),
    correo: str = Form(...),
    password: str = Form(...),
    rol: str = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return templates.TemplateResponse("crear_usuario.html", {"request": request, "error": "El correo ya está registrado"})

    cursor.execute(
        "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s, %s, %s, %s)",
        (nombre, correo, password, rol)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return templates.TemplateResponse("crear_usuario.html", {"request": request, "mensaje": "Usuario creado correctamente"})


# ── CREAR CLASE ──────────────────────────────────

@app.post("/crear_clase")
def crear_clase(
    fecha: str = Form(...),
    hora: str = Form(...),
    tipo: str = Form(...),
    instructor_correo: str = Form(""),
    cupos_total: int = Form(10),
    nombre: str = Form("Administrador")
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clases (fecha, hora, tipo, instructor_correo, cupos_total, cupos_disponibles, estado)
        VALUES (%s, %s, %s, %s, %s, %s, 'en_espera')
    """, (fecha, hora, tipo, instructor_correo or None, cupos_total, cupos_total))
    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse(url=f"/admin?nombre={nombre}&mensaje_clase=Clase creada correctamente", status_code=302)


# ── EDITAR CLASE ─────────────────────────────────

@app.post("/editar_clase")
def editar_clase(
    clase_id: int = Form(...),
    fecha: str = Form(...),
    hora: str = Form(...),
    nombre: str = Form("Administrador")
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clases SET fecha=%s, hora=%s WHERE id=%s AND estado='en_espera'",
        (fecha, hora, clase_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse(url=f"/admin?nombre={nombre}&mensaje_clase=Fecha y hora actualizadas", status_code=302)


# ── INICIAR CLASE ────────────────────────────────

@app.post("/iniciar_clase")
def iniciar_clase():
    clase = get_clase_activa()
    if not clase:
        return JSONResponse(content={"mensaje": "No hay clase activa", "ok": False})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clases SET estado='en_curso' WHERE id=%s", (clase["id"],))
    conn.commit()
    cursor.close()
    conn.close()
    return JSONResponse(content={"mensaje": "¡Clase iniciada!", "ok": True})


# ── FINALIZAR CLASE ──────────────────────────────

@app.post("/finalizar_clase")
def finalizar_clase():
    clase = get_clase_activa()
    if not clase:
        return JSONResponse(content={"mensaje": "No hay clase activa", "ok": False})

    resultado = actualizar_asistencias()
    print(resultado)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clases SET estado='finalizada' WHERE id=%s", (clase["id"],))
    conn.commit()
    cursor.close()
    conn.close()
    return JSONResponse(content={"mensaje": "Clase finalizada y asistencias registradas.", "ok": True})


# ── INSCRIBIRSE ──────────────────────────────────

class InscripcionRequest(BaseModel):
    clase_id: int
    correo: str


@app.post("/inscribirse")
def inscribirse(data: InscripcionRequest):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM clases WHERE id=%s", (data.clase_id,))
    clase = cursor.fetchone()

    if not clase:
        cursor.close(); conn.close()
        return JSONResponse(content={"mensaje": "Clase no encontrada.", "ok": False})

    if clase["cupos_disponibles"] <= 0:
        cursor.close(); conn.close()
        return JSONResponse(content={"mensaje": "No hay cupos disponibles.", "ok": False})

    if clase["tipo"] == "practica":
        cursor.execute("SELECT asistencias FROM usuarios WHERE correo=%s", (data.correo,))
        user = cursor.fetchone()
        if user and user["asistencias"] < 10:
            cursor.close(); conn.close()
            return JSONResponse(content={"mensaje": "Necesitas 10 asistencias para la práctica.", "ok": False})

    cursor.execute(
        "SELECT id FROM inscripciones WHERE estudiante_correo=%s AND clase_id=%s",
        (data.correo, data.clase_id)
    )
    if cursor.fetchone():
        cursor.close(); conn.close()
        return JSONResponse(content={"mensaje": "Ya estás inscrito en esta clase.", "ok": False})

    cursor.execute(
        "INSERT INTO inscripciones (estudiante_correo, clase_id) VALUES (%s, %s)",
        (data.correo, data.clase_id)
    )
    cursor.execute(
        "UPDATE clases SET cupos_disponibles = cupos_disponibles - 1 WHERE id=%s",
        (data.clase_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return JSONResponse(content={"mensaje": "¡Inscripción exitosa!", "ok": True})


# ── ASISTENCIAS ──────────────────────────────────

@app.get("/actualizar_asistencias")
def actualizar():
    return actualizar_asistencias()