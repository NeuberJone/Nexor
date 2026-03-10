from storage.database import init_database, get_connection

print("Inicializando banco...")

init_database()

conn = get_connection()

conn.execute("""
INSERT INTO log_sources (name, path, recursive, enabled)
VALUES (?, ?, ?, ?)
""", (
    "Logs Teste",
    "E:\\Projetos\\Nexor\\logs_import",
    1,
    1
))

conn.commit()
conn.close()

print("Fonte de logs cadastrada.")