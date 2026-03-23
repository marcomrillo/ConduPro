from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app_condupro.database import get_connection
import mysql.connector
from app_condupro.asistencia import actualizar_asistencias
from fastapi.responses import RedirectResponse
## python -m uvicorn app_condupro.main:app --reload iniciar el servidor

app = FastAPI()
# rutas
templates = Jinja2Templates(directory="app_condupro/templates")
app.mount("/static", StaticFiles(directory="app_condupro/static"), name="static")

# INICIO

@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# MOSTRAR LOGIN

@app.get("/login", response_class=HTMLResponse)
def mostrar_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# LOGIN

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

# Usuario no existe
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario no existe"}
        )

# Contraseña incorrecta
    if user["password"] != password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Contraseña incorrecta"}
        )

# Rol
    if user["rol"] == "admin":
        return RedirectResponse(url="/crear_usuario", status_code=302)

    if user["rol"] == "profesor":

        connexion = get_connection()
        cursor = connexion.cursor(dictionary=True)

        cursor.execute("SELECT nombre FROM usuarios WHERE rol='estudiante'")
        estudiantes = cursor.fetchall()

        cursor.close()
        connexion.close()

        return templates.TemplateResponse(
        "profesor.html",
        {
            "request": request,
            "nombre": user["nombre"],
            "estudiantes": estudiantes
        }
    )

    return templates.TemplateResponse(
    "estudiante.html",
    {
        "request": request,
        "nombre": user["nombre"],
        "asistencias": user["asistencias"]
    }
)



# MOSTRAR REGISTRO


@app.get("/registro", response_class=HTMLResponse)
def mostrar_registro(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


# REGISTRAR

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

    query = """
    INSERT INTO usuarios (nombre, correo, password, rol)
    VALUES (%s, %s, %s, 'estudiante')
    """
    cursor.execute(query, (nombre, correo, password))
    conn.commit()

    cursor.close()
    conn.close()

    return RedirectResponse(url="/login", status_code=302)


# CREAR USUARIO COMO ADMIN

@app.get("/crear_usuario", response_class=HTMLResponse)
def mostrar_crear_usuario(request: Request):
    return templates.TemplateResponse(
        "crear_usuario.html",
        {"request": request}
    )


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

    query = """
    INSERT INTO usuarios (nombre, correo, password, rol)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (nombre, correo, password, rol))
    conn.commit()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        "crear_usuario.html",
        {"request": request, "mensaje": "Usuario creado correctamente"}
    )

# count 

@app.get("/actualizar_asistencias")
def actualizar():

    return actualizar_asistencias()

@app.post("/finalizar_clase")
def finalizar_clase(request: Request):

    print("🔥 Endpoint ejecutado")  # DEBUG

    resultado = actualizar_asistencias()

    print(resultado)

    return RedirectResponse(url="/login", status_code=302)