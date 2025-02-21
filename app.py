from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, send_file, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import pandas as pd
from io import BytesIO

# Configuração inicial do Flask
app = Flask(__name__)

# Configuração do banco de dados (SQLite como padrão)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lanchonete.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_forte_aqui'

# Configuração do diretório de uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Inicialização do SQLAlchemy
db = SQLAlchemy(app)

# Definição dos modelos do banco de dados
class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_compra = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(100))

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100), nullable=False)
    data_venda = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class ItemVenda(db.Model):
    __tablename__ = 'itens_venda'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    lucro = db.Column(db.Float, nullable=False)

# Função para verificar se um arquivo é permitido
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para salvar uma imagem
def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# Rotas da aplicação

# Rota para a página inicial
@app.route('/')
def home():
    return render_template('index.html')

# Rota para cadastrar um novo produto
@app.route('/cadastrar_produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        valor_compra = request.form.get('valor_compra')
        quantidade = request.form.get('quantidade')

        # Validação dos dados
        if not nome or not preco or not valor_compra or not quantidade:
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('cadastrar_produto'))

        try:
            preco = float(preco)
            valor_compra = float(valor_compra)
            quantidade = int(quantidade)
        except ValueError:
            flash('Valores inválidos. Verifique os campos numéricos.', 'error')
            return redirect(url_for('cadastrar_produto'))

        # Upload da imagem (opcional)
        imagem = None
        if 'imagem' in request.files:
            file = request.files['imagem']
            imagem = save_image(file)

        # Cria o produto
        produto = Produto(nome=nome, preco=preco, valor_compra=valor_compra, quantidade=quantidade, imagem=imagem)
        db.session.add(produto)
        db.session.commit()

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('estoque'))

    return render_template('cadastrar_produto.html')

# Rota para editar um produto
@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    produto = db.session.get(Produto, produto_id)  # Usando db.session.get() em vez de Query.get()
    if not produto:
        flash('Produto não encontrado.', 'error')
        return redirect(url_for('estoque'))

    if request.method == 'POST':
        produto.nome = request.form.get('nome')
        produto.preco = float(request.form.get('preco'))
        produto.valor_compra = float(request.form.get('valor_compra'))
        produto.quantidade = int(request.form.get('quantidade'))

        # Upload da imagem (opcional)
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and allowed_file(file.filename):
                produto.imagem = save_image(file)

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('estoque'))

    return render_template('editar_produto.html', produto=produto)

# Rota para listar produtos no estoque
@app.route('/estoque')
def estoque():
    produtos = Produto.query.all()
    messages = get_flashed_messages(with_categories=True)
    return render_template('estoque.html', produtos=produtos, messages=messages)

