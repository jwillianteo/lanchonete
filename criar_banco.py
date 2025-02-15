# Importa a aplicação Flask do arquivo app.py
from app import app

# Importa a função init_db do arquivo database.py
from database import init_db

# Executa a função init_db() dentro do contexto da aplicação Flask
with app.app_context():
    print("Inicializando o banco de dados...")
    init_db()  # Cria as tabelas no banco de dados
    print("Banco de dados inicializado com sucesso!")