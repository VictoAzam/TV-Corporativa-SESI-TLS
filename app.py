import json
import os
import platform
import requests
import subprocess
import uuid
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import or_, and_
from werkzeug.utils import secure_filename

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv não encontrado. Instale com: pip install python-dotenv")
    print("⚠️  Usando variáveis de ambiente do sistema...")

app = Flask(__name__)

# Configurações com valores padrão para fallback
app.secret_key = os.getenv('SECRET_KEY', 'S3nh@IFMS')

api_key = os.getenv('API_KEY', '4cd224af1c46c58cf99cdbd798e13931')
city = os.getenv('CITY', 'Três Lagoas, br')
CACHE_FILE = os.getenv('CACHE_FILE', 'clima.json')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dispositivos.db')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


DURACAO_INTERVALO = timedelta(minutes=20)
AVISO_ANTECIPADO = timedelta(minutes=15)  
AVISO_FIM = timedelta(minutes=5)          

HORARIOS_EVENTOS = {
    # Intervalo da manhã: acontece às 9h15 e dura 20 minutos. Ideal para aquele café!
    "primeiro intervalo": {
        'inicio': time(9, 15), 
        'duracao': DURACAO_INTERVALO,
        'tipo': 'intervalo',
        'turno': 'manha'
    },
    # Intervalo da tarde: começa às 15h15, também com 20 minutos. Hora de relaxar um pouco!
    "intervalo da tarde": {
        'inicio': time(15, 15), 
        'duracao': DURACAO_INTERVALO,  # 15:15 às 15:35
        'tipo': 'intervalo',
        'turno': 'tarde'
    },
    # Intervalo da noite: para quem estuda à noite, começa às 21h05.
    "intervalo da noite": {
        'inicio': time(21, 5), 
        'duracao': DURACAO_INTERVALO,  # 21:05 às 21:25
        'tipo': 'intervalo',
        'turno': 'noite'
    },
    # Saídas: horários em que cada turno termina. Fique atento para não perder o horário!
    "saída manhã": {
        'inicio': time(12, 35), 
        'duracao': timedelta(minutes=0),
        'tipo': 'saida',
        'turno': 'manha'
    },
    "saída tarde": {
        'inicio': time(18, 35), 
        'duracao': timedelta(minutes=0),
        'tipo': 'saida',
        'turno': 'tarde'
    },
    "saída noite": {
        'inicio': time(22, 50), 
        'duracao': timedelta(minutes=0),
        'tipo': 'saida',
        'turno': 'noite'
    }
}

def get_turno_atual(hora_atual):
    """
    Função que descobre em qual turno estamos agora, com base no horário.
    Retorna 'manha', 'tarde', 'noite' ou None se estiver fora do horário escolar.
    """
    if time(7, 0) <= hora_atual < time(12, 30):
        return 'manha'
    elif time(13, 0) <= hora_atual < time(18, 50):
        return 'tarde'
    elif time(18, 50) <= hora_atual <= time(23, 59) or time(0, 0) <= hora_atual < time(1, 0):
        return 'noite'
    else:
        return None  # Fora do horário escolar

def get_status_intervalo():
    """
    Esta função verifica o horário atual e retorna o status do próximo evento (intervalo ou saída).
    Ela é útil para mostrar avisos na tela, como "Intervalo em andamento" ou "Saída em 5 minutos".
    """
    agora_dt = datetime.now()
    hoje = agora_dt.date()
    turno_atual = get_turno_atual(agora_dt.time())
  
    # Filtra apenas os eventos do turno atual ou eventos sem turno definido
    eventos_do_turno = {
        nome: detalhes for nome, detalhes in HORARIOS_EVENTOS.items()
        if detalhes.get('turno') == turno_atual or detalhes.get('turno') is None
    }
    
    # Ordena os eventos para garantir que o próximo evento seja identificado corretamente
    eventos_ordenados = sorted(eventos_do_turno.items(), key=lambda item: item[1]['inicio'])
    
    for nome, detalhes in eventos_ordenados:
        inicio_dt = datetime.combine(hoje, detalhes['inicio'])
        fim_dt = inicio_dt + detalhes['duracao']
        
        tempo_para_inicio = inicio_dt - agora_dt
        tempo_para_fim = fim_dt - agora_dt
        
        # CONDIÇÃO 1: Avisar 15 minutos antes do INÍCIO
        if timedelta(seconds=0) <= tempo_para_inicio <= AVISO_ANTECIPADO:
            return {
                "show_aviso": True,
                "mensagem_status": f"{nome.title()}",
                "tempo_restante_segundos": tempo_para_inicio.total_seconds(),
                "tipo_evento": "aviso_inicio",
                "turno": detalhes.get('turno', 'geral')
            }
        
        # CONDIÇÃO 2: DURANTE o intervalo
        if tempo_para_inicio <= timedelta(seconds=0) <= tempo_para_fim and detalhes['tipo'] == 'intervalo':
            # Se faltam 5 minutos ou menos para terminar
            if tempo_para_fim <= AVISO_FIM:
                return {
                    "show_aviso": True,
                    "mensagem_status": f"O intervalo termina em",
                    "tempo_restante_segundos": tempo_para_fim.total_seconds(),
                    "tipo_evento": "fim_intervalo",
                    "turno": detalhes.get('turno', 'geral')
                }
            else:
                return {
                    "show_aviso": True,
                    "mensagem_status": f"Intervalo em andamento",
                    "tempo_restante_segundos": tempo_para_fim.total_seconds(),
                    "tipo_evento": "durante_intervalo",
                    "turno": detalhes.get('turno', 'geral')
                }
        
        # CONDIÇÃO 3: Avisar saída (5 min antes)
        if detalhes['tipo'] == 'saida' and timedelta(seconds=0) <= tempo_para_inicio <= timedelta(minutes=5):
            minutos = int(tempo_para_inicio.total_seconds() // 60)
            return {
                "show_aviso": True,
                "mensagem_status": f"Saída do turno {detalhes.get('turno', '')} em {minutos} minutos",
                "tempo_restante_segundos": tempo_para_inicio.total_seconds(),
                "tipo_evento": "aviso_saida",
                "turno": detalhes.get('turno', 'geral')
            }
    
    # Se chegou aqui, não há avisos ativos para mostrar
    if agora_dt.weekday() >= 5:  # Final de semana
        return {
            "show_aviso": False,
            "mensagem_status": "Bom final de semana!",
            "tempo_restante_segundos": None,
            "tipo_evento": "fim_de_semana",
            "turno": None
        }
    elif turno_atual is None:  # Fora do horário escolar
        return {
            "show_aviso": False,
            "mensagem_status": "Escola fechada - Próximo turno: 7h (manhã)",
            "tempo_restante_segundos": None,
            "tipo_evento": "fora_horario",
            "turno": None
        }
    else:  # Horário normal de aula
        return {
            "show_aviso": False,
            "mensagem_status": f"Aula em andamento - Turno da {turno_atual}",
            "tempo_restante_segundos": None,
            "tipo_evento": "aula_normal",
            "turno": turno_atual
        }

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def fetch_and_cache_weather():
    """
    Busca a previsão do tempo na API e salva em um arquivo local para evitar consultas repetidas.
    Se houver algum erro de rede, mostra uma mensagem no terminal.
    """
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=pt_br'
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        dados_previsao = response.json()
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados_previsao, f, ensure_ascii=False, indent=4)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados do clima: {e}")
        # Adicionar log se necessário


