from flask import Flask, request, redirect
import pyodbc

app = Flask(__name__)

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
    
    
if __name__ == "__main__":
    app.run(debug=True)
