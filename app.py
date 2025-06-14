from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask (__name__)
app.secret_key = 'uma_chave_muito_secreta_aqui'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dispositivos.db'

db = SQLAlchemy(app)

class Dispositivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(50), nullable=False)
    # status = db.Column(db.String(20))
    # mensagem = db.Column(db.String(250), nullable=False)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    ultima_sincronizacao = db.Column(db.DateTime, default=datetime.now)

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    titulo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(250), nullable=False)
    link = db.Column(db.String(250))
    imagem = db.Column(db.String(250))
    status = db.Column(db.String(20), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    
    dispositivo = db.relationship('Dispositivo', backref=db.backref('eventos', lazy=True))
    
class Mensagem_Temporaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    mensagem = db.Column(db.String(250), nullable=True)
    link = db.Column(db.String(250), nullable=True)
    prioridade = db.Column(db.String(20), nullable=False)
    data_inicio= db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    hora_fim = db.Column(db.Time)
    
    dispositivo = db.relationship('Dispositivo', backref=db.backref('mensagens_temporarias', lazy=True))

class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    conteudo = db.Column(db.String(250), nullable=False)
    data_inicio= db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)
    
    dispositivo = db.relationship('Dispositivo', backref=db.backref('noticias', lazy=True))
    
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

  
with app.app_context():
    db.drop_all() #para limpar o banco(so nos testes)
    db.create_all()

with app.app_context():
    nova_noticia = Noticia(
        dispositivo_id=1,  # Use an existing dispositivo_id
        conteudo="Esta é uma notícia de teste para o painel.",
        data_inicio=datetime.now(),
        data_fim=None,
        status="ativa"
    )
    db.session.add(nova_noticia)
    db.session.commit()

with app.app_context():
    novo_dispositivo = Dispositivo(
        ip="192.168.0.10",
        nome="TV Sala",
        local="Sala Principal"
    )
    db.session.add(novo_dispositivo)
    db.session.commit()
    
with app.app_context():
    novo_evento = Evento(
        dispositivo_id=1,  # Use um ID válido
        titulo="Evento com Imagem",
        descricao="Este evento tem uma imagem separada.",
        link="https://exemplo.com",  # ou outro link relevante
        imagem="/static/images/partiuif.png",  # Caminho da imagem
        status="ativo",
        data_inicio=datetime.now(),
        data_fim=None
    )
    db.session.add(novo_evento)
    db.session.commit()
    
@app.route("/")
def show_painel():
    noticia = Noticia.query.all()
    evento = Evento.query.all()
    return render_template("painel.html", noticia=noticia, evento = evento)

@app.route('/dispositivos')
def show_dispositivos():
    dispositivos = Dispositivo.query.all()
    return render_template('dispositivos.html', dispositivos=dispositivos)

@app.route('/adicionar_dispositivo', methods=["GET",'POST'])
def adicionar_dispositivo():
    if request.method == "POST":
        ip = request.form["ip"]
        if Dispositivo.query.filter_by(ip=ip).first():
            flash("Já existe um dispositivo com esse IP!", "error")
            return render_template("adicionar_dispositivo.html")
        novo_dispositivo = Dispositivo(
            nome=request.form["nome"],
            local=request.form["local"],
            ip=ip,
            # status=request.form["status"],
            # mensagem=request.form["mensagem"],
            ultima_atualizacao=datetime.now(),
            ultima_sincronizacao=datetime.now()
        )
        db.session.add(novo_dispositivo)
        db.session.commit()
        return redirect("/")
    return render_template("adicionar_dispositivo.html")

if __name__ == '__main__':
    app.run(debug=True)