import json
import os
import platform
import re
import requests
import subprocess
import uuid
import ipaddress
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

api_key = os.getenv('API_KEY', '0326938873afe9a65f6c965706c4ada4')
city = os.getenv('CITY', 'Três Lagoas, br')
CACHE_FILE = os.getenv('CACHE_FILE', 'clima.json')

# Debug das configurações de clima
print("🌤️  Configurações de clima:")
print(f"   🔑 API Key: {api_key[:10]}..." if api_key else "   ❌ API Key não configurada")
print(f"   🏙️  Cidade: {city}")
print(f"   📁 Arquivo cache: {CACHE_FILE}")

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dispositivos.db')
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# =====================================================
# CONFIGURAÇÕES DE HORÁRIOS ESCOLARES - PROGRAMAÇÃO DEFENSIVA
# =====================================================
# Configurações centralizadas para facilitar manutenção
AVISO_ANTECIPADO = timedelta(minutes=15)  # Avisar 15 min antes dos eventos
AVISO_FIM = timedelta(minutes=5)          # Avisar 5 min antes do fim
AVISO_ENTRADA = timedelta(minutes=15)     # Avisar 15 min antes da entrada
AVISO_SAIDA = timedelta(minutes=15)        # Avisar 15 min antes da saída

# Validação de configurações
try:
    assert AVISO_ANTECIPADO.total_seconds() > 0, "AVISO_ANTECIPADO deve ser positivo"
    assert AVISO_FIM.total_seconds() > 0, "AVISO_FIM deve ser positivo"
    assert AVISO_ENTRADA.total_seconds() > 0, "AVISO_ENTRADA deve ser positivo"
    assert AVISO_SAIDA.total_seconds() > 0, "AVISO_SAIDA deve ser positivo"
except AssertionError as e:
    print(f"⚠️ ERRO DE CONFIGURAÇÃO: {e}")
    # Valores padrão seguros
    AVISO_ANTECIPADO = timedelta(minutes=15)
    AVISO_FIM = timedelta(minutes=5)
    AVISO_ENTRADA = timedelta(minutes=15)
    AVISO_SAIDA = timedelta(minutes=15)

def validar_horario_evento(horario_dict):
    """
    Função de programação defensiva para validar configurações de horários.
    Retorna True se válido, False caso contrário.
    """
    try:
        if not isinstance(horario_dict, dict):
            return False
        
        campos_obrigatorios = ['inicio', 'duracao', 'tipo', 'turno']
        for campo in campos_obrigatorios:
            if campo not in horario_dict:
                return False
        
        # Validar tipos
        if not isinstance(horario_dict['inicio'], time):
            return False
        if not isinstance(horario_dict['duracao'], timedelta):
            return False
        if horario_dict['tipo'] not in ['intervalo', 'entrada', 'saida', 'evento']:
            return False
        if horario_dict['turno'] not in ['manha', 'tarde', 'noite', None]:
            return False
            
        # Validar lógica de duração
        if horario_dict['duracao'].total_seconds() < 0:
            return False
            
        return True
    except Exception as e:
        print(f"⚠️ Erro na validação de horário: {e}")
        return False

# Horários atualizados conforme informações da escola
HORARIOS_EVENTOS = {
    # ========== ENTRADAS ==========
    "entrada geral": {
        'inicio': time(7, 0),
        'duracao': timedelta(minutes=0),
        'tipo': 'entrada',
        'turno': 'manha',
        'descricao': 'Entrada para todos os alunos'
    },
    
    "inicio contraturno": {
        'inicio': time(14, 0),
        'duracao': timedelta(minutes=0),
        'tipo': 'entrada',
        'turno': 'tarde',
        'descricao': 'Início do Contraturno'
    },
    
    # ========== INTERVALOS MANHÃ ==========
    "intervalo fund1 manha": {
        'inicio': time(8, 20), 
        'duracao': timedelta(minutes=35),  # 08h20 às 08h55
        'tipo': 'intervalo',
        'turno': 'manha',
        'descricao': 'Intervalo Fundamental I - Manhã'
    },
    
    "intervalo fund2 medio manha": {
        'inicio': time(9, 30), 
        'duracao': timedelta(minutes=15),  # 09h30 às 09h45
        'tipo': 'intervalo',
        'turno': 'manha',
        'descricao': 'Intervalo Fundamental II e Médio - Manhã'
    },
    
    # ========== INTERVALOS TARDE ========== 
    "intervalo contraturno tarde": {
        'inicio': time(14, 0), 
        'duracao': timedelta(minutes=30),  # 14h00 às 14h30
        'tipo': 'intervalo',
        'turno': 'tarde',
        'descricao': 'Intervalo Contraturno - Tarde'
    },
    "intervalo fund1 tarde": {
        'inicio': time(14, 40), 
        'duracao': timedelta(minutes=15),  # 14h40 às 14h55
        'tipo': 'intervalo',
        'turno': 'tarde',
        'descricao': 'Intervalo Fundamental I - Tarde'
    },
    
    "intervalo fund2 tarde": {
        'inicio': time(15, 30), 
        'duracao': timedelta(minutes=15),  # 15h30 às 15h45
        'tipo': 'intervalo',
        'turno': 'tarde',
        'descricao': 'Intervalo Fundamental II - Tarde'
    },
    
    # ========== SAÍDAS ==========
    "saida educacao infantil": {
        'inicio': time(11, 15),
        'duracao': timedelta(minutes=0),
        'tipo': 'saida',
        'turno': 'manha',
        'descricao': 'Saída Educação Infantil'
    },
    
    "saida fundamental1": {
        'inicio': time(11, 25),
        'duracao': timedelta(minutes=0),
        'tipo': 'saida',
        'turno': 'manha',
        'descricao': 'Saída Fundamental I'
    },
    
    "saida fundamental2 medio": {
        'inicio': time(12, 15),
        'duracao': timedelta(minutes=0),
        'tipo': 'saida',
        'turno': 'manha',
        'descricao': 'Saída Fundamental II e Ensino Médio'
    }
}