class Dispositivo(db.Model):
    # Modelo que representa cada TV ou painel cadastrado no sistema.
    # Inclui informações como IP, nome, local, status e observações.
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    local = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='ativo')  # ADICIONAR
    observacoes = db.Column(db.Text)  # ADICIONAR
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    ultima_sincronizacao = db.Column(db.DateTime, default=datetime.now)
    ultima_conexao = db.Column(db.DateTime)  # ADICIONAR para testar_dispositivo


class Evento(db.Model):
    # Modelo para eventos que aparecem nas TVs, como avisos, imagens ou vídeos.
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    titulo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(250))
    link = db.Column(db.String(250))
    imagem = db.Column(db.String(250))
    video = db.Column(db.String(250))
    cor_fundo = db.Column(db.String(7), default='#667eea')
    status = db.Column(db.String(20), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    dispositivo = db.relationship('Dispositivo', backref=db.backref('eventos', lazy=True))


class Mensagem_Temporaria(db.Model):
    # Modelo para mensagens temporárias que podem ser exibidas em um dispositivo por tempo limitado.
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    mensagem = db.Column(db.String(250), nullable=True)
    link = db.Column(db.String(250), nullable=True)
    prioridade = db.Column(db.String(20), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    hora_fim = db.Column(db.Time)
    dispositivo = db.relationship('Dispositivo', backref=db.backref('mensagens_temporarias', lazy=True))


class Noticia(db.Model):
    # Modelo para notícias rápidas que aparecem nas TVs.
    id = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('dispositivo.id'), nullable=False)
    conteudo = db.Column(db.String(250), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    data_fim = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)
    dispositivo = db.relationship('Dispositivo', backref=db.backref('noticias', lazy=True))


class Usuario(db.Model, UserMixin):
    # Modelo para usuários do sistema (administração, login, etc).
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)


with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(email='admin@example.com').first():
        admin_user = Usuario(nome='Admin', email='admin@example.com', senha='admin')
        db.session.add(admin_user)
        db.session.commit()
        
    if not Dispositivo.query.first():
        novo_dispositivo = Dispositivo(ip="192.168.0.1", nome="Painel Teste", local="Entrada")
        db.session.add(novo_dispositivo)
        db.session.commit()
    if not Noticia.query.first():
        nova_noticia = Noticia(dispositivo_id=1, conteudo="Sejam bem-vindos!", status="ativa")
        db.session.add(nova_noticia)
        db.session.commit()
    if not Evento.query.first():
        novo_evento = Evento(dispositivo_id=1, titulo="Início das Aulas", descricao="O ano letivo começa hoje.", status="ativo")
        db.session.add(novo_evento)
        db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = Usuario.query.filter_by(email=email).first()
        if user and user.senha == senha:
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for('login'))

@app.route('/testar_sistema')
@login_required
def testar_sistema():
    try:
        # Testar conexão com banco
        usuarios = Usuario.query.count()
        dispositivos = Dispositivo.query.count()
        
        # Testar função de status
        status = get_status_intervalo()
        
        return {
            'status': 'OK',
            'usuarios': usuarios,
            'dispositivos': dispositivos,
            'show_aviso': status['show_aviso'],
            'turno_atual': status.get('turno'),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'status': 'ERRO', 'erro': str(e)}

@app.route("/")
def show_painel():
    noticia = Noticia.query.filter_by(status='ativa').all()
    # Filtra eventos ativos que tenham pelo menos título ou descrição
    evento = Evento.query.filter(
        Evento.status == 'ativo',
        or_(
            and_(Evento.imagem != None, Evento.imagem != ""),
            and_(Evento.video != None, Evento.video != ""),
            and_(Evento.titulo != None, Evento.titulo != ""),
            and_(Evento.descricao != None, Evento.descricao != "")
        )
    ).order_by(Evento.data_inicio.desc()).all()
    
    status_intervalo = get_status_intervalo()
    return render_template(
        "painel.html",
        noticia=noticia,
        evento=evento,
        **status_intervalo
    )


@app.route('/dispositivos')
@login_required
def show_dispositivos():
    dispositivos = Dispositivo.query.all()
    return render_template('dispositivos.html', dispositivos=dispositivos)


# Função auxiliar para validar endereço IP
def validar_ip(ip):
    """
    Valida se o endereço IP está em formato correto.
    Retorna True se válido, False caso contrário.
    """
    if not ip or not isinstance(ip, str):
        return False
    
    try:
        import ipaddress
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False

# Função auxiliar para sanitizar entrada de texto
def sanitizar_texto(texto, max_length=250):
    """
    Remove caracteres perigosos e limita o tamanho do texto.
    Retorna o texto sanitizado.
    """
    if not texto:
        return ""
    
    # Remove caracteres de controle e limita o tamanho
    texto_limpo = ''.join(char for char in str(texto) if ord(char) >= 32 or char in '\n\t')
    return texto_limpo.strip()[:max_length]

