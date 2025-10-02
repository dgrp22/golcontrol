from flask import Flask, request
import pyodbc

app = Flask(__name__)

# Conexión a Azure SQL
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=golcontrol-sqlserver.database.windows.net;"
    "Database=golcontrol_db;"
    "Uid=vista_gc;"  # usuario administrador SQL
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
    usuario = request.form['user']
    password = request.form['pass']

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dbo.clientes (nombre_negocio, direccion, contacto, usuario_login, password_hash, activo)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (nombre_negocio, direccion, contacto, usuario, password))
        conn.commit()
        conn.close()

        # Mostrar mensaje de éxito y luego redirigir en 3s
        html = """
        <html>
        <head>
          <meta http-equiv="refresh" content="3;url=https://kind-desert-05fafcb0f.2.azurestaticapps.net/index.html" />
        </head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
          <h2 style="color: green;">✅ Registro exitoso</h2>
          <p>Serás redirigido al login en unos segundos...</p>
        </body>
        </html>
        """
        return html

    except Exception as e:
        return f"❌ Error al registrar: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
