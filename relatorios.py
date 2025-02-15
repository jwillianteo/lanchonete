import json
import os
from datetime import datetime

# Caminho dos arquivos de dados
ARQUIVO_PRODUTOS = "data/produtos.json"
PASTA_RELATORIOS = "relatorios"

# Função para carregar os produtos do arquivo JSON
def carregar_produtos():
    if os.path.exists(ARQUIVO_PRODUTOS):
        with open(ARQUIVO_PRODUTOS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return []

# Função para gerar o relatório de saldo
def gerar_relatorio_saldo(tipo):
    produtos = carregar_produtos()
    if not produtos:
        print("\nNenhum produto cadastrado. Cadastre produtos antes de gerar relatórios.")
        return

    # Criar a pasta de relatórios se não existir
    if not os.path.exists(PASTA_RELATORIOS):
        os.makedirs(PASTA_RELATORIOS)

    # Definir o nome do arquivo de relatório
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"{PASTA_RELATORIOS}/saldo_{tipo}_{data_hora}.txt"

    # Gerar o conteúdo do relatório
    conteudo = f"--- Relatório de Saldo {tipo.capitalize()} ---\n"
    conteudo += f"Data e Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    for produto in produtos:
        conteudo += f"Produto: {produto['nome']}\n"
        conteudo += f"Quantidade: {produto['quantidade']}\n"
        conteudo += f"Valor de Venda: R$ {produto['valor_venda']:.2f}\n"
        conteudo += "-" * 30 + "\n"

    # Salvar o relatório em um arquivo de texto
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)

    print(f"Relatório de saldo {tipo} gerado com sucesso: {nome_arquivo}")

# Menu principal
def menu():
    while True:
        print("\n--- Menu de Relatórios ---")
        print("1. Gerar relatório de saldo inicial")
        print("2. Gerar relatório de saldo final")
        print("3. Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            gerar_relatorio_saldo("inicial")
        elif opcao == "2":
            gerar_relatorio_saldo("final")
        elif opcao == "3":
            print("Saindo...")
            break
        else:
            print("Opção inválida. Tente novamente.")

# Executar o programa
if __name__ == "__main__":
    menu()