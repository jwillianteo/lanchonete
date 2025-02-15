import json
import os
from datetime import datetime

# Caminho dos arquivos de dados
ARQUIVO_VENDAS = "data/vendas.json"
ARQUIVO_PRODUTOS = "data/produtos.json"
PASTA_RELATORIOS = "relatorios"

# Função para carregar as vendas do arquivo JSON
def carregar_vendas():
    if os.path.exists(ARQUIVO_VENDAS):
        with open(ARQUIVO_VENDAS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return []

# Função para carregar os produtos do arquivo JSON
def carregar_produtos():
    if os.path.exists(ARQUIVO_PRODUTOS):
        with open(ARQUIVO_PRODUTOS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return []

# Função para calcular o lucro de uma venda
def calcular_lucro(venda, produtos):
    lucro = 0.0
    for item in venda["itens"]:
        produto = next((p for p in produtos if p["nome"] == item["nome"]), None)
        if produto:
            custo = produto["valor_compra"] * item["quantidade"]
            lucro += item["subtotal"] - custo  # Correção feita aqui
    return lucro

# Função para gerar o relatório de contabilidade
def gerar_relatorio_contabilidade():
    vendas = carregar_vendas()
    produtos = carregar_produtos()
    if not vendas:
        print("\nNenhuma venda registrada. Realize vendas antes de gerar o relatório de contabilidade.")
        return

    # Criar a pasta de relatórios se não existir
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)

    # Definir o nome do arquivo de relatório
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"{PASTA_RELATORIOS}/contabilidade_{data_hora}.txt"

    # Calcular o total de vendas e o lucro
    total_vendas = sum(venda["total"] for venda in vendas)
    total_lucro = sum(calcular_lucro(venda, produtos) for venda in vendas)

    # Gerar o conteúdo do relatório
    conteudo = f"--- Relatório de Contabilidade ---\n"
    conteudo += f"Data e Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    conteudo += f"Total de Vendas: R$ {total_vendas:.2f}\n"
    conteudo += f"Lucro Total: R$ {total_lucro:.2f}\n"
    conteudo += "-" * 30 + "\n"

    # Detalhes das vendas
    conteudo += "\n--- Detalhes das Vendas ---\n"
    for venda in vendas:
        conteudo += f"Cliente: {venda['cliente']}\n"
        conteudo += f"Total da Venda: R$ {venda['total']:.2f}\n"
        conteudo += "Itens:\n"
        for item in venda["itens"]:
            conteudo += f"  - {item['quantidade']}x {item['nome']} (R$ {item['valor_unitario']:.2f} cada)\n"
        conteudo += "-" * 30 + "\n"

    # Salvar o relatório em um arquivo de texto
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)

    print(f"Relatório de contabilidade gerado com sucesso: {nome_arquivo}")

# Executar o programa
if __name__ == "__main__":
    gerar_relatorio_contabilidade()
