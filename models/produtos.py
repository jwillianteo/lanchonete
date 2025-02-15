import os
from werkzeug.utils import secure_filename
from data.database import produtos

# Definir o diretório onde as imagens serão salvas
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class Produto:
    def __init__(self, nome, preco, quantidade, valor_compra, imagem=None):
        self.id = len(produtos) + 1
        self.nome = nome
        self.preco = preco
        self.quantidade = quantidade
        self.valor_compra = valor_compra
        self.imagem = imagem  # Caminho da imagem

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "preco": self.preco,
            "quantidade": self.quantidade,
            "valor_compra": self.valor_compra,
            "imagem": self.imagem
        }

def adicionar_produto(nome, preco, quantidade, valor_compra, imagem=None):
    # Verificar se os valores são numéricos
    try:
        preco = float(preco)
    except ValueError:
        raise ValueError("Preco deve ser um número válido.")
    
    try:
        quantidade = int(quantidade)
    except ValueError:
        raise ValueError("Quantidade deve ser um número válido.")
    
    try:
        valor_compra = float(valor_compra)
    except ValueError:
        raise ValueError("Valor de compra deve ser um número válido.")

    produto = Produto(nome, preco, quantidade, valor_compra, imagem)
    produtos.append(produto)
    return produto.to_dict()

def listar_produtos():
    return [produto.to_dict() for produto in produtos]

def buscar_produto(produto_id):
    for produto in produtos:
        if produto.id == produto_id:
            return produto.to_dict()
    return None

def atualizar_produto(produto_id, nome=None, preco=None, quantidade=None, valor_compra=None, imagem=None):
    for produto in produtos:
        if produto.id == produto_id:
            # Atualiza os campos fornecidos
            if nome:
                produto.nome = nome
            if preco is not None:
                try:
                    produto.preco = float(preco)
                except ValueError:
                    raise ValueError("Preco deve ser um número válido.")
            if quantidade is not None:
                try:
                    produto.quantidade = int(quantidade)
                except ValueError:
                    raise ValueError("Quantidade deve ser um número válido.")
            if valor_compra is not None:
                try:
                    produto.valor_compra = float(valor_compra)
                except ValueError:
                    raise ValueError("Valor de compra deve ser um número válido.")
            if imagem:
                produto.imagem = imagem
            return produto.to_dict()
    return None

def deletar_produto(produto_id):
    global produtos
    produtos = [produto for produto in produtos if produto.id != produto_id]
    return True
