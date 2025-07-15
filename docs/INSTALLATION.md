# Guia de Instalação - Sistema de Painel Digital SESI

## 🎯 Visão Geral

Este guia detalha como instalar e configurar o Sistema de Painel Digital SESI em diferentes ambientes, desde desenvolvimento local até deploy em produção.

## 💻 Instalação para Desenvolvimento

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git
- Navegador web moderno

### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/sesi-painel-digital.git
cd sesi-painel-digital
```

### Passo 2: Criar Ambiente Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Passo 3: Instalar Dependências
```bash
pip install -r requirements.txt
```

### Passo 4: Configurar Variáveis de Ambiente
```bash
# Crie o arquivo .env na raiz do projeto
cp .env.example .env
```

Edite o arquivo `.env`:
```env
# Configurações básicas
SECRET_KEY=desenvolvimento_key_123456789
DEBUG=True

# API do Clima (OpenWeatherMap)
API_KEY=sua_api_key_aqui
CITY=Três Lagoas, br

# Banco de dados (SQLite para desenvolvimento)
DATABASE_URL=sqlite:///dispositivos.db

# Cache do clima
CACHE_FILE=clima.json
```

### Passo 5: Inicializar Banco de Dados
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Banco criado!')"
```

### Passo 6: Executar a Aplicação
```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

### Passo 7: Primeiro Acesso
1. Acesse `http://localhost:5000`
2. Pressione `F2` ou vá para `http://localhost:5000/login`
3. Use as credenciais padrão:
   - **Email:** admin@example.com
   - **Senha:** admin
4. **IMPORTANTE:** Altere essas credenciais após o primeiro login!

## 🏭 Instalação para Produção

### Pré-requisitos
- Servidor Linux (Ubuntu 20.04+ recomendado)
- Python 3.8+
- PostgreSQL (recomendado para produção)
- Nginx (proxy reverso)
- Certificado SSL

### Passo 1: Preparar o Servidor
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Instalar supervisor para gerenciar processos
sudo apt install supervisor -y
```

### Passo 2: Configurar PostgreSQL
```bash
# Acessar PostgreSQL
sudo -u postgres psql

# Criar banco e usuário
CREATE DATABASE sesi_painel;
CREATE USER sesi_user WITH PASSWORD 'senha_segura_aqui';
GRANT ALL PRIVILEGES ON DATABASE sesi_painel TO sesi_user;
\q
```

### Passo 3: Configurar a Aplicação
```bash
# Criar diretório da aplicação
sudo mkdir -p /var/www/sesi-painel
cd /var/www/sesi-painel

# Clonar repositório
sudo git clone https://github.com/seu-usuario/sesi-painel-digital.git .

# Criar ambiente virtual
sudo python3 -m venv venv
sudo chown -R www-data:www-data /var/www/sesi-painel

# Ativar ambiente e instalar dependências
sudo -u www-data bash -c "source venv/bin/activate && pip install -r requirements.txt"
```

### Passo 4: Configurar Variáveis de Produção
```bash
# Criar arquivo .env de produção
sudo -u www-data nano .env
```

Conteúdo do `.env` para produção:
```env
# PRODUÇÃO - Configurações Seguras
SECRET_KEY=gere_uma_chave_secreta_muito_segura_aqui_123456789
DEBUG=False
FLASK_ENV=production

# Banco PostgreSQL
DATABASE_URL=postgresql://sesi_user:senha_segura_aqui@localhost/sesi_painel

# API do Clima
API_KEY=sua_api_key_openweathermap
CITY=Três Lagoas, br

# Cache
CACHE_FILE=/var/www/sesi-painel/clima.json

