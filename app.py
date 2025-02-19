from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, get_flashed_messages, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import json
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configuração da chave secreta
app.secret_key = os.getenv('SECRET_KEY', 'sua_chave_secreta_muito_forte_aqui')

# Configuração do diretório de uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configuração do SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definição dos modelos
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
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filename

# Função para atualizar um produto
def atualizar_produto(produto_id, nome, preco, quantidade, valor_compra, imagem):
    produto = Produto.query.get(produto_id)
    if produto:
        produto.nome = nome
        produto.preco = preco
        produto.quantidade = quantidade
        produto.valor_compra = valor_compra
        produto.imagem = imagem
        db.session.commit()
        return produto
    return None

# Função para registrar uma venda no banco de dados
def registrar_venda(cliente, itens_vendidos):
    try:
        venda = Venda(cliente=cliente)
        db.session.add(venda)
        db.session.flush()  # Para obter o ID da venda antes de commit

        for item in itens_vendidos:
            produto_id = item['produto_id']
            quantidade = item['quantidade']
            
            produto = Produto.query.get(produto_id)
            if not produto:
                raise Exception(f"Produto com ID {produto_id} não encontrado")
            
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
        
        db.session.commit()
        return venda.id
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar venda: {str(e)}")
        raise e

# Função para gerar o relatório de estoque
def gerar_relatorio_estoque():
    hoje = datetime.now().strftime('%Y-%m-%d')
    produtos = Produto.query.all()
    relatorio = []
    for produto in produtos:
        estoque_anterior = produto.quantidade + sum(
            item.quantidade for item in ItemVenda.query.join(Venda).filter(
                ItemVenda.produto_id == produto.id,
                Venda.data_venda >= hoje
            ).all()
        )
        relatorio.append({
            'id': produto.id,
            'nome': produto.nome,
            'estoque_anterior': estoque_anterior,
            'estoque_atual': produto.quantidade
        })
    return relatorio

# Função para gerar o relatório de vendas
def gerar_relatorio_vendas(data_inicio, data_fim):
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
    return relatorio

# Rota para a página inicial
@app.route('/')
def home():
    return render_template('index.html')

# Rota para o formulário de relatório
@app.route('/gerar_relatorio_form')
def gerar_relatorio_form():
    return render_template('gerar_relatorio.html')

# Rota para gerar relatório
@app.route('/gerar_relatorio', methods=['GET'])
def gerar_relatorio():
    try:
        tipo_relatorio = request.args.get('tipo', 'vendas')
        periodo = request.args.get('periodo', 'hoje')
        
        if tipo_relatorio not in ['vendas', 'estoque']:
            return jsonify({"success": False, "message": "Tipo de relatório inválido."}), 400

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
        
        print(f"Gerando relatório {tipo_relatorio} para o período de {data_inicio} até {data_fim}")
        
        if tipo_relatorio == 'vendas':
            dados = gerar_relatorio_vendas(data_inicio, data_fim)
            print(f"Dados encontrados para vendas: {dados}")
            if dados:
                df = pd.DataFrame(dados)
                df['data_venda'] = pd.to_datetime(df['data_venda']).dt.strftime('%d/%m/%Y %H:%M')
                df = df.round(2)
                
                total_row = pd.DataFrame([{
                    'produto': 'TOTAL',
                    'quantidade': df['quantidade'].sum(),
                    'subtotal': df['subtotal'].sum(),
                    'lucro': df['lucro'].sum(),
                    'data_venda': ''
                }])
                df = pd.concat([df, total_row], ignore_index=True)
            else:
                df = pd.DataFrame(columns=['produto', 'quantidade', 'subtotal', 'lucro', 'data_venda'])
                
        elif tipo_relatorio == 'estoque':
            dados = gerar_relatorio_estoque()
            print(f"Dados encontrados para estoque: {dados}")
            if dados:
                df = pd.DataFrame(dados)
                df = df.round(2)
            else:
                df = pd.DataFrame(columns=['id', 'nome', 'estoque_anterior', 'estoque_atual'])

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=f'Relatorio_{tipo_relatorio}')
            
            workbook = writer.book
            worksheet = writer.sheets[f'Relatorio_{tipo_relatorio}']
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#CCCCCC',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
        
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

