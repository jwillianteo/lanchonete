import sqlite3

# Nome do banco de dados
nome_banco = 'lanchonete/banco.db'  # Caminho correto do banco de dados

# Conectando ao banco de dados
conn = sqlite3.connect(nome_banco)
cursor = conn.cursor()

# Listando as tabelas no banco de dados
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelas = cursor.fetchall()

print("Tabelas encontradas no banco de dados:")
for tabela in tabelas:
    print(tabela[0])

conn.close()
