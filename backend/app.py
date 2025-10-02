from flask import Flask, request, redirect
import pyodbc

app = Flask(__name__)

# Conexión a Azure SQL
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=golcontrol-sqlserver.database.windows.net;"
    "Database=golcontrol_db;"
    "Uid=vista_gc;"  # tu usuario administrador SQL
    "Pwd=*10////10||||Udl;"  
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
    
if __name__ == "__main__":
    app.run(debug=True)
