import sqlite3

conn = sqlite3.connect("sistema.db")
c = conn.cursor()

# Ver usuarios primero
c.execute("SELECT usuario, password, rol FROM usuarios")
print("USUARIOS:")
for u in c.fetchall():
    print(u)

# Reset docente
c.execute("""
UPDATE usuarios
SET password = '0204'
WHERE usuario = 'docente1'
""")

conn.commit()
conn.close()

print("✔ Contraseña de docente1 cambiada a 1234")