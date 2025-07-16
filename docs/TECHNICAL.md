# Documentação Técnica - Sistema de Painel Digital SESI

## 🏗️ Arquitetura do Sistema

### Stack Tecnológico
- **Backend:** Flask (Python 3.8+)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **APIs Externas:** OpenWeatherMap, QRCode.js
- **Integração:** Padlet iframe

### Componentes Principais

#### 1. Sistema de Rotação Automática
```javascript
// Lógica implementada em static/script.js
const paginasBase = ['/', '/clima', '/padlet'];
let paginasAtuais = [...paginasBase];

if (deveMostrarAviso) {
    paginasAtuais.push('/aviso-intervalo');
}
```

#### 2. Sistema de Avisos Inteligente
```python
# Implementado em app.py - função get_status_intervalo()
def get_status_intervalo():
    agora_dt = datetime.now()
    turno_atual = get_turno_atual(agora_dt.time())
    
    # Filtra eventos do turno atual
    eventos_do_turno = {
        nome: detalhes for nome, detalhes in HORARIOS_EVENTOS.items()
        if detalhes.get('turno') == turno_atual
    }
    
    # Verifica condições de aviso
    for nome, detalhes in eventos_ordenados:
        # Condição 1: Aviso antecipado (15 min antes)
        # Condição 2: Durante o evento
        # Condição 3: Aviso de saída (5 min antes)
```

#### 3. Gerenciamento de Mídia
```python
# Upload e processamento de arquivos
@app.route('/admin', methods=['POST'])
def admin():
    if 'imagem' in request.files:
        file = request.files['imagem']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            # Salva em static/uploads/
```

## 🗃️ Modelo de Dados

### Esquema do Banco de Dados

#### Tabela: dispositivos
```sql
CREATE TABLE dispositivo (
    id INTEGER PRIMARY KEY,
    ip VARCHAR(15) UNIQUE NOT NULL,
    nome VARCHAR(50) NOT NULL,
    local VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo',
    observacoes TEXT,
    ultima_atualizacao DATETIME,
    ultima_sincronizacao DATETIME,
    ultima_conexao DATETIME
);
```

#### Tabela: eventos
```sql
CREATE TABLE evento (
    id INTEGER PRIMARY KEY,
    dispositivo_id INTEGER NOT NULL,
    titulo VARCHAR(50) NOT NULL,
    descricao VARCHAR(250),
    link VARCHAR(250),
    imagem VARCHAR(250),
    video VARCHAR(250),
    cor_fundo VARCHAR(7) DEFAULT '#667eea',
    status VARCHAR(20) NOT NULL,
    data_inicio DATETIME,
    data_fim DATETIME,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivo (id)
);
```

#### Tabela: noticias
```sql
CREATE TABLE noticia (
    id INTEGER PRIMARY KEY,
    dispositivo_id INTEGER NOT NULL,
    conteudo VARCHAR(250) NOT NULL,
    data_inicio DATETIME,
    data_fim DATETIME,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivo (id)
);
```

#### Tabela: usuarios
```sql
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL,
    data_criacao DATETIME
);
```

## 🔄 Fluxo de Dados

### 1. Renderização de Páginas
```
Cliente → Flask Route → Template + Dados → HTML + JS → Rotação Automática
```

### 2. Sistema de Avisos
```
Horário Atual → get_status_intervalo() → Verificação de Condições → 
Template Rendering → JavaScript Recebe show_aviso → Adiciona à Rotação
```

### 3. Upload de Mídia
```
Form Upload → Validação → UUID Filename → Save to uploads/ → 
Database Record → Template Display
```

## 🚦 Estados do Sistema

### Estados de Dispositivo
- **ativo:** Dispositivo funcionando normalmente
- **inativo:** Dispositivo desabilitado
- **manutencao:** Em manutenção

### Estados de Conteúdo
- **ativo:** Conteúdo sendo exibido
- **inativo:** Conteúdo pausado
- **agendado:** Aguardando data de início

### Estados de Aviso
- **aviso_inicio:** 15 min antes do evento
- **durante_intervalo:** Durante o intervalo
- **fim_intervalo:** 5 min antes do fim
- **aviso_saida:** 5 min antes da saída

## 🔧 Configurações Avançadas

### Horários Personalizáveis
```python
HORARIOS_EVENTOS = {
    # Fund I manhã: 8h20-8h55 (35 min)
    "intervalo fund1 manha": {
        'inicio': time(8, 20),
        'duracao': timedelta(minutes=35),
        'tipo': 'intervalo',
        'turno': 'manha'
    },
    # Fund II e Médio manhã: 9h30-9h45 (15 min)
    "intervalo fund2 medio manha": {
        'inicio': time(9, 30),
        'duracao': timedelta(minutes=15),
        'tipo': 'intervalo',
        'turno': 'manha'
    },
    # Fund I tarde: 14h40-14h55 (15 min)
    "intervalo fund1 tarde": {
        'inicio': time(14, 40),
        'duracao': timedelta(minutes=15),
        'tipo': 'intervalo',
        'turno': 'tarde'
    },
    # Fund II tarde: 15h30-15h45 (15 min)
    "intervalo fund2 tarde": {
        'inicio': time(15, 30),
        'duracao': timedelta(minutes=15),
        'tipo': 'intervalo',
        'turno': 'tarde'
    }
}

# Constantes configuráveis
AVISO_ANTECIPADO = timedelta(minutes=15)  # Aviso antes do intervalo
AVISO_FIM = timedelta(minutes=5)          # Aviso antes do fim
```

