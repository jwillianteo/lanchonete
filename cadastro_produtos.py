from flask import Flask, render_template, request, redirect, url_for
from cadastro_produtos import CadastroProdutos  # Importar sua classe

app = Flask(__name__)
cadastro = CadastroProdutos()  # Instancia da classe CadastroProdutos

@app.route('/cadastrar-produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if request.method == 'POST':
        # Coletar os dados do formulário
        nome = request.form['nome']
        caminho_imagem = request.form['caminho_imagem']
        valor_compra = float(request.form['valor_compra'])
        valor_venda = float(request.form['valor_venda'])
        quantidade = int(request.form['quantidade'])

        # Chamar a função para cadastrar o produto
        sucesso, mensagem = cadastro.cadastrar_produto(
            nome, caminho_imagem, valor_compra, valor_venda, quantidade
        )
        
        # Retornar o feedback para o usuário
        if sucesso:
            return redirect(url_for('home'))
        else:
            return render_template('cadastrar_produto.html', mensagem=mensagem)

    return render_template('cadastrar_produto.html')

@app.route('/')
def home():
    return render_template('index.html')  # Tela principal

if __name__ == "__main__":
    app.run(debug=True)
