import sqlite3

conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE produtos
ADD COLUMN descricao TEXT
""")

conn.commit()
conn.close()

print("Coluna descricao adicionada com sucesso!")