### Agendamento de Clima
```python
# Horários para buscar dados do clima
horarios_agendados = [
    (6, 10), (8, 0), (12, 0), (13, 0), (15, 0),
    (17, 0), (18, 0), (19, 0), (21, 0), (22, 0), (22, 50)
]

scheduler = BackgroundScheduler(daemon=True)
for hora, minuto in horarios_agendados:
    scheduler.add_job(fetch_and_cache_weather, 'cron', hour=hora, minute=minuto)
```

## 🎛️ JavaScript - Funcionalidades Principais

### 1. Rotação de Páginas
```javascript
// Tempo de exibição por página
const tempoDeExibicao = 30000; // 30 segundos

// Lógica de próxima página
const indexDaProximaPagina = (indexDaPaginaAtual + 1) % paginasAtuais.length;
proximaPagina = paginasAtuais[indexDaProximaPagina];

// Redirecionamento automático
setTimeout(function() {
    window.location.href = proximaPagina;
}, tempoDeExibicao);
```

### 2. Animação de Notícias
```javascript
// Animação contínua usando requestAnimationFrame
function animar(timestamp) {
    const deltaTempoSegundos = (timestamp - ultimoTimestamp) / 1000;
    posicaoAtual -= velocidadePixelsPorSegundo * deltaTempoSegundos;
    
    // Reinicia quando sai da tela
    if (posicaoAtual < -larguraTotal) {
        posicaoAtual = 0;
    }
    
    noticiaRapida.style.transform = `translateX(${posicaoAtual}px)`;
    requestAnimationFrame(animar);
}
```

### 3. Gerenciamento de Estado
```javascript
// Persistência entre páginas
localStorage.setItem('posicaoAtualNoticiaRapida', posicaoAtual);
localStorage.setItem('idxEventoPainel', idx);

// Recuperação de estado
let posicaoAtual = parseFloat(localStorage.getItem('posicaoAtualNoticiaRapida')) || 0;
let idx = Number(localStorage.getItem('idxEventoPainel') || 0);
```

## 📊 Monitoramento e Logs

### Debug Logs Implementados
```python
# Logs de status de intervalo
print(f"🕐 DEBUG - Horário atual: {agora_dt.strftime('%H:%M:%S')}")
print(f"📚 DEBUG - Turno atual: {turno_atual}")
print(f"✅ DEBUG - CONDIÇÃO ATIVADA: {nome}")
```

### Logs JavaScript
```javascript
console.log("Usando window.SHOW_AVISO:", deveMostrarAviso);
console.log("Páginas na rotação:", paginasAtuais);
console.log("Página atual:", paginaAtualPath);
```

## 🔒 Segurança e Validações

### Validações de Entrada
```python
def sanitizar_texto(texto, max_length=250):
    if not texto:
        return ""
    # Remove caracteres de controle
    texto_limpo = ''.join(char for char in str(texto) if ord(char) >= 32 or char in '\n\t')
    return texto_limpo.strip()[:max_length]

def validar_ip(ip):
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False
```

### Upload Seguro
```python
# Filename seguro
filename = secure_filename(file.filename)
unique_filename = f"{uuid.uuid4()}_{filename}"

# Validação de tipo
if file.type.startswith('image/') or file.type.startswith('video/'):
    # Permitir upload
```

## 🌐 APIs Externas

### OpenWeatherMap
```python
def fetch_and_cache_weather():
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=pt_br'
    try:
        response = requests.get(url, verify=False)
        dados_previsao = response.json()
        # Cache local em JSON
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(dados_previsao, f, ensure_ascii=False, indent=4)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados do clima: {e}")
```

### QR Code Generation
```javascript
// Biblioteca QRCode.js
if (ev.link) {
    new QRCode(qrcodeDiv, {
        text: ev.link,
        width: 128,
        height: 128,
        colorDark: '#000000',
        colorLight: '#ffffff'
    });
}
```

## 🔄 Deploy e Produção

### Configurações de Produção
```python
# Usar PostgreSQL em produção
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Configurar SECRET_KEY segura
app.secret_key = os.getenv('SECRET_KEY')

# HTTPS obrigatório
if __name__ == '__main__':
    app.run(debug=False, ssl_context='adhoc')
```

### Estrutura de Deploy
```
/var/www/sesi2/
├── app.py
├── requirements.txt
├── static/
├── templates/
├── .env (configurações de produção)
└── logs/ (logs do sistema)
```

### Monitoramento
- Logs de acesso
- Monitoramento de conectividade com dispositivos
- Backup automático do banco de dados
- Monitoramento de uso de storage (uploads)

---

Esta documentação técnica fornece uma visão detalhada da implementação e arquitetura do sistema, facilitando manutenção, debugging e futuras extensões.
