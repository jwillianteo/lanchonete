import json
import os
from datetime import datetime
from Lanchonete.cadastro_produtos import CadastroProdutos

class SistemaVendas:
    def __init__(self):
        self.cadastro = CadastroProdutos()
        self.arquivo_vendas = 'data/vendas.json'
        self.vendas = self.carregar_vendas()
        self.carrinho = []
        self.cliente_atual = None

    def carregar_vendas(self):
        """Carrega as vendas do arquivo JSON ou retorna lista vazia se não existir"""
        try:
            with open(self.arquivo_vendas, 'r', encoding='utf-8') as arquivo:
                return json.load(arquivo)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def salvar_vendas(self):
        """Salva a lista de vendas no arquivo JSON"""
        with open(self.arquivo_vendas, 'w', encoding='utf-8') as arquivo:
            json.dump(self.vendas, arquivo, indent=4, ensure_ascii=False)

    def iniciar_venda(self, nome_cliente):
        """Inicia uma nova venda para um cliente"""
        if self.carrinho:
            return False, "Existe uma venda em andamento. Finalize ou cancele primeiro."
        
        self.cliente_atual = nome_cliente
        self.carrinho = []
        return True, "Venda iniciada para " + nome_cliente

    def adicionar_ao_carrinho(self, id_produto, quantidade=1):
        """Adiciona um produto ao carrinho"""
        if not self.cliente_atual:
            return False, "Inicie uma venda primeiro!"

        produto = self.cadastro.buscar_produto(id_produto)
        if not produto:
            return False, "Produto não encontrado!"

        if produto['quantidade'] < quantidade:
            return False, "Quantidade insuficiente em estoque!"

        # Verifica se o produto já está no carrinho
        for item in self.carrinho:
            if item['id'] == id_produto:
                nova_qtd = item['quantidade'] + quantidade
                if produto['quantidade'] >= nova_qtd:
                    item['quantidade'] = nova_qtd
                    item['subtotal'] = nova_qtd * produto['valor_venda']
                    return True, "Quantidade atualizada no carrinho!"
                return False, "Quantidade insuficiente em estoque!"

        # Adiciona novo item ao carrinho
        item_carrinho = {
            'id': produto['id'],
            'nome': produto['nome'],
            'quantidade': quantidade,
            'valor_unitario': produto['valor_venda'],
            'subtotal': quantidade * produto['valor_venda']
        }
        self.carrinho.append(item_carrinho)
        return True, "Produto adicionado ao carrinho!"

    def remover_do_carrinho(self, id_produto):
        """Remove um produto do carrinho"""
        for i, item in enumerate(self.carrinho):
            if item['id'] == id_produto:
                self.carrinho.pop(i)
                return True, "Produto removido do carrinho!"
        return False, "Produto não encontrado no carrinho!"

    def calcular_total(self):
        """Calcula o total da venda"""
        return sum(item['subtotal'] for item in self.carrinho)

    def finalizar_venda(self):
        """Finaliza a venda atual"""
        if not self.carrinho:
            return False, "Não há itens no carrinho!"

        # Atualiza o estoque
        for item in self.carrinho:
            produto = self.cadastro.buscar_produto(item['id'])
            nova_quantidade = produto['quantidade'] - item['quantidade']
            self.cadastro.atualizar_quantidade(item['id'], nova_quantidade)

        # Registra a venda
        venda = {
            'id': len(self.vendas) + 1,
            'cliente': self.cliente_atual,
            'itens': self.carrinho,
            'total': self.calcular_total(),
            'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.vendas.append(venda)
        self.salvar_vendas()

        # Limpa o carrinho
        self.carrinho = []
        self.cliente_atual = None

        return True, f"Venda finalizada! Total: R$ {venda['total']:.2f}"

    def cancelar_venda(self):
        """Cancela a venda atual"""
        self.carrinho = []
        self.cliente_atual = None
        return True, "Venda cancelada!"

    def listar_vendas_do_dia(self):
        """Lista todas as vendas do dia atual"""
        hoje = datetime.now().strftime('%Y-%m-%d')
        vendas_do_dia = [
            venda for venda in self.vendas 
            if venda['data'].startswith(hoje)
        ]
        return vendas_do_dia

def menu_vendas():
    sistema = SistemaVendas()
    
    while True:
        print("\n=== Sistema de Vendas ===")
        print("1. Iniciar nova venda")
        print("2. Adicionar produto ao carrinho")
        print("3. Remover produto do carrinho")
        print("4. Ver carrinho")
        print("5. Finalizar venda")
        print("6. Cancelar venda")
        print("7. Ver vendas do dia")
        print("8. Voltar")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == "1":
            nome_cliente = input("Nome do cliente: ")
            sucesso, msg = sistema.iniciar_venda(nome_cliente)
            print(msg)

        elif opcao == "2":
            # Mostra produtos disponíveis
            print("\nProdutos disponíveis:")
            produtos = sistema.cadastro.listar_produtos()
            for produto in produtos:
                print(f"ID: {produto['id']} - {produto['nome']} - Qtd: {produto['quantidade']} - R$ {produto['valor_venda']:.2f}")
            
            id_produto = int(input("\nID do produto: "))
            quantidade = int(input("Quantidade: "))
            sucesso, msg = sistema.adicionar_ao_carrinho(id_produto, quantidade)
            print(msg)

        elif opcao == "3":
            id_produto = int(input("ID do produto para remover: "))
            sucesso, msg = sistema.remover_do_carrinho(id_produto)
            print(msg)

        elif opcao == "4":
            if not sistema.carrinho:
                print("Carrinho vazio!")
            else:
                print("\n=== Carrinho ===")
                for item in sistema.carrinho:
                    print(f"{item['nome']} - {item['quantidade']}x R$ {item['valor_unitario']:.2f} = R$ {item['subtotal']:.2f}")
                print(f"\nTotal: R$ {sistema.calcular_total():.2f}")

        elif opcao == "5":
            sucesso, msg = sistema.finalizar_venda()
            print(msg)

        elif opcao == "6":
            sucesso, msg = sistema.cancelar_venda()
            print(msg)

        elif opcao == "7":
            vendas = sistema.listar_vendas_do_dia()
            if not vendas:
                print("Nenhuma venda hoje!")
            else:
                total_dia = 0
                for venda in vendas:
                    print(f"\nVenda #{venda['id']} - Cliente: {venda['cliente']}")
                    for item in venda['itens']:
                        print(f"- {item['nome']}: {item['quantidade']}x R$ {item['valor_unitario']:.2f}")
                    print(f"Total: R$ {venda['total']:.2f}")
                    total_dia += venda['total']
                print(f"\nTotal do dia: R$ {total_dia:.2f}")

        elif opcao == "8":
            break

        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu_vendas()