# Rota para atualizar o estoque
@app.route('/atualizar_estoque', methods=['POST'])
def atualizar_estoque():
    try:
        for key, value in request.form.items():
            if key.startswith('quantidade_'):
                produto_id = int(key.split('_')[1])
                nova_quantidade = int(value)

                produto = db.session.get(Produto, produto_id)  # Usando db.session.get() em vez de Query.get()
                if produto:
                    produto.quantidade = nova_quantidade
                    db.session.commit()

        flash('Estoque atualizado com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao atualizar estoque: {str(e)}")
        flash('Erro ao atualizar estoque.', 'error')

    return redirect(url_for('estoque'))

# Rota para a página de vendas
@app.route('/vendas')
def vendas():
    produtos = Produto.query.all()
    messages = get_flashed_messages(with_categories=True)
    return render_template('vendas.html', produtos=produtos, messages=messages)

# Rota para finalizar uma venda
@app.route('/finalizar_venda', methods=['POST'])
def finalizar_venda():
    try:
        dados = request.json
        itens_vendidos = dados.get('itens_vendidos', [])
        cliente = dados.get('cliente', '')

        if not itens_vendidos:
            return jsonify({"success": False, "message": "Nenhum item foi vendido."}), 400

        if not cliente:
            return jsonify({"success": False, "message": "Nome do cliente é obrigatório."}), 400

        # Verificar estoque antes de finalizar a venda
        for item in itens_vendidos:
            produto_id = item.get('produto_id')
            quantidade_vendida = item.get('quantidade')

            produto = db.session.get(Produto, produto_id)  # Usando db.session.get() em vez de Query.get()
            if not produto:
                return jsonify({"success": False, "message": f"Produto com ID {produto_id} não encontrado."}), 404

            if produto.quantidade < quantidade_vendida:
                return jsonify({"success": False, "message": f"Estoque insuficiente para o produto {produto.nome}."}), 400

        # Registrar a venda no banco de dados
        venda = Venda(cliente=cliente)
        db.session.add(venda)
        db.session.flush()  # Para obter o ID da venda antes de commit

        for item in itens_vendidos:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade')

            produto = db.session.get(Produto, produto_id)  # Usando db.session.get() em vez de Query.get()
            preco_unitario = produto.preco
            valor_compra = produto.valor_compra
            subtotal = preco_unitario * quantidade
            lucro = (preco_unitario - valor_compra) * quantidade

            item_venda = ItemVenda(
                venda_id=venda.id,
                produto_id=produto_id,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
                subtotal=subtotal,
                lucro=lucro
            )
            db.session.add(item_venda)

        # Atualizar o estoque
        for item in itens_vendidos:
            produto_id = item.get('produto_id')
            quantidade_vendida = item.get('quantidade')

            produto = db.session.get(Produto, produto_id)  # Usando db.session.get() em vez de Query.get()
            produto.quantidade -= quantidade_vendida
            db.session.commit()

        return jsonify({
            "success": True,
            "message": "Venda finalizada e estoque atualizado!",
            "venda_id": venda.id
        }), 200

    except Exception as e:
        print(f"Erro ao finalizar a venda: {str(e)}")
        return jsonify({"success": False, "message": f"Erro ao finalizar a venda: {str(e)}"}), 500

# Rota para gerar relatórios
@app.route('/gerar_relatorio', methods=['GET'])
def gerar_relatorio():
    try:
        tipo_relatorio = request.args.get('tipo', 'vendas')
        periodo = request.args.get('periodo', 'hoje')

        hoje = datetime.now()
        if periodo == 'hoje':
            data_inicio = hoje.strftime('%Y-%m-%d 00:00:00')
            data_fim = hoje.strftime('%Y-%m-%d 23:59:59')
        elif periodo == 'semana':
            data_inicio = (hoje - timedelta(days=7)).strftime('%Y-%m-%d 00:00:00')
            data_fim = hoje.strftime('%Y-%m-%d 23:59:59')
        elif periodo == 'mes':
            data_inicio = (hoje - timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
            data_fim = hoje.strftime('%Y-%m-%d 23:59:59')

        if tipo_relatorio == 'vendas':
            vendas = Venda.query.filter(Venda.data_venda.between(data_inicio, data_fim)).all()
            relatorio = []
            for venda in vendas:
                for item in venda.itens_venda:
                    relatorio.append({
                        'produto': item.produto.nome,
                        'quantidade': item.quantidade,
                        'subtotal': item.subtotal,
                        'lucro': item.lucro,
                        'data_venda': venda.data_venda.strftime('%Y-%m-%d %H:%M:%S')
                    })
            df = pd.DataFrame(relatorio)
        elif tipo_relatorio == 'estoque':
            produtos = Produto.query.all()
            relatorio = [{
                'id': produto.id,
                'nome': produto.nome,
                'estoque_atual': produto.quantidade
            } for produto in produtos]
            df = pd.DataFrame(relatorio)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=f'Relatorio_{tipo_relatorio}')

        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name=f'relatorio_{tipo_relatorio}_{periodo}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"Erro ao gerar relatório: {str(e)}")
        return jsonify({"success": False, "message": f"Erro ao gerar relatório: {str(e)}"}), 500

# Rota para o formulário de relatório
@app.route('/gerar_relatorio_form')
def gerar_relatorio_form():
    return render_template('gerar_relatorio.html')

# Inicializa o servidor Flask
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados se não existirem
    app.run(debug=True)