# Logs
LOG_FILE=/var/www/sesi-painel/logs/app.log
```

### Passo 5: Configurar Supervisor
```bash
sudo nano /etc/supervisor/conf.d/sesi-painel.conf
```

Conteúdo:
```ini
[program:sesi-painel]
command=/var/www/sesi-painel/venv/bin/python app.py
directory=/var/www/sesi-painel
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sesi-painel.log
environment=PATH="/var/www/sesi-painel/venv/bin"
```

### Passo 6: Configurar Nginx
```bash
sudo nano /etc/nginx/sites-available/sesi-painel
```

Conteúdo:
```nginx
server {
    listen 80;
    server_name seu_dominio.com;

    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name seu_dominio.com;

    # Certificados SSL
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Servir arquivos estáticos diretamente
    location /static {
        alias /var/www/sesi-painel/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Logs
    access_log /var/log/nginx/sesi-painel-access.log;
    error_log /var/log/nginx/sesi-painel-error.log;
}
```

### Passo 7: Ativar e Iniciar Serviços
```bash
# Ativar site Nginx
sudo ln -s /etc/nginx/sites-available/sesi-painel /etc/nginx/sites-enabled/
sudo nginx -t  # Testar configuração
sudo systemctl reload nginx

# Iniciar aplicação com Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sesi-painel

# Verificar status
sudo supervisorctl status
```

## 🚀 Instalação em Raspberry Pi (Dispositivos)

### Para os Painéis (TVs)

### Pré-requisitos
- Raspberry Pi 3 ou superior
- Raspbian OS Lite
- Conexão à internet

### Instalação Rápida
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install chromium-browser xorg openbox python3 python3-pip -y

# Instalar aplicação
cd /home/pi
git clone https://github.com/seu-usuario/sesi-painel-client.git
cd sesi-painel-client
pip3 install -r requirements.txt

# Configurar auto-start
sudo nano /etc/systemd/system/painel.service
```

Conteúdo do serviço:
```ini
[Unit]
Description=Painel Digital SESI
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/sesi-painel-client
ExecStart=/usr/bin/python3 client.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Ativar serviço
sudo systemctl enable painel.service
sudo systemctl start painel.service
```

## 🔧 Configurações Adicionais

### API Key do OpenWeatherMap

1. Acesse: https://openweathermap.org/api
2. Registre-se gratuitamente
3. Obtenha sua API key
4. Adicione no arquivo `.env`:
```env
API_KEY=sua_api_key_aqui
```

### Configurar HTTPS (Produção)

#### Usando Let's Encrypt (Recomendado)
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d seu_dominio.com

# Renovação automática
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

### Backup Automático

Criar script de backup:
```bash
sudo nano /usr/local/bin/backup-sesi.sh
```

Conteúdo:
```bash
#!/bin/bash
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/sesi-painel"
APP_DIR="/var/www/sesi-painel"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
sudo -u postgres pg_dump sesi_painel > $BACKUP_DIR/db_$DATE.sql

# Backup dos uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz $APP_DIR/static/uploads/

# Manter apenas últimos 7 dias
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup concluído: $DATE"
```

```bash
# Tornar executável
sudo chmod +x /usr/local/bin/backup-sesi.sh

# Agendar no crontab
sudo crontab -e
# Adicionar linha para backup diário às 2h:
0 2 * * * /usr/local/bin/backup-sesi.sh
```

## 🔍 Verificações Pós-Instalação

### Teste de Funcionalidades

1. **Acesso à aplicação:**
```bash
curl -I http://localhost:5000
# Deve retornar 200 OK
```

2. **Teste do banco de dados:**
```bash
# No ambiente da aplicação
python3 -c "from app import db; print('Conexão OK' if db.engine.execute('SELECT 1').scalar() == 1 else 'Erro')"
```

3. **Teste da API do clima:**
```bash
# Verificar se o arquivo de cache é criado
ls -la clima.json
```

4. **Teste de upload:**
- Acesse a área administrativa
- Tente fazer upload de uma imagem pequena
- Verifique se aparece em `static/uploads/`

### Monitoramento

```bash
# Logs da aplicação
sudo tail -f /var/log/sesi-painel.log

# Status do Supervisor
sudo supervisorctl status

# Logs do Nginx
sudo tail -f /var/log/nginx/sesi-painel-access.log
sudo tail -f /var/log/nginx/sesi-painel-error.log

# Status dos serviços
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status supervisor
```

## 🆘 Troubleshooting

### Problemas Comuns

#### Erro: "Address already in use"
```bash
# Verificar processos na porta 5000
sudo lsof -i :5000
# Matar processo se necessário
sudo kill -9 PID
```

#### Erro de permissão em uploads
```bash
# Corrigir permissões
sudo chown -R www-data:www-data /var/www/sesi-painel/static/uploads/
sudo chmod -R 755 /var/www/sesi-painel/static/uploads/
```

#### Erro de conexão com banco
```bash
# Verificar status PostgreSQL
sudo systemctl status postgresql

# Testar conexão
sudo -u postgres psql -c "SELECT version();"
```

#### Aplicação não inicia
```bash
# Verificar logs detalhados
sudo supervisorctl tail -f sesi-painel

# Testar manualmente
cd /var/www/sesi-painel
sudo -u www-data bash -c "source venv/bin/activate && python app.py"
```

---

## 📋 Checklist Final

- [ ] Sistema atualizado
- [ ] Dependências instaladas
- [ ] Banco de dados configurado
- [ ] Variáveis de ambiente definidas
- [ ] Aplicação iniciando corretamente
- [ ] Nginx configurado (produção)
- [ ] SSL configurado (produção)
- [ ] Backup automatizado (produção)
- [ ] Monitoramento ativo
- [ ] Credenciais padrão alteradas
- [ ] Testes de funcionalidade realizados

**Instalação concluída! 🎉**

Para suporte técnico, consulte o arquivo `README.md` ou entre em contato com a equipe de desenvolvimento.