# Função auxiliar para validar status
def validar_status(status, valores_validos=['ativo', 'inativo', 'manutencao']):
    """
    Verifica se o status está entre os valores válidos.
    Retorna o status se válido, 'ativo' como padrão caso contrário.
    """
    if not status or status not in valores_validos:
        return 'ativo'  # Valor padrão seguro
    return status


@app.route('/adicionar_dispositivo', methods=['GET', 'POST'])
@login_required
def adicionar_dispositivo():
    if request.method == 'POST':
        # Validação defensiva de entrada
        nome = sanitizar_texto(request.form.get('nome', '').strip(), 50)
        local = sanitizar_texto(request.form.get('local', '').strip(), 50)
        ip = request.form.get('ip', '').strip()
        status = validar_status(request.form.get('status', ''))
        observacoes = sanitizar_texto(request.form.get('observacoes', ''), 500)
        
        # Verificações de segurança básicas
        if not nome:
            flash('Erro: Nome do dispositivo é obrigatório!', 'error')
            return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
        
        if not local:
            flash('Erro: Local do dispositivo é obrigatório!', 'error')
            return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
        
        if not validar_ip(ip):
            flash('Erro: Endereço IP inválido! Use o formato correto (ex: 192.168.1.100)', 'error')
            return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
        
        # Verificar se IP já existe
        try:
            dispositivo_existente = Dispositivo.query.filter_by(ip=ip).first()
            if dispositivo_existente:
                flash('Erro: Já existe um dispositivo com este IP!', 'error')
                return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
        except Exception as e:
            flash(f'Erro ao verificar IP existente: {str(e)}', 'error')
            return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
        
        # Criar novo dispositivo com validação adicional
        try:
            novo_dispositivo = Dispositivo(
                nome=nome,
                local=local,
                ip=ip,
                status=status,
                observacoes=observacoes
            )
            
            db.session.add(novo_dispositivo)
            db.session.commit()
            flash(f'Dispositivo {nome} adicionado com sucesso!', 'success')
            return redirect(url_for('listar_dispositivos'))
            
        except Exception as e:
            db.session.rollback()
            # Log do erro para depuração (em produção, usar logging apropriado)
            print(f"Erro ao adicionar dispositivo: {str(e)}")
            flash('Erro interno do servidor. Tente novamente mais tarde.', 'error')
            return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
    
    return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')

@app.route('/listar_dispositivos')
@login_required
def listar_dispositivos():
    dispositivos = Dispositivo.query.all()
    return render_template('gerenciador_deconteudo/dispositivos.html', dispositivos=dispositivos)

@app.route('/editar_dispositivo/<int:dispositivo_id>', methods=['GET', 'POST'])
@login_required
def editar_dispositivo(dispositivo_id):
    # Validação de entrada básica
    if not isinstance(dispositivo_id, int) or dispositivo_id <= 0:
        return jsonify({
            'sucesso': False, 
            'erro': 'ID do dispositivo inválido!'
        })
    
    dispositivo = Dispositivo.query.get_or_404(dispositivo_id)
    
    if request.method == 'POST':
        # Validação defensiva de entrada
        nome = sanitizar_texto(request.form.get('nome', '').strip(), 50)
        local = sanitizar_texto(request.form.get('local', '').strip(), 50)
        ip = request.form.get('ip', '').strip()
        status = validar_status(request.form.get('status', 'ativo'))
        observacoes = sanitizar_texto(request.form.get('observacoes', ''), 500)
        
        # Verificações de segurança básicas
        if not nome:
            return jsonify({
                'sucesso': False, 
                'erro': 'Nome do dispositivo é obrigatório!'
            })
        
        if not local:
            return jsonify({
                'sucesso': False, 
                'erro': 'Local do dispositivo é obrigatório!'
            })
        
        if not validar_ip(ip):
            return jsonify({
                'sucesso': False, 
                'erro': 'Endereço IP inválido! Use o formato correto (ex: 192.168.1.100)'
            })
        
        # Verificar se IP já existe (exceto no dispositivo atual)
        try:
            dispositivo_existente = Dispositivo.query.filter(
                Dispositivo.ip == ip, 
                Dispositivo.id != dispositivo_id
            ).first()
            
            if dispositivo_existente:
                return jsonify({
                    'sucesso': False, 
                    'erro': 'Já existe um dispositivo com este IP!'
                })
        except Exception as e:
            print(f"Erro ao verificar IP existente: {str(e)}")
            return jsonify({
                'sucesso': False, 
                'erro': 'Erro interno ao verificar dados. Tente novamente.'
            })
        
        try:
            # Atualizar dados do dispositivo com validação
            dispositivo.nome = nome
            dispositivo.local = local
            dispositivo.ip = ip
            dispositivo.status = status
            dispositivo.observacoes = observacoes
            dispositivo.ultima_atualizacao = datetime.now()
            
            db.session.commit()
            return jsonify({
                'sucesso': True, 
                'mensagem': f'Dispositivo {nome} atualizado com sucesso!'
            })
            
        except Exception as e:
            db.session.rollback()
            # Log do erro para depuração (em produção, usar logging apropriado)
            print(f"Erro ao atualizar dispositivo: {str(e)}")
            return jsonify({
                'sucesso': False, 
                'erro': 'Erro interno do servidor. Tente novamente mais tarde.'
            })
    
    # GET - retorna os dados do dispositivo
    return render_template('gerenciador_deconteudo/editar_dispositivo.html', dispositivo=dispositivo)