# Rota para atualizar estoque
@app.route('/atualizar_estoque', methods=['POST'])
def atualizar_estoque():
    try:
        for key, value in request.form.items():
            if key.startswith('quantidade_'):
                produto_id = int(key.split('_')[1])
                nova_quantidade = int(value)
                
                produto = Produto.query.get(produto_id)
                if produto:
                    produto.quantidade = nova_quantidade
                    db.session.commit()
        
        flash('Estoque atualizado com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao atualizar estoque: {str(e)}")
        flash('Erro ao atualizar estoque.', 'error')
    
    return redirect(url_for('estoque'))

# Rota para cadastrar um novo produto
@app.route('/cadastrar_produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if request.method == 'POST':
        try:
            nome = request.form.get("nome")
            preco = request.form.get("preco")
            valor_compra = request.form.get("valor_compra")
            quantidade = request.form.get("quantidade", 0)

            if not nome or not preco or not valor_compra:
                flash("Todos os campos são obrigatórios.", "error")
                return redirect(url_for('cadastrar_produto'))

            try:
                preco = float(preco)
                valor_compra = float(valor_compra)
                quantidade = int(quantidade)
            except ValueError as e:
                flash("Valores numéricos inválidos.", "error")
                return redirect(url_for('cadastrar_produto'))

            imagem = None
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and allowed_file(file.filename):
                    imagem = save_image(file)
                elif file.filename:
                    flash("Tipo de arquivo não permitido.", "error")
                    return redirect(url_for('cadastrar_produto'))

            produto = Produto(
                nome=nome,
                preco=preco,
                quantidade=quantidade,
                valor_compra=valor_compra,
                imagem=imagem
            )
            db.session.add(produto)
            db.session.commit()
            flash("Produto cadastrado com sucesso!", "success")
            return redirect(url_for('estoque'))
        except Exception as e:
            print(f"Erro inesperado: {str(e)}")
            flash("Erro interno no servidor. Tente novamente.", "error")
            return redirect(url_for('cadastrar_produto'))
    return render_template('cadastrar_produto.html')

# Rota para a página de estoque
@app.route('/estoque')
def estoque():
    produtos = Produto.query.all()
    messages = get_flashed_messages(with_categories=True)
    return render_template('estoque.html', produtos=produtos, messages=messages)

# Rota para deletar produto
@app.route('/deletar-produto/<int:produto_id>', methods=['POST'])
def deletar_produto_route(produto_id):
    try:
        produto = Produto.query.get(produto_id)
        if produto:
            db.session.delete(produto)
            db.session.commit()
            flash("Produto removido com sucesso!", "success")
        else:
            flash("Produto não encontrado.", "error")
    except Exception as e:
        print(f"Erro ao deletar produto: {str(e)}")
        flash("Erro ao deletar produto.", "error")
    
    return redirect(url_for('estoque'))

# Rota para a página de vendas
@app.route('/vendas')
def vendas():
    produtos = Produto.query.all()
    messages = get_flashed_messages(with_categories=True)
    return render_template('vendas.html', produtos=produtos, messages=messages)

# Rota para finalizar a venda e subtrair o estoque
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

            produto = Produto.query.get(produto_id)
            if not produto:
                return jsonify({"success": False, "message": f"Produto com ID {produto_id} não encontrado."}), 404

            if produto.quantidade < quantidade_vendida:
                return jsonify({"success": False, "message": f"Estoque insuficiente para o produto {produto.nome}."}), 400

        # Registrar a venda no banco de dados
        try:
            venda_id = registrar_venda(cliente, itens_vendidos)
        except Exception as e:
            return jsonify({"success": False, "message": f"Erro ao registrar venda: {str(e)}"}), 500

        # Atualizar o estoque
        for item in itens_vendidos:
            produto_id = item.get('produto_id')
            quantidade_vendida = item.get('quantidade')

            produto = Produto.query.get(produto_id)
            produto.quantidade -= quantidade_vendida
            db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Venda finalizada e estoque atualizado!",
            "venda_id": venda_id,
            "clear_marked_sales": True  # Adiciona um flag para limpar vendas marcadas no frontend
        }), 200

    except Exception as e:
        print(f"Erro ao finalizar a venda: {str(e)}")
        return jsonify({"success": False, "message": f"Erro ao finalizar a venda: {str(e)}"}), 500

