import sqlite3
import os
from flask import g, current_app
import pandas as pd

# Caminho para o banco de dados
DATABASE = os.path.join(os.getcwd(), 'database.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # Criar tabela de produtos se não existir
    db.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        nome TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        imagem TEXT
    )
    ''')
    
    # Criar tabela de vendas se não existir
    db.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        data_venda DATETIME NOT NULL
    )
    ''')
    
    # Criar tabela de itens de venda se não existir
    db.execute('''
    CREATE TABLE IF NOT EXISTS itens_venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        lucro REAL NOT NULL,
        FOREIGN KEY (venda_id) REFERENCES vendas (id),
        FOREIGN KEY (produto_id) REFERENCES produtos (id)
    )
    ''')
    
    db.commit()

def adicionar_produto(nome, preco, quantidade, valor_compra, imagem=None):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO produtos (nome, preco, quantidade, valor_compra, imagem) VALUES (?, ?, ?, ?, ?)",
            (nome, preco, quantidade, valor_compra, imagem)
        )
        db.commit()
        produto_id = cursor.lastrowid
        return buscar_produto(produto_id)
    except Exception as e:
        print(f"Erro ao adicionar produto: {str(e)}")
        return None

def buscar_produto(produto_id):
    db = get_db()
    try:
        produto = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if produto:
            return {
                "id": produto["id"],
                "nome": produto["nome"],
                "preco": produto["preco"],
                "quantidade": produto["quantidade"],
                "valor_compra": produto["valor_compra"],
                "imagem": produto["imagem"]
            }
        return None
    except Exception as e:
        print(f"Erro ao buscar produto: {str(e)}")
        return None

def deletar_produto(produto_id):
    db = get_db()
    try:
        cursor = db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erro ao deletar produto: {str(e)}")
        return False

def obter_produtos_do_banco():
    db = get_db()
    try:
        produtos = db.execute("SELECT * FROM produtos ORDER BY nome").fetchall()
        return [{
            "id": p["id"],
            "nome": p["nome"],
            "preco": p["preco"],
            "quantidade": p["quantidade"],
            "valor_compra": p["valor_compra"],
            "imagem": p["imagem"]
        } for p in produtos]
    except Exception as e:
        print(f"Erro ao obter produtos: {str(e)}")
        return []

def gerar_relatorio_vendas(data_inicio, data_fim):
    db = get_db()
    try:
        query = """
        SELECT 
            p.nome as produto, 
            SUM(iv.quantidade) as quantidade, 
            SUM(iv.subtotal) as subtotal, 
            SUM(iv.lucro) as lucro,
            v.data_venda
        FROM 
            itens_venda iv
        JOIN 
            produtos p ON iv.produto_id = p.id
        JOIN 
            vendas v ON iv.venda_id = v.id
        WHERE 
            v.data_venda BETWEEN ? AND ?
        GROUP BY 
            p.id
        ORDER BY 
            p.nome
        """
        
        resultados = db.execute(query, (data_inicio, data_fim)).fetchall()
        
        return [{
            "produto": r["produto"],
            "quantidade": r["quantidade"],
            "subtotal": r["subtotal"],
            "lucro": r["lucro"],
            "data_venda": r["data_venda"]
        } for r in resultados]
    except Exception as e:
        print(f"Erro ao gerar relatório de vendas: {str(e)}")
        return []

def gerar_relatorio_estoque():
    db = get_db()
    try:
        query = """
        SELECT 
            id,
            nome,
            quantidade as estoque_atual,
            preco as preco_venda,
            valor_compra
        FROM 
            produtos
        ORDER BY 
            nome
        """
        
        resultados = db.execute(query).fetchall()
        
        return [{
            "id": r["id"],
            "nome": r["nome"],
            "estoque_atual": r["estoque_atual"],
            "preco_venda": r["preco_venda"],
            "valor_compra": r["valor_compra"]
        } for r in resultados]
    except Exception as e:
        print(f"Erro ao gerar relatório de estoque: {str(e)}")
        return []