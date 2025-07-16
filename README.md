# Sistema de Painel Digital SESI

Sistema web para gerenciamento e exibição de conteúdo em painéis digitais (TVs) do SESI. Permite rotação automática entre páginas principais, clima, Padlet e avisos de intervalo.

## 📋 Índice

- [Características](#características)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API e Rotas](#api-e-rotas)
- [Troubleshooting](#troubleshooting)
- [Contribuição](#contribuição)

## ✨ Características

### 🖥️ Painel Principal
- **Rotação automática** entre páginas a cada 30 segundos
- **Exibição de eventos** com imagens, vídeos e QR codes
- **Notícias rápidas** com animação horizontal
- **Relógio** em tempo real
- **Sistema de avisos** automático para intervalos

### 🌤️ Página do Clima
- **Previsão do tempo** com dados da OpenWeatherMap
- **Atualização automática** em horários programados
- **Cache local** para evitar excesso de requisições

### 📱 Integração Padlet
- **Página dedicada** com Padlet em tela cheia
- **QR Code** para acesso direto ao mural virtual
- **Design responsivo** sem barras de rolagem

### ⏰ Sistema de Avisos Inteligente
- **Detecção automática** de horários de intervalo
- **Avisos antecipados** (15 minutos antes)
- **Contagem regressiva** em tempo real
- **Suporte a múltiplos turnos** (manhã, tarde, noite)

### 🔧 Gerenciamento
- **Interface administrativa** completa
- **Gestão de dispositivos** (Raspberry Pi)
- **Upload de mídias** (imagens e vídeos)
- **Agendamento de conteúdo**
- **Sistema de login** seguro

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- Flask e dependências (ver `requirements.txt`)
- Navegador moderno para administração

### Instalação Local

1. **Clone o repositório:**
```bash
git clone [url-do-repositorio]
cd sesi2
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**
```bash
# Crie um arquivo .env na raiz do projeto
cp .env.example .env
# Edite o .env com suas configurações
```

4. **Execute a aplicação:**
```bash
python app.py
```

5. **Acesse o sistema:**
- Painel principal: http://localhost:5000
- Administração: http://localhost:5000/login (F2 na tela principal)

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# Chave secreta do Flask
SECRET_KEY=sua_chave_secreta_aqui

# API do clima (OpenWeatherMap)
API_KEY=sua_api_key_openweathermap
CITY=Três Lagoas, br

# Banco de dados
DATABASE_URL=sqlite:///dispositivos.db

# Cache do clima
CACHE_FILE=clima.json
```

### Horários dos Intervalos
Configure em `app.py` na variável `HORARIOS_EVENTOS`:

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
    },
    # ... outros eventos
}
```

### Configuração do Padlet
Edite o link do Padlet em `templates/padlet.html`:
```javascript
text: 'https://padlet.com/seu-padlet-aqui'
```

## 📖 Uso

### Acesso Administrativo
1. **Login:** Na tela principal, pressione `F2` ou acesse `/login`
2. **Credenciais padrão:** admin@example.com / admin
3. **Altere as credenciais** após o primeiro acesso

### Adicionando Conteúdo
1. Acesse **Admin** → **Adicionar Conteúdo**
2. Escolha o tipo: **Notícia**, **Imagem** ou **Vídeo**
3. Selecione os dispositivos de destino
4. Configure agendamento (opcional)
5. Publique o conteúdo

### Gerenciando Dispositivos
1. Acesse **Dispositivos** → **Listar Dispositivos**
2. **Adicionar novo:** IP, nome, local
3. **Testar conexão** com cada dispositivo
4. **Editar/Excluir** conforme necessário

### Sistema de Rotação
A rotação acontece automaticamente:
```
Painel Principal → Clima → Padlet → [Aviso-Intervalo*] → Painel Principal
```
*Aviso-Intervalo aparece apenas quando há avisos ativos

## 📁 Estrutura do Projeto

```
sesi2/
├── app.py                          # Aplicação principal Flask
├── requirements.txt                # Dependências Python
├── README.md                       # Esta documentação
├── .env                           # Variáveis de ambiente (criar)
├── dispositivos.db                # Banco SQLite (auto-criado)
├── clima.json                     # Cache do clima (auto-criado)
│
├── static/                        # Arquivos estáticos
│   ├── script.js                 # JavaScript principal
│   ├── css/                      # Estilos CSS
│   │   ├── style.css            # Estilo principal
│   │   ├── clima.css            # Estilo da página clima
│   │   ├── aviso.css            # Estilo dos avisos
│   │   └── ...                  # Outros estilos
│   ├── images/                   # Imagens do sistema
│   └── uploads/                  # Uploads de usuários (auto-criado)
│
└── templates/                     # Templates HTML
    ├── painel.html               # Página principal
    ├── clima.html                # Página do clima
    ├── padlet.html               # Página do Padlet
    ├── aviso-intervalo.html      # Página de avisos
    ├── login.html                # Página de login
    └── gerenciador_deconteudo/   # Templates administrativos
        ├── adicionar_conteudo.html
        ├── dispositivos.html
        └── ...
```

## 🔗 API e Rotas

### Rotas Principais
- `GET /` - Painel principal
- `GET /clima` - Página do clima
- `GET /padlet` - Página do Padlet
- `GET /aviso-intervalo` - Página de avisos

### Rotas Administrativas
- `GET/POST /login` - Sistema de login
- `GET/POST /admin` - Adicionar conteúdo
- `GET /publicacoes_ativas` - Gerenciar publicações
- `GET/POST /adicionar_dispositivo` - Gerenciar dispositivos
- `GET /listar_dispositivos` - Listar dispositivos

### API Endpoints
- `GET /testar_dispositivo/<ip>` - Testar conectividade
- `POST /excluir_evento/<id>` - Excluir evento
- `POST /excluir_noticia/<id>` - Excluir notícia

## 🛠️ Troubleshooting

### Problema: Avisos não aparecem
**Solução:**
1. Verifique os horários em `HORARIOS_EVENTOS`
2. Confirme que `show_aviso` está sendo passado para os templates
3. Verifique os logs no terminal para debug

### Problema: Clima não carrega
**Solução:**
1. Verifique a `API_KEY` do OpenWeatherMap
2. Confirme a conectividade com a internet
3. Verifique se o arquivo `clima.json` foi criado

### Problema: Dispositivo não responde
**Solução:**
1. Verifique se o IP está correto
2. Teste conectividade com `ping`
3. Confirme que o Raspberry Pi está ligado e conectado

### Problema: Upload de mídia falha
**Solução:**
1. Verifique permissões da pasta `static/uploads/`
2. Confirme o tamanho do arquivo (limite do Flask)
3. Verifique tipos de arquivo suportados

## 🔄 Rotação e Timing

### Configuração de Tempo
- **Rotação entre páginas:** 30 segundos
- **Avisos antecipados:** 15 minutos antes
- **Aviso de fim:** 5 minutos antes do término
- **Atualização do clima:** Horários programados

### Lógica de Avisos
```python
# Condições para mostrar avisos:
1. 15 minutos antes do início do intervalo
2. Durante o intervalo (com countdown)
3. 5 minutos antes da saída do turno
```

## 🎨 Personalização

### Modificando Estilos
- Edite arquivos em `static/css/`
- Principais: `style.css`, `clima.css`, `aviso.css`

### Adicionando Páginas
1. Crie template em `templates/`
2. Adicione rota em `app.py`
3. Inclua na rotação em `script.js`

### Configurando Horários
Edite `HORARIOS_EVENTOS` em `app.py` para ajustar:
- Horários de intervalo
- Duração dos intervalos
- Turnos (manhã/tarde/noite)

## 🔐 Segurança

### Recomendações
1. **Altere as credenciais padrão** após instalação
2. **Use HTTPS** em produção
3. **Configure firewall** adequadamente
4. **Mantenha backups** do banco de dados
5. **Monitore logs** de acesso

### Validações Implementadas
- Sanitização de entrada de dados
- Validação de IPs
- Proteção contra upload de arquivos maliciosos
- Prevenção de duplicação de conteúdo

## 🤝 Contribuição

### Desenvolvimento
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### Reportando Bugs
- Use as Issues do GitHub
- Inclua logs de erro
- Descreva passos para reproduzir
- Especifique ambiente (SO, Python, etc.)

---


---

**Desenvolvido para SESI Três Lagoas** 🏫