# Validação defensiva dos horários configurados
print("🔍 Validando configurações de horários...")
horarios_validos = {}
for nome, config in HORARIOS_EVENTOS.items():
    if validar_horario_evento(config):
        horarios_validos[nome] = config
        print(f"✅ Horário '{nome}' validado com sucesso")
    else:
        print(f"❌ Horário '{nome}' possui configuração inválida - IGNORADO")

# Substituir pela versão validada
HORARIOS_EVENTOS = horarios_validos
print(f"✅ {len(HORARIOS_EVENTOS)} horários válidos carregados")

def get_turno_atual(hora_atual):
    """
    Função que descobre em qual turno estamos agora, com base no horário.
    Retorna 'manha', 'tarde', 'noite' ou None se estiver fora do horário escolar.
    """
    if time(7, 0) <= hora_atual < time(12, 30):
        return 'manha'
    elif time(13, 0) <= hora_atual < time(18, 50):  # Tarde começa às 13h00
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
    try:
        agora_dt = datetime.now()
        hoje = agora_dt.date()
        turno_atual = get_turno_atual(agora_dt.time())
        
        # DEBUG: Log do horário atual e turno
        print(f"🕐 DEBUG - Horário atual: {agora_dt.strftime('%H:%M:%S')}")
        print(f"📚 DEBUG - Turno atual: {turno_atual}")
      
        # Validação defensiva - verificar se temos horários configurados
        if not HORARIOS_EVENTOS:
            print("⚠️ ERRO: Nenhum horário de evento configurado")
            return {
                "show_aviso": False,
                "mensagem_status": "Sistema sem horários configurados",
                "tempo_restante_segundos": None,
                "tipo_evento": "erro_configuracao",
                "turno": None
            }
        
        # Filtra apenas os eventos do turno atual ou eventos sem turno definido
        eventos_do_turno = {
            nome: detalhes for nome, detalhes in HORARIOS_EVENTOS.items()
            if detalhes.get('turno') == turno_atual or detalhes.get('turno') is None
        }
        
        print(f"📅 DEBUG - Eventos do turno '{turno_atual}': {list(eventos_do_turno.keys())}")
        
        # Ordena os eventos para garantir que o próximo evento seja identificado corretamente
        eventos_ordenados = sorted(eventos_do_turno.items(), key=lambda item: item[1]['inicio'])
        
        for nome, detalhes in eventos_ordenados:
            try:
                inicio_dt = datetime.combine(hoje, detalhes['inicio'])
                fim_dt = inicio_dt + detalhes['duracao']
                
                tempo_para_inicio = inicio_dt - agora_dt
                tempo_para_fim = fim_dt - agora_dt
                
                print(f"⏰ DEBUG - Evento '{nome}':")
                print(f"   - Início: {detalhes['inicio']} ({inicio_dt.strftime('%H:%M:%S')})")
                print(f"   - Fim: {fim_dt.strftime('%H:%M:%S')}")
                print(f"   - Tempo para início: {tempo_para_inicio}")
                print(f"   - Tempo para fim: {tempo_para_fim}")
                print(f"   - Tipo: {detalhes['tipo']}")
                
                # CONDIÇÃO 1: Avisar entrada (10 min antes)
                if detalhes['tipo'] == 'entrada' and timedelta(seconds=0) <= tempo_para_inicio <= AVISO_ENTRADA:
                    print(f"✅ DEBUG - CONDIÇÃO ENTRADA ATIVADA: Aviso de entrada '{nome}'")
                    minutos = int(tempo_para_inicio.total_seconds() // 60)
                    
                    # Mapear nomes das entradas para exibição mais amigável
                    nomes_entradas = {
                        "entrada geral": "Entrada Geral",
                        "inicio contraturno": "Início do Contraturno"
                    }
                    
                    nome_exibicao = nomes_entradas.get(nome, detalhes.get('descricao', nome.title()))
                    
                    return {
                        "show_aviso": True,
                        "mensagem_status": f"{nome_exibicao} em {minutos} minutos",
                        "tempo_restante_segundos": tempo_para_inicio.total_seconds(),
                        "tipo_evento": "aviso_entrada",
                        "turno": detalhes.get('turno', 'geral')
                    }
                
                # CONDIÇÃO 2: Avisar 15 minutos antes do INÍCIO (intervalos)
                if detalhes['tipo'] == 'intervalo' and timedelta(seconds=0) <= tempo_para_inicio <= AVISO_ANTECIPADO:
                    print(f"✅ DEBUG - CONDIÇÃO 2 ATIVADA: Aviso antecipado para '{nome}'")
                    
                    # Mapear nomes dos eventos para exibição mais amigável
                    nomes_eventos = {
                        "intervalo fund1 manha": "Intervalo Fund I - Manhã",
                        "intervalo fund2 medio manha": "Intervalo Fund II e Médio - Manhã", 
                        "intervalo fund1 tarde": "Intervalo Fund I - Tarde",
                        "intervalo fund2 tarde": "Intervalo Fund II - Tarde"
                    }
                    
                    nome_exibicao = nomes_eventos.get(nome, detalhes.get('descricao', nome.title()))
                    minutos = int(tempo_para_inicio.total_seconds() // 60)
                    
                    return {
                        "show_aviso": True,
                        "mensagem_status": f"{nome_exibicao} em {minutos} minutos",
                        "tempo_restante_segundos": tempo_para_inicio.total_seconds(),
                        "tipo_evento": "aviso_inicio",
                        "turno": detalhes.get('turno', 'geral')
                    }
                
                # CONDIÇÃO 3: DURANTE o intervalo
                if tempo_para_inicio <= timedelta(seconds=0) <= tempo_para_fim and detalhes['tipo'] == 'intervalo':
                    print(f"✅ DEBUG - CONDIÇÃO 3 ATIVADA: Durante o intervalo '{nome}'")
                    
                    # Mapear nomes dos intervalos para exibição mais amigável
                    nomes_intervalos = {
                        "intervalo fund1 manha": "Intervalo Fund I - Manhã",
                        "intervalo fund2 medio manha": "Intervalo Fund II e Médio - Manhã", 
                        "intervalo fund1 tarde": "Intervalo Fund I - Tarde",
                        "intervalo fund2 tarde": "Intervalo Fund II - Tarde"
                    }
                    
                    nome_exibicao = nomes_intervalos.get(nome, detalhes.get('descricao', nome.title()))
                    
                    # Se faltam 5 minutos ou menos para terminar
                    if tempo_para_fim <= AVISO_FIM:
                        print(f"⚠️ DEBUG - Fim do intervalo em breve")
                        return {
                            "show_aviso": True,
                            "mensagem_status": f"{nome_exibicao} termina em",
                            "tempo_restante_segundos": tempo_para_fim.total_seconds(),
                            "tipo_evento": "fim_intervalo",
                            "turno": detalhes.get('turno', 'geral')
                        }
                    else:
                        print(f"🔄 DEBUG - Intervalo em andamento")
                        return {
                            "show_aviso": True,
                            "mensagem_status": f"{nome_exibicao} em andamento",
                            "tempo_restante_segundos": tempo_para_fim.total_seconds(),
                            "tipo_evento": "durante_intervalo",
                            "turno": detalhes.get('turno', 'geral')
                        }
                
                # CONDIÇÃO 4: Avisar saída (5 min antes)
                if detalhes['tipo'] == 'saida' and timedelta(seconds=0) <= tempo_para_inicio <= AVISO_SAIDA:
                    print(f"✅ DEBUG - CONDIÇÃO 4 ATIVADA: Aviso de saída '{nome}'")
                    minutos = int(tempo_para_inicio.total_seconds() // 60)
                    
                    # Mapear nomes das saídas para exibição mais amigável
                    nomes_saidas = {
                        "saida educacao infantil": "Saída Educação Infantil",
                        "saida fundamental1": "Saída Fundamental I",
                        "saida fundamental2 medio": "Saída Fundamental II e Médio"
                    }
                    
                    nome_exibicao = nomes_saidas.get(nome, detalhes.get('descricao', nome.title()))
                    
                    return {
                        "show_aviso": True,
                        "mensagem_status": f"{nome_exibicao} em {minutos} minutos",
                        "tempo_restante_segundos": tempo_para_inicio.total_seconds(),
                        "tipo_evento": "aviso_saida",
                        "turno": detalhes.get('turno', 'geral')
                    }
                
                print(f"❌ DEBUG - Nenhuma condição atendida para '{nome}'")
                
            except Exception as evento_erro:
                print(f"⚠️ Erro ao processar evento '{nome}': {evento_erro}")
                continue
        
        # Se chegou aqui, não há avisos ativos para mostrar
        if agora_dt.weekday() >= 5:  # Final de semana
            print(f"📅 DEBUG - Final de semana detectado")
            return {
                "show_aviso": False,
                "mensagem_status": "Bom final de semana!",
                "tempo_restante_segundos": None,
                "tipo_evento": "fim_de_semana",
                "turno": None
            }
        elif turno_atual is None:  # Fora do horário escolar
            print(f"🏫 DEBUG - Fora do horário escolar")
            return {
                "show_aviso": False,
                "mensagem_status": "Escola fechada - Próximo turno: 7h (manhã)",
                "tempo_restante_segundos": None,
                "tipo_evento": "fora_horario",
                "turno": None
            }
        else:  # Horário normal de aula
            print(f"📖 DEBUG - Aula normal em andamento")
            return {
                "show_aviso": False,
                "mensagem_status": f"Aula em andamento - Turno da {turno_atual}",
                "tempo_restante_segundos": None,
                "tipo_evento": "aula_normal",
                "turno": turno_atual
            }
            
    except Exception as e:
        print(f"⚠️ ERRO CRÍTICO em get_status_intervalo(): {e}")
        return {
            "show_aviso": False,
            "mensagem_status": "Erro no sistema de horários",
            "tempo_restante_segundos": None,
            "tipo_evento": "erro_sistema",
            "turno": None
        }

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def fetch_and_cache_weather():
    """
    Busca a previsão do tempo na API e salva em um arquivo local para evitar consultas repetidas.
    Se houver algum erro de rede, mostra uma mensagem no terminal.
    """
    print(f"🌤️  Iniciando busca de dados do clima...")
    print(f"🌍 Cidade: {city}")
    print(f"📁 Arquivo cache: {CACHE_FILE}")
    
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=pt_br'
    
    
    try:
        print(f"🔄 Fazendo requisição para: {url[:50]}...")
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Resposta recebida: {response.status_code}")
        dados_previsao = response.json()
        
        # Verificar se os dados são válidos
        if 'list' not in dados_previsao or not dados_previsao['list']:
            print(f"⚠️ Dados de previsão inválidos ou vazios")
            return
        
        # Salvar no arquivo
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados_previsao, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Dados do clima salvos em: {CACHE_FILE}")
        print(f"📊 Previsões disponíveis: {len(dados_previsao['list'])}")
        
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout ao buscar dados do clima (30s)")
    except requests.exceptions.ConnectionError:
        print(f"🌐 Erro de conexão ao buscar dados do clima")
    except requests.exceptions.HTTPError as e:
        print(f"🚫 Erro HTTP ao buscar dados do clima: {e}")
        if response.status_code == 401:
            print(f"🔑 Verificar se a API_KEY está correta: {api_key[:10]}...")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de requisição ao buscar dados do clima: {e}")
    except json.JSONDecodeError as e:
        print(f"📄 Erro ao decodificar JSON da API do clima: {e}")
    except IOError as e:
        print(f"💾 Erro ao salvar arquivo de clima: {e}")
    except Exception as e:
        print(f"⚠️ Erro inesperado ao buscar dados do clima: {e}")
        import traceback
        traceback.print_exc()


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
    try:
        print("🔧 Inicializando banco de dados...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso")
        
        # Verificar e criar usuário administrador padrão
        try:
            if not Usuario.query.filter_by(email='marketingsesitls@sesims.com').first():
                admin_user = Usuario(nome='Admin', email='marketingsesitls@sesims.com', senha='gff$@h12dh')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuário administrador criado")
            else:
                print("ℹ️ Usuário administrador já existe")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erro ao criar usuário administrador: {e}")
            
        # Verificar e criar dispositivo de teste
        try:
            if not Dispositivo.query.first():
                novo_dispositivo = Dispositivo(
                    ip="192.168.1.100", 
                    nome="Painel Principal", 
                    local="Entrada",
                    status="ativo",
                    observacoes="Dispositivo de teste criado automaticamente"
                )
                db.session.add(novo_dispositivo)
                db.session.commit()
                print("✅ Dispositivo de teste criado")
            else:
                print("ℹ️ Dispositivos já existem no banco")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erro ao criar dispositivo de teste: {e}")
            
        # Verificar e criar notícia de exemplo
        try:
            if not Noticia.query.first():
                nova_noticia = Noticia(
                    dispositivo_id=1, 
                    conteudo="Bem-vindos ao Sistema de Avisos Escolares!", 
                    status="ativa"
                )
                db.session.add(nova_noticia)
                db.session.commit()
                print("✅ Notícia de exemplo criada")
            else:
                print("ℹ️ Notícias já existem no banco")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erro ao criar notícia de exemplo: {e}")
            
        # Verificar e criar evento de exemplo
        try:
            if not Evento.query.first():
                novo_evento = Evento(
                    dispositivo_id=1, 
                    titulo="Sistema Funcionando", 
                    descricao="O sistema de avisos está operacional e monitorando os horários escolares.", 
                    status="ativo",
                    cor_fundo="#2563eb"
                )
                db.session.add(novo_evento)
                db.session.commit()
                print("✅ Evento de exemplo criado")
            else:
                print("ℹ️ Eventos já existem no banco")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erro ao criar evento de exemplo: {e}")
            
        print("🎉 Inicialização do banco de dados concluída")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO na inicialização do banco: {e}")
        print("   O sistema pode não funcionar corretamente!")
        raise


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
    
    # DEBUG: Log do status retornado
    print(f"🚨 DEBUG PAINEL - Status do intervalo:")
    print(f"   - show_aviso: {status_intervalo.get('show_aviso')}")
    print(f"   - mensagem_status: {status_intervalo.get('mensagem_status')}")
    print(f"   - tipo_evento: {status_intervalo.get('tipo_evento')}")
    print("=" * 50)
    
    return render_template(
        "painel.html",
        noticia=noticia,
        evento=evento,
        **status_intervalo
    )


@app.route("/padlet")
def show_padlet():
    noticia = Noticia.query.filter_by(status='ativa').all()
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
        "padlet.html",
        noticia=noticia,
        evento=evento,
        **status_intervalo
    )

@app.route('/dispositivos')
@login_required
def show_dispositivos():
    dispositivos = Dispositivo.query.all()
    return render_template('dispositivos.html', dispositivos=dispositivos)


# =====================================================
# FUNÇÕES AUXILIARES COM PROGRAMAÇÃO DEFENSIVA
# =====================================================

def validar_ip(ip):
    """
    Valida se o endereço IP está em formato correto e é seguro.
    Implementa validações extras para evitar IPs perigosos.
    Retorna True se válido, False caso contrário.
    """
    # Validação básica
    if not ip or not isinstance(ip, str):
        print(f"⚠️ IP inválido: não é string ou está vazio")
        return False
    
    # Sanitizar entrada
    ip_limpo = ip.strip()
    
    # Verificar tamanho máximo
    if len(ip_limpo) > 15:  # IPv4 máximo: 255.255.255.255 = 15 chars
        print(f"⚠️ IP muito longo: {len(ip_limpo)} caracteres")
        return False
    
    try:
        # Validar formato usando ipaddress
        ip_obj = ipaddress.ip_address(ip_limpo)
        
        # Verificações de segurança adicionais
        if ip_obj.is_loopback and ip_limpo != '127.0.0.1':
            print(f"⚠️ IP loopback não permitido: {ip_limpo}")
            return False
            
        if ip_obj.is_multicast:
            print(f"⚠️ IP multicast não permitido: {ip_limpo}")
            return False
            
        if ip_obj.is_reserved:
            print(f"⚠️ IP reservado não permitido: {ip_limpo}")
            return False
        
        # Verificar se está em faixas válidas para uso local
        if not (ip_obj.is_private or ip_limpo == '127.0.0.1'):
            print(f"⚠️ IP público não recomendado para dispositivos locais: {ip_limpo}")
            # Não bloquear, apenas avisar
        
        print(f"✅ IP válido: {ip_limpo}")
        return True
        
    except ValueError as e:
        print(f"⚠️ Erro na validação do IP '{ip_limpo}': {e}")
        return False
    except Exception as e:
        print(f"⚠️ Erro inesperado na validação do IP: {e}")
        return False

def sanitizar_texto(texto, max_length=250):
    """
    Remove caracteres perigosos e limita o tamanho do texto.
    Implementa validações robustas para evitar injeções.
    Retorna o texto sanitizado.
    """
    if not texto:
        return ""
    
    try:
        # Converter para string se não for
        texto_str = str(texto)
        
        # Verificar tamanho antes do processamento
        if len(texto_str) > max_length * 2:  # Permitir o dobro antes de cortar
            print(f"⚠️ Texto muito longo ({len(texto_str)} chars), cortando...")
            texto_str = texto_str[:max_length * 2]
        
        # Remove caracteres de controle perigosos, mantendo apenas espaços, tabs e quebras
        caracteres_permitidos = []
        for char in texto_str:
            # Permitir caracteres imprimíveis + espaços + quebras de linha
            if ord(char) >= 32 or char in '\n\t\r':
                caracteres_permitidos.append(char)
            else:
                print(f"⚠️ Caractere de controle removido: ord({ord(char)})")
        
        texto_limpo = ''.join(caracteres_permitidos)
        
        # Remover tags HTML básicas por segurança
        texto_limpo = re.sub(r'<[^>]*>', '', texto_limpo)
        
        # Limitar tamanho final
        resultado = texto_limpo.strip()[:max_length]
        
        if len(resultado) != len(texto.strip()):
            print(f"📝 Texto sanitizado: {len(texto)} -> {len(resultado)} caracteres")
        
        return resultado
        
    except Exception as e:
        print(f"⚠️ Erro ao sanitizar texto: {e}")
        return ""  # Retorna string vazia em caso de erro

def validar_status(status, valores_validos=['ativo', 'inativo', 'manutencao']):
    """
    Verifica se o status está entre os valores válidos.
    Implementa validação defensiva com logging.
    Retorna o status se válido, 'ativo' como padrão caso contrário.
    """
    try:
        if not status:
            print("📋 Status vazio, usando padrão 'ativo'")
            return 'ativo'
        
        # Sanitizar entrada
        status_limpo = str(status).lower().strip()
        
        # Verificar se está na lista de valores válidos
        if status_limpo in valores_validos:
            print(f"✅ Status válido: {status_limpo}")
            return status_limpo
        else:
            print(f"⚠️ Status inválido '{status_limpo}', usando padrão 'ativo'")
            print(f"   Valores válidos: {valores_validos}")
            return 'ativo'
            
    except Exception as e:
        print(f"⚠️ Erro na validação de status: {e}")
        return 'ativo'  # Valor padrão seguro

def validar_arquivo_upload(arquivo, tipos_permitidos=['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi']):
    """
    Valida arquivo de upload com verificações de segurança.
    Retorna (valido: bool, erro: str, nome_seguro: str)
    """
    try:
        if not arquivo:
            return False, "Nenhum arquivo selecionado", ""
        
        if arquivo.filename == '':
            return False, "Nome do arquivo está vazio", ""
        
        # Verificar extensão
        if '.' not in arquivo.filename:
            return False, "Arquivo sem extensão", ""
        
        extensao = arquivo.filename.rsplit('.', 1)[1].lower()
        if extensao not in tipos_permitidos:
            return False, f"Tipo de arquivo não permitido. Use: {', '.join(tipos_permitidos)}", ""
        
        # Gerar nome seguro
        nome_seguro = secure_filename(arquivo.filename)
        if not nome_seguro:
            return False, "Nome do arquivo inválido", ""
        
        # Verificar tamanho (50MB máximo)
        arquivo.seek(0, 2)  # Ir para o final
        tamanho = arquivo.tell()
        arquivo.seek(0)  # Voltar para o início
        
        limite_tamanho = 50 * 1024 * 1024  # 50MB
        if tamanho > limite_tamanho:
            return False, f"Arquivo muito grande ({tamanho // 1024 // 1024}MB). Máximo: 50MB", ""
        
        print(f"✅ Arquivo válido: {nome_seguro} ({tamanho // 1024}KB)")
        return True, "", nome_seguro
        
    except Exception as e:
        print(f"⚠️ Erro na validação do arquivo: {e}")
        return False, "Erro interno na validação do arquivo", ""

def validar_data_hora(data_str, formato='%Y-%m-%d %H:%M'):
    """
    Valida e converte string de data/hora.
    Retorna (valido: bool, datetime_obj: datetime, erro: str)
    """
    try:
        if not data_str:
            return False, None, "Data não fornecida"
        
        # Sanitizar entrada
        data_limpa = str(data_str).strip()
        
        # Tentar converter
        data_obj = datetime.strptime(data_limpa, formato)
        
        # Verificar se a data não é muito antiga ou muito futura
        agora = datetime.now()
        if data_obj < agora - timedelta(days=365):
            return False, None, "Data muito antiga (mais de 1 ano)"
        
        if data_obj > agora + timedelta(days=365):
            return False, None, "Data muito futura (mais de 1 ano)"
        
        print(f"✅ Data válida: {data_obj}")
        return True, data_obj, ""
        
    except ValueError as e:
        return False, None, f"Formato de data inválido: {e}"
    except Exception as e:
        print(f"⚠️ Erro na validação da data: {e}")
        return False, None, "Erro interno na validação da data"


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

print("🕐 Configurando scheduler para busca de dados do clima...")
scheduler = BackgroundScheduler(daemon=True)

# Adicionar jobs agendados
for hora, minuto in horarios_agendados:
    scheduler.add_job(fetch_and_cache_weather, 'cron', hour=hora, minute=minuto)
    print(f"   ⏰ Agendado para {hora:02d}:{minuto:02d}")

# Tentar buscar dados imediatamente na inicialização
print("🚀 Executando busca inicial dos dados do clima...")
try:
    fetch_and_cache_weather()
except Exception as e:
    print(f"⚠️ Erro na busca inicial do clima: {e}")

scheduler.start()
print("✅ Scheduler iniciado com sucesso!")


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
    print(f"🌤️  Acessando rota /clima...")
    print(f"📁 Verificando arquivo: {CACHE_FILE}")
    print(f"📂 Caminho absoluto: {os.path.abspath(CACHE_FILE)}")
    
    status_intervalo = get_status_intervalo()
    clima_data = None
    erro_msg = None
    noticia = Noticia.query.filter_by(status='ativa').all()
    evento = Evento.query.filter_by(status='ativo').all()
    noticia = Noticia.query.filter_by(status='ativa').all()
    evento = Evento.query.filter_by(status='ativo').all()

    if not os.path.exists(CACHE_FILE):
        print(f"❌ Arquivo {CACHE_FILE} não existe")
        # Tentar buscar dados agora
        print(f"🔄 Tentando buscar dados do clima agora...")
        try:
            fetch_and_cache_weather()
            # Verificar novamente se o arquivo foi criado
            if os.path.exists(CACHE_FILE):
                print(f"✅ Arquivo criado com sucesso!")
            else:
                print(f"❌ Arquivo ainda não foi criado")
                erro_msg = "Erro ao buscar dados do clima. Verifique sua conexão e API key."
        except Exception as e:
            print(f"⚠️ Erro ao buscar clima: {e}")
            erro_msg = f"Erro ao buscar dados do clima: {str(e)}"
    
    if os.path.exists(CACHE_FILE) and not erro_msg:
        try:
            print(f"📖 Lendo arquivo de clima...")
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                dados_previsao = json.load(f)

            print(f"✅ Dados carregados com sucesso")
            primeira_previsao = dados_previsao['list'][0]
            clima_data = {
                'cidade': dados_previsao['city']['name'],
                'temperatura': f"{primeira_previsao['main']['temp']:.0f}",
                'condicao': primeira_previsao['weather'][0]['description'].capitalize(),
                'chance_chuva': int(primeira_previsao['pop'] * 100),
                'vento': round(primeira_previsao['wind']['speed'] * 3.6, 1),
                'icone': primeira_previsao['weather'][0]['icon'],
            }
            print(f"🌡️  Temperatura: {clima_data['temperatura']}°C")
            print(f"🏙️  Cidade: {clima_data['cidade']}")
            
        except (IOError, json.JSONDecodeError, KeyError) as e:
            print(f"❌ Erro ao processar dados do clima: {e}")
            erro_msg = f"Erro ao carregar os dados do clima: {str(e)}"
            
    return render_template(
        'clima.html',
        clima=clima_data,
        erro=erro_msg,
        noticia=noticia,
        evento=evento,
        **status_intervalo
    )

@app.route('/testar_clima')
@login_required
def testar_clima_manual():
    """
    Rota para testar a API do clima manualmente (apenas para administradores)
    """
    try:
        print("🧪 Teste manual da API do clima iniciado...")
        fetch_and_cache_weather()
        
        # Verificar se o arquivo foi criado
        cache_path = os.path.join(os.path.dirname(__file__), CACHE_FILE)
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            resultado = {
                'sucesso': True,
                'mensagem': 'Dados do clima atualizados com sucesso!',
                'cidade': dados['city']['name'],
                'temperatura': f"{dados['list'][0]['main']['temp']:.1f}°C",
                'condicao': dados['list'][0]['weather'][0]['description'],
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
        else:
            resultado = {
                'sucesso': False,
                'mensagem': 'Arquivo de cache não foi criado. Verifique a API key.'
            }
    except Exception as e:
        resultado = {
            'sucesso': False,
            'mensagem': f'Erro ao testar API: {str(e)}'
        }
    
    return jsonify(resultado)


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

@app.route('/testar_clima')
@login_required
def testar_clima():
    """Rota para testar manualmente a busca de dados do clima"""
    try:
        print("🧪 Teste manual da função de clima...")
        fetch_and_cache_weather()
        
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            return jsonify({
                'status': 'sucesso',
                'arquivo_existe': True,
                'cidade': dados.get('city', {}).get('name', 'N/A'),
                'previsoes': len(dados.get('list', [])),
                'primeira_temp': dados['list'][0]['main']['temp'] if dados.get('list') else 'N/A'
            })
        else:
            return jsonify({
                'status': 'erro',
                'arquivo_existe': False,
                'mensagem': 'Arquivo não foi criado'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        })

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
        
        # Processamento de arquivo (imagem)
        arquivo_filename = None
        
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

@app.route('/debug_intervalo')
@login_required
def debug_intervalo():
    """
    Rota para debugar o sistema de horários em tempo real.
    Útil para verificar se os horários estão funcionando corretamente.
    """
    try:
        status = get_status_intervalo()
        agora = datetime.now()
        
        # Calcular próximos eventos
        proximos_eventos = []
        for nome, detalhes in HORARIOS_EVENTOS.items():
            try:
                inicio_hoje = datetime.combine(agora.date(), detalhes['inicio'])
                tempo_para_evento = inicio_hoje - agora
                
                if tempo_para_evento.total_seconds() > 0 and tempo_para_evento.total_seconds() < 86400:  # Próximas 24h
                    proximos_eventos.append({
                        'nome': nome,
                        'inicio': detalhes['inicio'].strftime('%H:%M'),
                        'tipo': detalhes['tipo'],
                        'turno': detalhes.get('turno', 'N/A'),
                        'tempo_restante_minutos': int(tempo_para_evento.total_seconds() / 60),
                        'descricao': detalhes.get('descricao', nome.title())
                    })
            except Exception as e:
                print(f"Erro ao processar evento {nome}: {e}")
        
        # Ordenar por tempo restante
        proximos_eventos.sort(key=lambda x: x['tempo_restante_minutos'])
        
        debug_info = {
            'sistema': {
                'horario_atual': agora.strftime('%H:%M:%S'),
                'data_atual': agora.strftime('%d/%m/%Y'),
                'dia_semana': agora.weekday(),
                'turno_atual': get_turno_atual(agora.time()),
                'total_horarios_configurados': len(HORARIOS_EVENTOS)
            },
            'status_intervalo': status,
            'proximos_eventos': proximos_eventos[:5],  # Próximos 5 eventos
            'horarios_configurados': {
                nome: {
                    'inicio': str(detalhes['inicio']),
                    'fim': str((datetime.combine(agora.date(), detalhes['inicio']) + detalhes['duracao']).time()),
                    'duracao_minutos': int(detalhes['duracao'].total_seconds() / 60),
                    'tipo': detalhes['tipo'],
                    'turno': detalhes.get('turno', 'N/A'),
                    'descricao': detalhes.get('descricao', nome.title())
                }
                for nome, detalhes in HORARIOS_EVENTOS.items()
            },
            'configuracoes': {
                'AVISO_ANTECIPADO_minutos': int(AVISO_ANTECIPADO.total_seconds() / 60),
                'AVISO_FIM_minutos': int(AVISO_FIM.total_seconds() / 60),
                'AVISO_ENTRADA_minutos': int(AVISO_ENTRADA.total_seconds() / 60),
                'AVISO_SAIDA_minutos': int(AVISO_SAIDA.total_seconds() / 60)
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        print(f"⚠️ Erro na rota de debug: {e}")
        return jsonify({
            'erro': 'Erro interno no sistema de debug',
            'detalhes': str(e),
            'horario_atual': datetime.now().strftime('%H:%M:%S')
        }), 500

@app.route('/testar_horarios')
@login_required 
def testar_horarios():
    """
    Rota para testar o sistema de horários com diferentes simulações.
    Útil para verificar se os avisos funcionam corretamente.
    """
    try:
        # Horários de teste para simular diferentes situações
        horarios_teste = [
            time(6, 50),   # 10 min antes da entrada
            time(7, 0),    # Entrada geral
            time(8, 5),    # 15 min antes do intervalo Fund I
            time(8, 20),   # Durante intervalo Fund I
            time(8, 50),   # 5 min antes do fim do intervalo Fund I
            time(9, 15),   # 15 min antes do intervalo Fund II/Médio
            time(9, 30),   # Durante intervalo Fund II/Médio
            time(11, 10),  # 5 min antes da saída Ed. Infantil
            time(11, 20),  # 5 min antes da saída Fund I
            time(12, 10),  # 5 min antes da saída Fund II/Médio
            time(13, 50),  # 10 min antes do contraturno
            time(14, 25),  # 15 min antes do intervalo Fund I tarde
            time(15, 15),  # 15 min antes do intervalo Fund II tarde
        ]
        
        resultados = []
        
        for horario_teste in horarios_teste:
            # Simular o horário atual
            agora_original = datetime.now()
            agora_simulado = datetime.combine(agora_original.date(), horario_teste)
            
            # Calcular turno para este horário
            turno_simulado = get_turno_atual(horario_teste)
            
            # Simular os cálculos que seriam feitos em get_status_intervalo
            eventos_do_turno = {
                nome: detalhes for nome, detalhes in HORARIOS_EVENTOS.items()
                if detalhes.get('turno') == turno_simulado or detalhes.get('turno') is None
            }
            
            status_simulado = None
            for nome, detalhes in eventos_do_turno.items():
                inicio_dt = datetime.combine(agora_simulado.date(), detalhes['inicio'])
                fim_dt = inicio_dt + detalhes['duracao']
                
                tempo_para_inicio = inicio_dt - agora_simulado
                tempo_para_fim = fim_dt - agora_simulado
                
                # Verificar condições
                if detalhes['tipo'] == 'entrada' and timedelta(seconds=0) <= tempo_para_inicio <= AVISO_ENTRADA:
                    status_simulado = f"Aviso de entrada: {nome}"
                    break
                elif detalhes['tipo'] == 'intervalo' and timedelta(seconds=0) <= tempo_para_inicio <= AVISO_ANTECIPADO:
                    status_simulado = f"Aviso de intervalo: {nome}"
                    break
                elif tempo_para_inicio <= timedelta(seconds=0) <= tempo_para_fim and detalhes['tipo'] == 'intervalo':
                    if tempo_para_fim <= AVISO_FIM:
                        status_simulado = f"Fim do intervalo: {nome}"
                    else:
                        status_simulado = f"Durante intervalo: {nome}"
                    break
                elif detalhes['tipo'] == 'saida' and timedelta(seconds=0) <= tempo_para_inicio <= AVISO_SAIDA:
                    status_simulado = f"Aviso de saída: {nome}"
                    break
            
            if not status_simulado:
                if turno_simulado:
                    status_simulado = f"Aula normal - turno {turno_simulado}"
                else:
                    status_simulado = "Fora do horário escolar"
            
            resultados.append({
                'horario': horario_teste.strftime('%H:%M'),
                'turno': turno_simulado,
                'status': status_simulado
            })
        
        return jsonify({
            'titulo': 'Teste do Sistema de Horários',
            'data_teste': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'resultados': resultados,
            'total_horarios_configurados': len(HORARIOS_EVENTOS),
            'configuracoes': {
                'aviso_antecipado': f"{int(AVISO_ANTECIPADO.total_seconds() / 60)} min",
                'aviso_fim': f"{int(AVISO_FIM.total_seconds() / 60)} min",
                'aviso_entrada': f"{int(AVISO_ENTRADA.total_seconds() / 60)} min",
                'aviso_saida': f"{int(AVISO_SAIDA.total_seconds() / 60)} min"
            }
        })
        
    except Exception as e:
        print(f"⚠️ Erro no teste de horários: {e}")
        return jsonify({
            'erro': 'Erro interno no teste de horários',
            'detalhes': str(e)
        }), 500
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)