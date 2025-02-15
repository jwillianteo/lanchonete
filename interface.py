from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                           QTableWidget, QTableWidgetItem, QMessageBox, 
                           QTabWidget, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ajuste das importações para refletir a estrutura de pastas do projeto
from Lanchonete.vendas import SistemaVendas
from Lanchonete.cadastro_produtos import CadastroProdutos

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Lanchonete")
        self.setGeometry(100, 100, 800, 600)
        
        # Inicializa os sistemas
        self.sistema_vendas = SistemaVendas()
        self.cadastro = CadastroProdutos()
        
        # Cria as tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Cria as páginas
        self.tab_vendas = QWidget()
        self.tab_produtos = QWidget()
        self.tab_relatorios = QWidget()
        
        # Adiciona as tabs
        self.tabs.addTab(self.tab_vendas, "Vendas")
        self.tabs.addTab(self.tab_produtos, "Produtos")
        self.tabs.addTab(self.tab_relatorios, "Relatórios")
        
        # Configura cada tab
        self.setup_vendas_tab()
        self.setup_produtos_tab()
        self.setup_relatorios_tab()

    def setup_vendas_tab(self):
        layout = QVBoxLayout()
        
        # Área do cliente
        cliente_layout = QHBoxLayout()
        self.cliente_input = QLineEdit()
        self.cliente_input.setPlaceholderText("Nome do Cliente")
        self.iniciar_venda_btn = QPushButton("Iniciar Venda")
        self.iniciar_venda_btn.clicked.connect(self.iniciar_venda)
        cliente_layout.addWidget(self.cliente_input)
        cliente_layout.addWidget(self.iniciar_venda_btn)
        
        # Tabela de produtos disponíveis
        produtos_label = QLabel("Produtos Disponíveis")
        produtos_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.produtos_table = QTableWidget()
        self.produtos_table.setColumnCount(5)
        self.produtos_table.setHorizontalHeaderLabels(["ID", "Nome", "Preço", "Estoque", "Quantidade"])
        
        # Tabela do carrinho
        carrinho_label = QLabel("Carrinho")
        carrinho_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.carrinho_table = QTableWidget()
        self.carrinho_table.setColumnCount(4)
        self.carrinho_table.setHorizontalHeaderLabels(["Nome", "Quantidade", "Preço Unit.", "Subtotal"])
        
        # Botões de ação
        botoes_layout = QHBoxLayout()
        self.adicionar_btn = QPushButton("Adicionar ao Carrinho")
        self.adicionar_btn.clicked.connect(self.adicionar_ao_carrinho)
        self.finalizar_btn = QPushButton("Finalizar Venda")
        self.finalizar_btn.clicked.connect(self.finalizar_venda)
        self.cancelar_btn = QPushButton("Cancelar Venda")
        self.cancelar_btn.clicked.connect(self.cancelar_venda)
        
        botoes_layout.addWidget(self.adicionar_btn)
        botoes_layout.addWidget(self.finalizar_btn)
        botoes_layout.addWidget(self.cancelar_btn)
        
        # Total
        self.total_label = QLabel("Total: R$ 0.00")
        self.total_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_label.setAlignment(Qt.AlignRight)
        
        # Adiciona todos os widgets ao layout
        layout.addLayout(cliente_layout)
        layout.addWidget(produtos_label)
        layout.addWidget(self.produtos_table)
        layout.addWidget(carrinho_label)
        layout.addWidget(self.carrinho_table)
        layout.addLayout(botoes_layout)
        layout.addWidget(self.total_label)
        
        self.tab_vendas.setLayout(layout)
        self.atualizar_tabela_produtos()

    def setup_produtos_tab(self):
        layout = QVBoxLayout()
        
        # Formulário de cadastro
        form_layout = QVBoxLayout()
        
        # Nome
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome do Produto")
        
        # Preço de compra
        self.preco_compra = QDoubleSpinBox()
        self.preco_compra.setPrefix("R$ ")
        self.preco_compra.setMaximum(1000.00)
        
        # Preço de venda
        self.preco_venda = QDoubleSpinBox()
        self.preco_venda.setPrefix("R$ ")
        self.preco_venda.setMaximum(1000.00)
        
        # Quantidade
        self.quantidade = QSpinBox()
        self.quantidade.setMaximum(1000)
        
        # Botão cadastrar
        self.cadastrar_btn = QPushButton("Cadastrar Produto")
        self.cadastrar_btn.clicked.connect(self.cadastrar_produto)
        
        # Lista de produtos
        self.lista_produtos = QTableWidget()
        self.lista_produtos.setColumnCount(5)
        self.lista_produtos.setHorizontalHeaderLabels(
            ["ID", "Nome", "Preço Compra", "Preço Venda", "Quantidade"]
        )
        
        # Adiciona widgets ao layout
        form_layout.addWidget(QLabel("Nome do Produto:"))
        form_layout.addWidget(self.nome_input)
        form_layout.addWidget(QLabel("Preço de Compra:"))
        form_layout.addWidget(self.preco_compra)
        form_layout.addWidget(QLabel("Preço de Venda:"))
        form_layout.addWidget(self.preco_venda)
        form_layout.addWidget(QLabel("Quantidade:"))
        form_layout.addWidget(self.quantidade)
        form_layout.addWidget(self.cadastrar_btn)
        
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Produtos Cadastrados:"))
        layout.addWidget(self.lista_produtos)
        
        self.tab_produtos.setLayout(layout)
        self.atualizar_lista_produtos()

    def setup_relatorios_tab(self):
        layout = QVBoxLayout()
        
        # Botões para diferentes tipos de relatórios
        self.vendas_dia_btn = QPushButton("Vendas do Dia")
        self.vendas_dia_btn.clicked.connect(self.mostrar_vendas_dia)
        
        self.estoque_btn = QPushButton("Relatório de Estoque")
        self.estoque_btn.clicked.connect(self.mostrar_estoque)
        
        # Tabela para exibir relatórios
        self.relatorios_table = QTableWidget()
        
        layout.addWidget(self.vendas_dia_btn)
        layout.addWidget(self.estoque_btn)
        layout.addWidget(self.relatorios_table)
        
        self.tab_relatorios.setLayout(layout)

    # Métodos de funcionalidade
    def iniciar_venda(self):
        cliente = self.cliente_input.text()
        if cliente:
            sucesso, msg = self.sistema_vendas.iniciar_venda(cliente)
            if sucesso:
                self.atualizar_tabela_produtos()
                QMessageBox.information(self, "Sucesso", msg)
            else:
                QMessageBox.warning(self, "Erro", msg)
        else:
            QMessageBox.warning(self, "Erro", "Digite o nome do cliente!")

    def atualizar_tabela_produtos(self):
        produtos = self.cadastro.listar_produtos()
        self.produtos_table.setRowCount(len(produtos))
        
        for i, produto in enumerate(produtos):
            self.produtos_table.setItem(i, 0, QTableWidgetItem(str(produto['id'])))
            self.produtos_table.setItem(i, 1, QTableWidgetItem(produto['nome']))
            self.produtos_table.setItem(i, 2, QTableWidgetItem(f"R$ {produto['valor_venda']:.2f}"))
            self.produtos_table.setItem(i, 3, QTableWidgetItem(str(produto['quantidade'])))
            
            # Adiciona SpinBox para quantidade
            qtd_spin = QSpinBox()
            qtd_spin.setMaximum(produto['quantidade'])
            qtd_spin.setMinimum(1)
            self.produtos_table.setCellWidget(i, 4, qtd_spin)

    def adicionar_ao_carrinho(self):
        row = self.produtos_table.currentRow()
        if row >= 0:
            id_produto = int(self.produtos_table.item(row, 0).text())
            quantidade = self.produtos_table.cellWidget(row, 4).value()
            
            sucesso, msg = self.sistema_vendas.adicionar_ao_carrinho(id_produto, quantidade)
            if sucesso:
                self.atualizar_carrinho()
                QMessageBox.information(self, "Sucesso", msg)
            else:
                QMessageBox.warning(self, "Erro", msg)

    def atualizar_carrinho(self):
        carrinho = self.sistema_vendas.carrinho
        self.carrinho_table.setRowCount(len(carrinho))
        
        for i, item in enumerate(carrinho):
            self.carrinho_table.setItem(i, 0, QTableWidgetItem(item['nome']))
            self.carrinho_table.setItem(i, 1, QTableWidgetItem(str(item['quantidade'])))
            self.carrinho_table.setItem(i, 2, QTableWidgetItem(f"R$ {item['valor_unitario']:.2f}"))
            self.carrinho_table.setItem(i, 3, QTableWidgetItem(f"R$ {item['subtotal']:.2f}"))
        
        total = self.sistema_vendas.calcular_total()
        self.total_label.setText(f"Total: R$ {total:.2f}")

    def finalizar_venda(self):
        sucesso, msg = self.sistema_vendas.finalizar_venda()
        if sucesso:
            self.atualizar_tabela_produtos()
            self.atualizar_carrinho()
            QMessageBox.information(self, "Sucesso", msg)
        else:
            QMessageBox.warning(self, "Erro", msg)

    def cancelar_venda(self):
        self.sistema_vendas.cancelar_venda()
        self.atualizar_carrinho()
        QMessageBox.information(self, "Cancelado", "Venda cancelada com sucesso!")

    def cadastrar_produto(self):
        nome = self.nome_input.text()
        preco_compra = self.preco_compra.value()
        preco_venda = self.preco_venda.value()
        quantidade = self.quantidade.value()
        
        if nome and preco_compra > 0 and preco_venda > 0 and quantidade > 0:
            sucesso, msg = self.cadastro.cadastrar_produto(nome, preco_compra, preco_venda, quantidade)
            if sucesso:
                self.atualizar_lista_produtos()
                QMessageBox.information(self, "Sucesso", msg)
            else:
                QMessageBox.warning(self, "Erro", msg)
        else:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos corretamente!")

    def atualizar_lista_produtos(self):
        produtos = self.cadastro.listar_produtos()
        self.lista_produtos.setRowCount(len(produtos))
        
        for i, produto in enumerate(produtos):
            self.lista_produtos.setItem(i, 0, QTableWidgetItem(str(produto['id'])))
            self.lista_produtos.setItem(i, 1, QTableWidgetItem(produto['nome']))
            self.lista_produtos.setItem(i, 2, QTableWidgetItem(f"R$ {produto['preco_compra']:.2f}"))
            self.lista_produtos.setItem(i, 3, QTableWidgetItem(f"R$ {produto['preco_venda']:.2f}"))
            self.lista_produtos.setItem(i, 4, QTableWidgetItem(str(produto['quantidade'])))

    def mostrar_vendas_dia(self):
        # Exemplo de implementação, você pode adaptar conforme seu sistema
        relatorio = self.sistema_vendas.gerar_relatorio_vendas_dia()
        self.relatorios_table.setRowCount(len(relatorio))
        for i, venda in enumerate(relatorio):
            self.relatorios_table.setItem(i, 0, QTableWidgetItem(venda['id']))
            self.relatorios_table.setItem(i, 1, QTableWidgetItem(venda['cliente']))
            self.relatorios_table.setItem(i, 2, QTableWidgetItem(f"R$ {venda['total']:.2f}"))

    def mostrar_estoque(self):
        # Exemplo de implementação, você pode adaptar conforme seu sistema
        relatorio = self.cadastro.gerar_relatorio_estoque()
        self.relatorios_table.setRowCount(len(relatorio))
        for i, produto in enumerate(relatorio):
            self.relatorios_table.setItem(i, 0, QTableWidgetItem(str(produto['id'])))
            self.relatorios_table.setItem(i, 1, QTableWidgetItem(produto['nome']))
            self.relatorios_table.setItem(i, 2, QTableWidgetItem(f"R$ {produto['preco_venda']:.2f}"))
            self.relatorios_table.setItem(i, 3, QTableWidgetItem(str(produto['quantidade'])))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