@app.route('/excluir_dispositivo/<int:dispositivo_id>', methods=['POST'])
@login_required
def excluir_dispositivo(dispositivo_id):
    dispositivo = Dispositivo.query.get_or_404(dispositivo_id)
    
    try:
        # Excluir eventos e notícias relacionados primeiro
        Evento.query.filter_by(dispositivo_id=dispositivo_id).delete()
        Noticia.query.filter_by(dispositivo_id=dispositivo_id).delete()
        Mensagem_Temporaria.query.filter_by(dispositivo_id=dispositivo_id).delete()
        
        # Excluir o dispositivo
        db.session.delete(dispositivo)
        db.session.commit()
        
        return jsonify({
            'sucesso': True, 
            'mensagem': f'Dispositivo {dispositivo.nome} excluído com sucesso!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'sucesso': False, 
            'erro': f'Erro ao excluir dispositivo: {str(e)}'
        })

@app.route('/testar_dispositivo/<ip>')
@login_required
def testar_dispositivo(ip):
    # Validação defensiva do IP
    if not validar_ip(ip):
        return jsonify({
            'sucesso': False, 
            'erro': 'Endereço IP inválido!'
        })
    
    try:
        # Sanitizar o IP para evitar injeção de comandos
        ip_limpo = ip.strip()
        
        # Usar comando ping apropriado para Windows ou Linux com timeout limitado
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', '-w', '3000', ip_limpo], 
                                  capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', ip_limpo], 
                                  capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            # Atualizar última conexão com proteção contra erros
            try:
                dispositivo = Dispositivo.query.filter_by(ip=ip_limpo).first()
                if dispositivo:
                    dispositivo.ultima_conexao = datetime.now()
                    db.session.commit()
            except Exception as db_error:
                print(f"Erro ao atualizar última conexão: {str(db_error)}")
                # Continua mesmo se não conseguir atualizar o banco
            
            return jsonify({'sucesso': True, 'status': 'Online'})
        else:
            return jsonify({'sucesso': False, 'erro': 'Dispositivo não responde ao ping'})
    
    except subprocess.TimeoutExpired:
        return jsonify({'sucesso': False, 'erro': 'Timeout ao testar conexão'})
    except Exception as e:
        print(f"Erro ao testar dispositivo: {str(e)}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno ao testar conexão'})
    
@app.route('/enviar_conteudo/<int:dispositivo_id>')
@login_required
def enviar_conteudo(dispositivo_id):
    dispositivo = Dispositivo.query.get_or_404(dispositivo_id)
    
    # Verificar se o dispositivo está ativo
    if dispositivo.status != 'ativo':
        flash(f'Dispositivo {dispositivo.nome} está inativo. Ative-o primeiro para enviar conteúdo.', 'warning')
        return redirect(url_for('listar_dispositivos'))
    
    # Primeiro, testar se o dispositivo responde
    try:
        # Usar comando ping apropriado para Windows
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', '-w', '3000', dispositivo.ip], 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', dispositivo.ip], 
                                  capture_output=True, text=True)
        
        if result.returncode != 0:
            flash(f'Dispositivo {dispositivo.nome} ({dispositivo.ip}) não está respondendo ao ping. Verifique a conexão.', 'error')
            return redirect(url_for('listar_dispositivos'))
    
    except Exception as e:
        flash(f'Erro ao testar conexão com {dispositivo.nome}: {str(e)}', 'error')
        return redirect(url_for('listar_dispositivos'))
    
    # Se chegou aqui, o dispositivo responde ao ping
    try:
        # Tentar enviar comando HTTP para o Raspberry Pi
        url = f"http://{dispositivo.ip}:5000/atualizar_conteudo"
        data = {
            'pagina': request.args.get('pagina', '/'),
            'comando': request.args.get('comando', 'reload')
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            dispositivo.ultima_conexao = datetime.now()
            db.session.commit()
            flash(f'✅ Conteúdo enviado para {dispositivo.nome} com sucesso!', 'success')
        else:
            flash(f'❌ O dispositivo {dispositivo.nome} respondeu, mas com erro HTTP {response.status_code}', 'error')
    
    except requests.exceptions.ConnectTimeout:
        flash(f'⏱️ Timeout ao conectar com {dispositivo.nome}. O dispositivo pode estar ocupado.', 'warning')
    except requests.exceptions.ConnectionError:
        flash(f'🔌 Falha na conexão com {dispositivo.nome}. Verifique se o serviço está rodando na porta 5000.', 'error')
    except requests.exceptions.RequestException as e:
        flash(f'❌ Erro de rede com {dispositivo.nome}: {str(e)}', 'error')
    except Exception as e:
        flash(f'❌ Erro inesperado ao comunicar com {dispositivo.nome}: {str(e)}', 'error')
    
    return redirect(url_for('listar_dispositivos'))

@app.route("/aviso-intervalo")
def aviso_intervalo():
    noticia = Noticia.query.filter_by(status="ativa").all()
    status_intervalo = get_status_intervalo()
    return render_template('aviso-intervalo.html', noticia=noticia, **status_intervalo)


horarios_agendados = [
    (6, 10), (8, 0), (12, 0), (13, 0), (15, 0),
    (17, 0), (18, 0), (19, 0), (21, 0), (22, 0), (22, 50)
]

scheduler = BackgroundScheduler(daemon=True)
for hora, minuto in horarios_agendados:
    scheduler.add_job(fetch_and_cache_weather, 'cron', hour=hora, minute=minuto)
scheduler.start()


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        dispositivos_ids = request.form.getlist('dispositivos')
        tipo_conteudo = request.form.get('tipo_conteudo')
        
        # Campos de agendamento
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')

        if not dispositivos_ids:
            flash("Você deve selecionar ao menos um dispositivo.", "danger")
            return redirect(url_for('admin'))

        # Processar datas
        data_inicio = None
        data_fim = None
        
        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de início inválido.", "danger")
                return redirect(url_for('admin'))
        
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de fim inválido.", "danger")
                return redirect(url_for('admin'))

        # Processar baseado no tipo de conteúdo com validação defensiva
        if tipo_conteudo == 'noticia':
            # NOTÍCIA RÁPIDA - com sanitização
            conteudo_noticia = request.form.get('conteudo_noticia', '').strip()
            
            if not conteudo_noticia:
                flash("Você deve preencher o texto da notícia rápida.", "danger")
                return redirect(url_for('admin'))
            
            # Sanitizar conteúdo da notícia
            conteudo_limpo = sanitizar_texto(conteudo_noticia, 250)
            
            # Validar tamanho do conteúdo após sanitização
            if len(conteudo_limpo) > 250:
                flash("O texto da notícia é muito longo (máximo 250 caracteres).", "danger")
                return redirect(url_for('admin'))
            
            if len(conteudo_limpo) < 3:
                flash("O texto da notícia é muito curto (mínimo 3 caracteres).", "danger")
                return redirect(url_for('admin'))
            
            # Verificar se já existe uma notícia idêntica nos últimos 5 segundos (prevenção contra duplicação)
            try:
                cinco_segundos_atras = datetime.now() - timedelta(seconds=5)
                noticia_recente = Noticia.query.filter(
                    Noticia.conteudo == conteudo_limpo,
                    Noticia.data_inicio >= cinco_segundos_atras
                ).first()
                
                if noticia_recente:
                    flash("Esta notícia já foi criada recentemente.", "warning")
                    return redirect(url_for('admin'))
            except Exception as e:
                print(f"Erro ao verificar notícias duplicadas: {str(e)}")
                # Continua mesmo se a verificação falhar
            
            # Processar cada dispositivo com validação
            for id_dispositivo in dispositivos_ids:
                try:
                    # Validar se o ID é um número válido
                    dispositivo_id = int(id_dispositivo)
                    if dispositivo_id <= 0:
                        flash(f"ID de dispositivo inválido: {id_dispositivo}", "danger")
                        return redirect(url_for('admin'))
                    
                    # Validar se o dispositivo existe
                    dispositivo = Dispositivo.query.get(dispositivo_id)
                    if not dispositivo:
                        flash(f"Dispositivo ID {dispositivo_id} não foi encontrado.", "danger")
                        return redirect(url_for('admin'))
                except (ValueError, TypeError):
                    flash(f"ID de dispositivo inválido: {id_dispositivo}", "danger")
                    return redirect(url_for('admin'))
                
                nova_noticia = Noticia(
                    conteudo=conteudo_limpo,
                    status="ativa",
                    dispositivo_id=int(id_dispositivo),
                    data_inicio=data_inicio or datetime.now(),
                    data_fim=data_fim
                )
                db.session.add(nova_noticia)
        
        elif tipo_conteudo in ['imagem', 'video']:
            # EVENTO COM IMAGEM OU VÍDEO
            if tipo_conteudo == 'imagem':
                titulo_evento = request.form.get('titulo_evento_imagem')
                descricao_evento = request.form.get('descricao_evento_imagem')
            else:  # tipo_conteudo == 'video'
                titulo_evento = request.form.get('titulo_evento_video')
                descricao_evento = request.form.get('descricao_evento_video')
            
            link_qrcode = request.form.get('link_qrcode')
            cor_fundo = request.form.get('cor_fundo', '#667eea')  # Cor padrão se não especificada
            
            # Validação: título é obrigatório
            if not titulo_evento or not titulo_evento.strip():
                flash("Você deve preencher o título do evento.", "danger")
                return redirect(url_for('admin'))
            
            titulo_final = titulo_evento.strip()
            descricao_final = descricao_evento.strip() if descricao_evento else ""
            
            # Processamento de arquivo (imagem ou vídeo)
            arquivo_filename = None
            
            if tipo_conteudo == 'imagem':
                if 'imagem' in request.files:
                    file = request.files['imagem']
                    if file and file.filename != '':
                        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(upload_folder, unique_filename)
                        file.save(file_path)
                        arquivo_filename = f"uploads/{unique_filename}"
                    
                # VALIDAÇÃO: Para eventos do tipo "imagem", deve ter pelo menos descrição OU imagem
                if not descricao_final and not arquivo_filename:
                    flash("Para eventos com imagem, você deve preencher pelo menos a descrição ou enviar uma imagem.", "danger")
                    return redirect(url_for('admin'))
            
            elif tipo_conteudo == 'video':
                if 'video' in request.files:
                    file = request.files['video']
                    if file and file.filename != '':
                        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        file_path = os.path.join(upload_folder, unique_filename)
                        file.save(file_path)
                        arquivo_filename = f"uploads/{unique_filename}"
                    else:
                        flash("Você deve selecionar um vídeo.", "danger")
                        return redirect(url_for('admin'))
                else:
                    flash("Você deve selecionar um vídeo.", "danger")
                    return redirect(url_for('admin'))
            
            # Verificar se já existe um evento idêntico nos últimos 5 segundos (prevenção contra duplicação)
            cinco_segundos_atras = datetime.now() - timedelta(seconds=5)
            evento_recente = Evento.query.filter(
                Evento.titulo == titulo_final,
                Evento.data_inicio >= cinco_segundos_atras
            ).first()
            
            if evento_recente:
                flash("Este evento já foi criado recentemente.", "warning")
                return redirect(url_for('admin'))
            
            # Criar evento para cada dispositivo
            for id_dispositivo in dispositivos_ids:
                novo_evento = Evento(
                    dispositivo_id=id_dispositivo,
                    titulo=titulo_final,
                    descricao=descricao_final,
                    link=link_qrcode.strip() if link_qrcode else "",
                    imagem=arquivo_filename if tipo_conteudo == 'imagem' else "",
                    video=arquivo_filename if tipo_conteudo == 'video' else "",
                    cor_fundo=cor_fundo,
                    status="ativo",
                    data_inicio=data_inicio or datetime.now(),
                    data_fim=data_fim
                )
                db.session.add(novo_evento)
        
        else:
            flash("Tipo de conteúdo inválido.", "danger")
            return redirect(url_for('admin'))
        
        try:
            db.session.commit()
            flash("Conteúdo adicionado com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar no banco de dados: {str(e)}", "danger")
            
        return redirect(url_for('admin'))

    # GET request - mostrar a página
    dispositivos = Dispositivo.query.order_by(Dispositivo.nome).all()
    noticias = Noticia.query.filter_by(status='ativa').all()
    eventos = Evento.query.filter_by(status='ativo').all()
    
    return render_template(
        "gerenciador_deconteudo/adicionar_conteudo.html", 
        dispositivos=dispositivos,
        noticias=noticias,
        eventos=eventos
    )


@app.route('/publicacoes_ativas')
@login_required
def publicacoes_ativas():
    # Buscar todas as notícias e eventos ativos
    noticias_raw = Noticia.query.filter_by(status='ativa').all()  # Corrigido: notícias usam 'ativa'
    eventos_raw = Evento.query.filter_by(status='ativo').all()    # Eventos usam 'ativo'
    
    # Agrupar notícias por conteúdo
    noticias_agrupadas = {}
    for noticia in noticias_raw:
        key = (noticia.conteudo, noticia.data_inicio, noticia.data_fim)
        if key not in noticias_agrupadas:
            noticias_agrupadas[key] = {
                'noticia': noticia,
                'dispositivos': []
            }
        noticias_agrupadas[key]['dispositivos'].append(noticia.dispositivo)
    
    # Agrupar eventos por título, descrição, imagem e vídeo
    eventos_agrupados = {}
    for evento in eventos_raw:
        key = (evento.titulo, evento.descricao, evento.imagem, evento.video, evento.data_inicio, evento.data_fim)
        if key not in eventos_agrupados:
            eventos_agrupados[key] = {
                'evento': evento,
                'dispositivos': []
            }
        eventos_agrupados[key]['dispositivos'].append(evento.dispositivo)
    
    # Converter para listas
    noticias_finais = list(noticias_agrupadas.values())
    eventos_finais = list(eventos_agrupados.values())
    
    return render_template(
        "gerenciador_deconteudo/publicacoes_ativas.html", 
        noticias=noticias_finais,
        eventos=eventos_finais
    )


@app.route('/excluir_noticia/<int:id>', methods=['POST'])
@login_required
def excluir_noticia(id):
    noticia = Noticia.query.get_or_404(id)
    
    # Buscar todas as notícias com o mesmo conteúdo e período
    noticias_similares = Noticia.query.filter(
        Noticia.conteudo == noticia.conteudo,
        Noticia.data_inicio == noticia.data_inicio,
        Noticia.data_fim == noticia.data_fim,
        Noticia.status == 'ativa'
    ).all()
    
    # Excluir todas as notícias similares (de todas as TVs)
    for noticia_similar in noticias_similares:
        db.session.delete(noticia_similar)
    
    db.session.commit()
    flash(f"Notícia excluída de {len(noticias_similares)} TV(s) com sucesso!", "success")
    return redirect(url_for('publicacoes_ativas'))

@app.route('/excluir_evento/<int:id>', methods=['POST'])
@login_required
def excluir_evento(id):
    evento = Evento.query.get_or_404(id)
    
    # Buscar todos os eventos similares (mesmo título, descrição, imagem, vídeo e período)
    eventos_similares = Evento.query.filter(
        Evento.titulo == evento.titulo,
        Evento.descricao == evento.descricao,
        Evento.imagem == evento.imagem,
        Evento.video == evento.video,
        Evento.data_inicio == evento.data_inicio,
        Evento.data_fim == evento.data_fim,
        Evento.status == 'ativo'
    ).all()
    
    # Remover arquivos apenas uma vez (eles são compartilhados)
    if evento.imagem:
        arquivo_path = os.path.join(app.root_path, 'static', evento.imagem)
        if os.path.exists(arquivo_path):
            try:
                os.remove(arquivo_path)
            except Exception as e:
                pass  # Silenciar erro ao remover arquivo
    
    if evento.video:
        arquivo_path = os.path.join(app.root_path, 'static', evento.video)
        if os.path.exists(arquivo_path):
            try:
                os.remove(arquivo_path)
            except Exception as e:
                pass  # Silenciar erro ao remover arquivo
    
    # Excluir todos os eventos similares (de todas as TVs)
    for evento_similar in eventos_similares:
        db.session.delete(evento_similar)
    
    db.session.commit()
    flash(f"Evento excluído de {len(eventos_similares)} TV(s) com sucesso!", "success")
    return redirect(url_for('publicacoes_ativas'))

@app.route('/excluir_mensagem/<int:id>', methods=['POST'])
@login_required
def excluir_mensagem(id):
    mensagem = Mensagem_Temporaria.query.get_or_404(id)
    
    # Remover eventos QR relacionados (que começam com "QR Code -")
    eventos_qr = Evento.query.filter(
        Evento.titulo.like('QR Code -%'),
        Evento.data_inicio == mensagem.data_inicio,
        Evento.dispositivo_id == mensagem.dispositivo_id
    ).all()
    
    for evento_qr in eventos_qr:
        db.session.delete(evento_qr)
    
    # Remover arquivo de imagem se existir
    if mensagem.link:
        arquivo_path = os.path.join(app.root_path, 'static', mensagem.link)
        if os.path.exists(arquivo_path):
            os.remove(arquivo_path)
    
    db.session.delete(mensagem)
    db.session.commit()
    flash("Mensagem e QR Code relacionado excluídos com sucesso!", "success")
    return redirect(url_for('admin'))

@app.route('/clima')
def clima():
    status_intervalo = get_status_intervalo()
    clima_data = None
    erro_msg = None
    noticia = Noticia.query.all()
    evento = Evento.query.all()
    noticia = Noticia.query.all()
    evento = Evento.query.all()

    if not os.path.exists(CACHE_FILE):
        erro_msg = "Dados do clima ainda não disponíveis. Aguardando a primeira busca."
    else:
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                dados_previsao = json.load(f)

            primeira_previsao = dados_previsao['list'][0]
            clima_data = {
                'cidade': dados_previsao['city']['name'],
                'temperatura': f"{primeira_previsao['main']['temp']:.0f}",
                'condicao': primeira_previsao['weather'][0]['description'].capitalize(),
                'chance_chuva': int(primeira_previsao['pop'] * 100),
                'vento': round(primeira_previsao['wind']['speed'] * 3.6, 1),
                'icone': primeira_previsao['weather'][0]['icon'],
            }
        except (IOError, json.JSONDecodeError, KeyError) as e:
            erro_msg = "Ocorreu um erro ao carregar os dados do clima."
            
    return render_template(
        'clima.html',
        clima=clima_data,
        erro=erro_msg,
        noticia=noticia,
        evento=evento,
        **status_intervalo
    )


@app.route('/configurar_dispositivo_exemplo')
@login_required 
def configurar_dispositivo_exemplo():
    """Rota para ajudar a configurar o dispositivo de exemplo"""
    dispositivo_exemplo = Dispositivo.query.filter_by(ip='192.168.0.1').first()
    
    if dispositivo_exemplo:
        # Redirecionar para edição do dispositivo
        return redirect(url_for('editar_dispositivo', dispositivo_id=dispositivo_exemplo.id))
    else:
        flash('Dispositivo de exemplo não encontrado.', 'info')
        return redirect(url_for('listar_dispositivos'))

# Rotas para edição de publicações
@app.route('/editar_noticia/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_noticia(id):
    noticia = Noticia.query.get_or_404(id)
    
    if request.method == 'POST':
        conteudo_noticia = request.form.get('conteudo_noticia')
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')
        
        if not conteudo_noticia or conteudo_noticia.strip() == '':
            flash("Você deve preencher o texto da notícia rápida.", "danger")
            return redirect(url_for('editar_noticia', id=id))
        
        conteudo_limpo = conteudo_noticia.strip()
        
        if len(conteudo_limpo) > 250:
            flash("O texto da notícia é muito longo (máximo 250 caracteres).", "danger")
            return redirect(url_for('editar_noticia', id=id))
        
        # Processar datas
        data_inicio = None
        data_fim = None
        
        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de início inválido.", "danger")
                return redirect(url_for('editar_noticia', id=id))
        
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de fim inválido.", "danger")
                return redirect(url_for('editar_noticia', id=id))
        
        # Obter dispositivos selecionados
        dispositivos_selecionados = request.form.getlist('dispositivos')
        
        if not dispositivos_selecionados:
            flash("Você deve selecionar pelo menos uma TV.", "danger")
            return redirect(url_for('editar_noticia', id=id))
        
        # Remover todas as notícias similares existentes
        noticias_para_remover = Noticia.query.filter(
            Noticia.conteudo == noticia.conteudo,
            Noticia.data_inicio == noticia.data_inicio,
            Noticia.data_fim == noticia.data_fim,
            Noticia.status == 'ativa'
        ).all()
        
        for not_rem in noticias_para_remover:
            db.session.delete(not_rem)
        
        # Criar novas notícias para os dispositivos selecionados
        for dispositivo_id in dispositivos_selecionados:
            nova_noticia = Noticia(
                conteudo=conteudo_limpo,
                data_inicio=data_inicio or datetime.now(),
                data_fim=data_fim,
                dispositivo_id=int(dispositivo_id),
                status='ativa'
            )
            db.session.add(nova_noticia)
        
        try:
            db.session.commit()
            flash(f"Notícia atualizada em {len(dispositivos_selecionados)} TV(s) com sucesso!", "success")
            return redirect(url_for('publicacoes_ativas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar notícia: {str(e)}", "danger")
    
    # Para GET, buscar dispositivos disponíveis e selecionados
    dispositivos = Dispositivo.query.all()
    
    # Buscar quais dispositivos têm esta notícia
    dispositivos_com_noticia = db.session.query(Dispositivo.id).join(Noticia).filter(
        Noticia.conteudo == noticia.conteudo,
        Noticia.data_inicio == noticia.data_inicio,
        Noticia.data_fim == noticia.data_fim,
        Noticia.status == 'ativa'
    ).all()
    dispositivos_selecionados = [d.id for d in dispositivos_com_noticia]
    
    return render_template('gerenciador_deconteudo/editar_noticia.html', 
                         noticia=noticia, 
                         dispositivos=dispositivos,
                         dispositivos_selecionados=dispositivos_selecionados)

@app.route('/editar_evento_imagem/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_evento_imagem(id):
    evento = Evento.query.get_or_404(id)
    
    if request.method == 'POST':
        titulo_evento = request.form.get('titulo_evento_imagem')
        descricao_evento = request.form.get('descricao_evento_imagem')
        link_qrcode = request.form.get('link_qrcode')
        cor_fundo = request.form.get('cor_fundo', '#667eea')
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')
        
        if not titulo_evento or not titulo_evento.strip():
            flash("Você deve preencher o título do evento.", "danger")
            return redirect(url_for('editar_evento_imagem', id=id))
        
        titulo_final = titulo_evento.strip()
        descricao_final = descricao_evento.strip() if descricao_evento else ""
        
        # Processar datas
        data_inicio = None
        data_fim = None
        
        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de início inválido.", "danger")
                return redirect(url_for('editar_evento_imagem', id=id))
        
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de fim inválido.", "danger")
                return redirect(url_for('editar_evento_imagem', id=id))
        
        # Processamento de nova imagem (opcional)
        arquivo_filename = evento.imagem  # Manter imagem atual por padrão
        
        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename != '':
                # Remover imagem antiga se existir
                if evento.imagem:
                    arquivo_path_antigo = os.path.join(app.root_path, 'static', evento.imagem)
                    if os.path.exists(arquivo_path_antigo):
                        try:
                            os.remove(arquivo_path_antigo)
                        except Exception as e:
                            pass  # Silenciar erro ao remover arquivo
                
                # Salvar nova imagem
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                arquivo_filename = f"uploads/{unique_filename}"
        
        # Validação: Para eventos do tipo "imagem", deve ter pelo menos descrição OU imagem
        if not descricao_final and not arquivo_filename:
            flash("Para eventos com imagem, você deve preencher pelo menos a descrição ou enviar uma imagem.", "danger")
            return redirect(url_for('editar_evento_imagem', id=id))
        
        # Obter dispositivos selecionados
        dispositivos_selecionados = request.form.getlist('dispositivos')
        
        if not dispositivos_selecionados:
            flash("Você deve selecionar pelo menos uma TV.", "danger")
            return redirect(url_for('editar_evento_imagem', id=id))
        
        # Remover todos os eventos similares existentes
        eventos_para_remover = Evento.query.filter(
            Evento.titulo == evento.titulo,
            Evento.descricao == evento.descricao,
            Evento.imagem == evento.imagem,
            Evento.video == evento.video,
            Evento.data_inicio == evento.data_inicio,
            Evento.data_fim == evento.data_fim,
            Evento.status == 'ativo'
        ).all()
        
        for ev in eventos_para_remover:
            db.session.delete(ev)
        
        # Criar novos eventos para os dispositivos selecionados
        for dispositivo_id in dispositivos_selecionados:
            novo_evento = Evento(
                titulo=titulo_final,
                descricao=descricao_final,
                link=link_qrcode.strip() if link_qrcode else "",
                imagem=arquivo_filename,
                cor_fundo=cor_fundo,
                data_inicio=data_inicio or datetime.now(),
                data_fim=data_fim,
                dispositivo_id=int(dispositivo_id),
                status='ativo'
            )
            db.session.add(novo_evento)
        
        try:
            db.session.commit()
            flash(f"Evento atualizado em {len(dispositivos_selecionados)} TV(s) com sucesso!", "success")
            return redirect(url_for('publicacoes_ativas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar evento: {str(e)}", "danger")
    
    # Para GET, buscar dispositivos disponíveis e selecionados
    dispositivos = Dispositivo.query.all()
    
    # Buscar quais dispositivos têm este evento
    dispositivos_com_evento = db.session.query(Dispositivo.id).join(Evento).filter(
        Evento.titulo == evento.titulo,
        Evento.descricao == evento.descricao,
        Evento.imagem == evento.imagem,
        Evento.status == 'ativo'
    ).all()
    dispositivos_selecionados = [d.id for d in dispositivos_com_evento]
    
    return render_template('gerenciador_deconteudo/editar_evento_imagem.html', 
                         evento=evento, 
                         dispositivos=dispositivos,
                         dispositivos_selecionados=dispositivos_selecionados)

@app.route('/editar_evento_video/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_evento_video(id):
    evento = Evento.query.get_or_404(id)
    
    if request.method == 'POST':
        titulo_evento = request.form.get('titulo_evento_video')
        descricao_evento = request.form.get('descricao_evento_video')
        link_qrcode = request.form.get('link_qrcode')
        data_inicio_str = request.form.get('data_inicio')
        data_fim_str = request.form.get('data_fim')
        
        if not titulo_evento or not titulo_evento.strip():
            flash("Você deve preencher o título do evento.", "danger")
            return redirect(url_for('editar_evento_video', id=id))
        
        titulo_final = titulo_evento.strip()
        descricao_final = descricao_evento.strip() if descricao_evento else ""
        
        # Processar datas
        data_inicio = None
        data_fim = None
        
        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de início inválido.", "danger")
                return redirect(url_for('editar_evento_video', id=id))
        
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Formato de data de fim inválido.", "danger")
                return redirect(url_for('editar_evento_video', id=id))
        
        # Processamento de novo vídeo (opcional)
        arquivo_filename = evento.video  # Manter vídeo atual por padrão
        
        if 'video' in request.files:
            file = request.files['video']
            if file and file.filename != '':
                # Remover vídeo antigo se existir
                if evento.video:
                    arquivo_path_antigo = os.path.join(app.root_path, 'static', evento.video)
                    if os.path.exists(arquivo_path_antigo):
                        try:
                            os.remove(arquivo_path_antigo)
                        except Exception as e:
                            pass  # Silenciar erro ao remover arquivo
                
                # Salvar novo vídeo
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                arquivo_filename = f"uploads/{unique_filename}"
        
        # Validação: vídeo é obrigatório
        if not arquivo_filename:
            flash("Você deve manter ou selecionar um vídeo.", "danger")
            return redirect(url_for('editar_evento_video', id=id))
        
        # Obter dispositivos selecionados
        dispositivos_selecionados = request.form.getlist('dispositivos')
        
        if not dispositivos_selecionados:
            flash("Você deve selecionar pelo menos uma TV.", "danger")
            return redirect(url_for('editar_evento_video', id=id))
        
        # Remover todos os eventos similares existentes
        eventos_para_remover = Evento.query.filter(
            Evento.titulo == evento.titulo,
            Evento.descricao == evento.descricao,
            Evento.imagem == evento.imagem,
            Evento.video == evento.video,
            Evento.data_inicio == evento.data_inicio,
            Evento.data_fim == evento.data_fim,
            Evento.status == 'ativo'
        ).all()
        
        for ev in eventos_para_remover:
            db.session.delete(ev)
        
        # Criar novos eventos para os dispositivos selecionados
        for dispositivo_id in dispositivos_selecionados:
            novo_evento = Evento(
                titulo=titulo_final,
                descricao=descricao_final,
                link=link_qrcode.strip() if link_qrcode else "",
                video=arquivo_filename,
                data_inicio=data_inicio or datetime.now(),
                data_fim=data_fim,
                dispositivo_id=int(dispositivo_id),
                status='ativo'
            )
            db.session.add(novo_evento)
        
        try:
            db.session.commit()
            flash(f"Evento atualizado em {len(dispositivos_selecionados)} TV(s) com sucesso!", "success")
            return redirect(url_for('publicacoes_ativas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar evento: {str(e)}", "danger")
    
    # Para GET, buscar dispositivos disponíveis e selecionados
    dispositivos = Dispositivo.query.all()
    
    # Buscar quais dispositivos têm este evento
    dispositivos_com_evento = db.session.query(Dispositivo.id).join(Evento).filter(
        Evento.titulo == evento.titulo,
        Evento.descricao == evento.descricao,
        Evento.video == evento.video,
        Evento.status == 'ativo'
    ).all()
    dispositivos_selecionados = [d.id for d in dispositivos_com_evento]
    
    return render_template('gerenciador_deconteudo/editar_evento_video.html', 
                         evento=evento, 
                         dispositivos=dispositivos,
                         dispositivos_selecionados=dispositivos_selecionados)

if __name__ == '__main__':
    with app.app_context():
        fetch_and_cache_weather()
    app.run(debug=True, use_reloader=False)-