# Rota para servir arquivos de uploads
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para servir arquivos estáticos (imagens, CSS, etc.)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Rotas da API REST
@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    produtos = Produto.query.all()
    return jsonify([{
        'id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'quantidade': produto.quantidade,
        'valor_compra': produto.valor_compra,
        'imagem': produto.imagem
    } for produto in produtos])

@app.route('/api/produtos/<int:produto_id>', methods=['GET'])
def get_produto(produto_id):
    produto = Produto.query.get(produto_id)
    if produto:
        return jsonify({
            'id': produto.id,
            'nome': produto.nome,
            'preco': produto.preco,
            'quantidade': produto.quantidade,
            'valor_compra': produto.valor_compra,
            'imagem': produto.imagem
        })
    return jsonify({"erro": "Produto não encontrado"}), 404

@app.route('/api/produtos', methods=['POST'])
def post_produto():
    try:
        dados = request.get_json()
        if not all(key in dados for key in ['nome', 'preco', 'valor_compra', 'quantidade']):
            return jsonify({"erro": "Campos obrigatórios faltando"}), 400

        try:
            nome = str(dados['nome'])
            preco = float(dados['preco'])
            valor_compra = float(dados['valor_compra'])
            quantidade = int(dados['quantidade'])
        except ValueError as e:
            return jsonify({"erro": "Valores inválidos fornecidos"}), 400

        produto = Produto(
            nome=nome,
            preco=preco,
            quantidade=quantidade,
            valor_compra=valor_compra,
            imagem=dados.get('imagem')
        )
        db.session.add(produto)
        db.session.commit()

        return jsonify({
            'id': produto.id,
            'nome': produto.nome,
            'preco': produto.preco,
            'quantidade': produto.quantidade,
            'valor_compra': produto.valor_compra,
            'imagem': produto.imagem
        }), 201

    except Exception as e:
        print(f"Erro ao adicionar produto via API: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor"}), 500

# Rota para atualizar um produto via API
@app.route('/api/produtos/<int:produto_id>', methods=['PUT'])
def put_produto(produto_id):
    try:
        dados = request.get_json()

        produto = Produto.query.get(produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        produto.nome = dados.get('nome', produto.nome)
        produto.preco = float(dados.get('preco', produto.preco))
        produto.valor_compra = float(dados.get('valor_compra', produto.valor_compra))
        produto.quantidade = int(dados.get('quantidade', produto.quantidade))
        produto.imagem = dados.get('imagem', produto.imagem)

        db.session.commit()

        return jsonify({
            'id': produto.id,
            'nome': produto.nome,
            'preco': produto.preco,
            'quantidade': produto.quantidade,
            'valor_compra': produto.valor_compra,
            'imagem': produto.imagem
        }), 200

    except Exception as e:
        print(f"Erro ao atualizar produto via API: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor"}), 500

# Rota para deletar um produto via API
@app.route('/api/produtos/<int:produto_id>', methods=['DELETE'])
def delete_produto_api(produto_id):
    try:
        produto = Produto.query.get(produto_id)
        if produto:
            db.session.delete(produto)
            db.session.commit()
            return jsonify({"mensagem": "Produto deletado com sucesso"}), 200
        else:
            return jsonify({"erro": "Produto não encontrado"}), 404
    except Exception as e:
        print(f"Erro ao deletar produto via API: {str(e)}")
        return jsonify({"erro": "Erro interno no servidor"}), 500

# Inicializa o servidor Flask
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados se não existirem
    app.run(debug=True)