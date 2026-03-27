from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app_condupro.database import get_connection
from app_condupro.asistencia import actualizar_asistencias
## python -m uvicorn app_condupro.main:app --reload

app = FastAPI()
templates = Jinja2Templates(directory="app_condupro/templates")
app.mount("/static", StaticFiles(directory="app_condupro/static"), name="static")


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
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario no existe"}
        )

    if user["password"] != password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Contraseña incorrecta"}
        )

    if user["rol"] == "admin":
        # Redirige al dashboard admin con el nombre
        return RedirectResponse(url=f"/admin?nombre={user['nombre']}", status_code=302)

    if user["rol"] == "profesor":
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM usuarios WHERE rol='estudiante'")
        estudiantes = cursor.fetchall()
        cursor.close()
        conn.close()

        return templates.TemplateResponse(
            "profesor.html",
            {"request": request, "nombre": user["nombre"], "estudiantes": estudiantes}
        )

    # Estudiante
    return templates.TemplateResponse(
        "estudiante.html",
        {"request": request, "nombre": user["nombre"], "asistencias": user["asistencias"]}
    )


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
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        cursor.close()
        conn.close()
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "El correo ya está registrado"}
        )

    cursor.execute(
        "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s, %s, %s, 'estudiante')",
        (nombre, correo, password)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return RedirectResponse(url="/login", status_code=302)


# ── ADMIN DASHBOARD ──────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def panel_admin(request: Request, nombre: str = "Administrador"):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol='estudiante'")
    total_estudiantes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol='profesor'")
    total_profesores = cursor.fetchone()["total"]

    # Si no tienes tabla vehiculos aún, devuelve 0 sin romper
    try:
        cursor.execute("SELECT COUNT(*) as total FROM vehiculos")
        total_vehiculos = cursor.fetchone()["total"]
    except Exception:
        total_vehiculos = 0

    clases_hoy = 0  # Placeholder hasta que exista tabla horarios

    cursor.execute("SELECT nombre, correo, rol, asistencias FROM usuarios ORDER BY rol, nombre")
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "nombre": nombre,
        "total_estudiantes": total_estudiantes,
        "total_profesores": total_profesores,
        "total_vehiculos": total_vehiculos,
        "clases_hoy": clases_hoy,
        "usuarios": usuarios,
        "mensaje": None,
        "error": None,
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
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        cursor.close()
        conn.close()
        return templates.TemplateResponse(
            "crear_usuario.html",
            {"request": request, "error": "El correo ya está registrado"}
        )

    cursor.execute(
        "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s, %s, %s, %s)",
        (nombre, correo, password, rol)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "crear_usuario.html",
        {"request": request, "mensaje": "Usuario creado correctamente"}
    )


# ── ASISTENCIAS ──────────────────────────────────

@app.get("/actualizar_asistencias")
def actualizar():
    return actualizar_asistencias()

@app.post("/finalizar_clase")
def finalizar_clase(request: Request):
    resultado = actualizar_asistencias()
    print(resultado)
    return JSONResponse(content={"mensaje": "Asistencias registradas correctamente"})