from flask import Flask, request, redirect, session
from flask_session import Session
from flask_cors import CORS
import pyodbc

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://kind-desert-05fafcb0f.2.azurestaticapps.net"}})

# Configuración de sesiones
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "clave-super-secreta"  # cámbiala en producción
Session(app)

# Conexión a Azure SQL
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=golcontrol-sqlserver.database.windows.net;"
    "Database=golcontrol_db;"
    "Uid=vista_gc;"
    "Pwd=*10////10||||Udl;"  # 👈 reemplaza por tu contraseña real
)

@app.route('/')
def home():
    return "GolControl backend funcionando ✅"

# --- Registrar clientes ---
@app.route('/register', methods=['POST'])
def register():
    nombre_negocio = request.form['nombre_negocio']
    direccion = request.form['direccion']
    contacto = request.form['contacto']
    correo = request.form['correo']
    telefono = request.form['telefono']
    usuario = request.form['user']
    password = request.form['pass']

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dbo.clientes (nombre_negocio, direccion, contacto, correo, telefono, usuario_login, password_hash, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (nombre_negocio, direccion, contacto, correo, telefono, usuario, password))
        conn.commit()
        conn.close()
        return redirect("https://kind-desert-05fafcb0f.2.azurestaticapps.net/index.html")
    except Exception as e:
        return f"Error al registrar: {str(e)}", 500

# --- Login ---
@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['user']
    password = request.form['pass']
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM dbo.clientes
            WHERE usuario_login = ? AND password_hash = ?
        """, (usuario, password))
        row = cursor.fetchone()
        conn.close()

        if row:
            session["dueno_id"] = row.id  # Guardamos el dueño logueado
            return redirect("https://kind-desert-05fafcb0f.2.azurestaticapps.net/inicio.html")
        else:
            return """
            <html><body style="font-family:Arial;text-align:center;margin-top:50px;">
            <h2 style="color:red;">❌ Usuario o contraseña incorrectos</h2>
            <a href='https://kind-desert-05fafcb0f.2.azurestaticapps.net/index.html'>Volver al login</a>
            </body></html>
            """
    except Exception as e:
        return f"❌ Error al iniciar sesión: {str(e)}", 500

# --- Guardar reserva ---
@app.route('/reservar', methods=['POST'])
def reservar():
    try:
        if "dueno_id" not in session:
            return {"ok": False, "error": "Sesión no iniciada"}, 401

        dueno_id = session["dueno_id"]  # dueño logueado
        data = request.json  

        cancha_id  = data.get("cancha_id")   
        fecha      = data["fecha"]              
        hora_inicio= data["hora_inicio"]        
        hora_fin   = data["hora_fin"]           
        nombre     = data["nombre_cliente"]
        celular    = data.get("celular")
        abono      = float(data["abono"])
        precio     = float(data["precio_total"])

        # Calcular estado_pago automáticamente
        if abono == 0:
            estado_pago = "No Abono"
        elif abono < precio:
            estado_pago = "Parcial"
        else:
            estado_pago = "Pagado"

        estado_reserva = "Activa"

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dbo.reservas 
            (dueno_id, cancha_id, fecha, hora_inicio, hora_fin, nombre_cliente, celular, abono, precio_total, estado_pago, estado_reserva)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (dueno_id, cancha_id, fecha, hora_inicio, hora_fin, nombre, celular, abono, precio, estado_pago, estado_reserva))
        conn.commit()
        conn.close()

        return {"ok": True, "msg": "Reserva guardada correctamente"}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

# --- Registrar abono ---
@app.route('/abonar', methods=['POST'])
def abonar():
    try:
        data = request.json
        reserva_id = data["reserva_id"]
        monto = float(data["monto_abono"])

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Insertar abono
        cursor.execute("""
            INSERT INTO dbo.abonos (reserva_id, monto_abono, fecha_abono)
            VALUES (?, ?, GETDATE())
        """, (reserva_id, monto))

        # Calcular total de abonos
        cursor.execute("SELECT SUM(monto_abono) FROM dbo.abonos WHERE reserva_id = ?", (reserva_id,))
        total_abonos = cursor.fetchone()[0] or 0

        # Obtener precio total de la reserva
        cursor.execute("SELECT precio_total FROM dbo.reservas WHERE id = ?", (reserva_id,))
        precio_total = cursor.fetchone()[0]

        # Calcular estado_pago
        if total_abonos == 0:
            estado_pago = "No Abono"
        elif total_abonos < precio_total:
            estado_pago = "Parcial"
        else:
            estado_pago = "Pagado"

        # Actualizar reservas
        cursor.execute("UPDATE dbo.reservas SET abono=?, estado_pago=? WHERE id=?", (total_abonos, estado_pago, reserva_id))
        conn.commit()
        conn.close()

        return {"ok": True, "msg": "Abono registrado correctamente", "total_abonos": total_abonos, "estado_pago": estado_pago}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

# --- Obtener reservas por fecha y cancha ---
@app.route('/reservas', methods=['GET'])
def get_reservas():
    try:
        fecha = request.args.get("fecha")
        cancha_id = request.args.get("cancha_id")

        if not fecha or not cancha_id:
            return {"ok": False, "error": "Se requiere fecha y cancha_id"}, 400

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, hora_inicio, hora_fin, nombre_cliente, celular, 
                   precio_total, abono, estado_pago, estado_reserva
            FROM dbo.reservas
            WHERE fecha = ? AND cancha_id = ?
        """, (fecha, cancha_id))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            result.append({
                "reserva_id": r.id,
                "hora_inicio": str(r.hora_inicio)[:5],
                "hora_fin": str(r.hora_fin)[:5],
                "nombre_cliente": r.nombre_cliente,
                "celular": r.celular,
                "precio_total": float(r.precio_total),
                "abono": float(r.abono),
                "estado_pago": r.estado_pago,
                "estado_reserva": r.estado_reserva
            })

        return {"ok": True, "reservas": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
