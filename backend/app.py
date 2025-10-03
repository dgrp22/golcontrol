from flask import Flask, request, redirect
from flask_cors import CORS
import pyodbc

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://kind-desert-05fafcb0f.2.azurestaticapps.net"}})
# Conexión a Azure SQL
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=golcontrol-sqlserver.database.windows.net;"
    "Database=golcontrol_db;"
    "Uid=vista_gc;"  # tu usuario administrador SQL
    "Pwd=*10////10||||Udl;"  # 👈 reemplaza por tu contraseña real
)

@app.route('/')
def home():
    return "GolControl backend funcionando ✅"

# Endpoint para registrar clientes
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

        # Después del registro, redirige al login
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
        data = request.json  # recibe JSON desde JS

        cliente_id = data.get("cliente_id", 0)  # si manejas clientes registrados
        cancha_id  = data.get("cancha_id", 0)   # si manejas catálogo de canchas
        fecha      = data["fecha"]              # "2025-10-03"
        hora_inicio= data["hora_inicio"]        # "09:00"
        hora_fin   = data["hora_fin"]           # "11:00"
        nombre     = data["nombre_cliente"]
        celular    = data.get("celular")
        abono      = data["abono"]
        precio     = data["precio_total"]
        estado_pago= data["estado_pago"]        # "Pagado", "Parcial", etc.
        estado_reserva = data["estado_reserva"] # "Activa", "Anulada", etc.

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dbo.reservas 
            (cliente_id, cancha_id, fecha, hora_inicio, hora_fin, nombre_cliente, celular, abono, precio_total, estado_pago, estado_reserva)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, cancha_id, fecha, hora_inicio, hora_fin, nombre, celular, abono, precio, estado_pago, estado_reserva))
        conn.commit()
        conn.close()

        return {"ok": True, "msg": "Reserva guardada correctamente"}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


# --- Obtener reservas por fecha y cancha ---
@app.route('/reservas', methods=['GET'])
def get_reservas():
    try:
        fecha = request.args.get("fecha")        # ej: "2025-10-03"
        cancha_id = request.args.get("cancha_id") # ej: "1"

        if not fecha or not cancha_id:
            return {"ok": False, "error": "Se requiere fecha y cancha_id"}, 400

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hora_inicio, hora_fin, nombre_cliente, celular, 
                   precio_total, abono, estado_pago, estado_reserva
            FROM dbo.reservas
            WHERE fecha = ? AND cancha_id = ?
        """, (fecha, cancha_id))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            result.append({
                "hora_inicio": str(r.hora_inicio)[:5], # "09:00"
                "hora_fin": str(r.hora_fin)[:5],       # "11:00"
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
