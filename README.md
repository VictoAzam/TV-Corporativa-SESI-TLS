# 📺 Sistema de Gerenciamento de TVs Educacionais

Um sistema web desenvolvido em Flask para gerenciar conteúdo exibido em TVs/painéis digitais de instituições educacionais. O sistema permite controlar notícias, eventos, avisos de intervalo e informações climáticas de forma centralizada.

## 🚀 Funcionalidades

### 📋 Gerenciamento de Conteúdo
- **Notícias Rápidas**: Criação e exibição de notícias curtas
- **Eventos com Imagem**: Upload e exibição de eventos com imagens
- **Eventos com Vídeo**: Upload e reprodução de vídeos promocionais
- **QR Codes**: Geração automática de QR codes para links

### 🖥️ Gerenciamento de Dispositivos
- **Cadastro de TVs**: Registro de dispositivos por IP, nome e localização
- **Status em Tempo Real**: Monitoramento do status de cada dispositivo
- **Teste de Conectividade**: Verificação de ping para cada TV
- **Envio de Conteúdo**: Sincronização automática com os dispositivos

### ⏰ Sistema de Intervalos Inteligente
- **Avisos Automáticos**: Notificações 15 minutos antes dos intervalos
- **Três Turnos**: Suporte para manhã, tarde e noite
- **Contagem Regressiva**: Timer visual para intervalos e saídas
- **Horários Personalizáveis**: Configuração flexível de horários

### 🌤️ Integração Climática
- **Previsão do Tempo**: Dados da API OpenWeatherMap
- **Cache Inteligente**: Armazenamento local para reduzir consultas
- **Atualizações Automáticas**: Busca periódica de dados climáticos

### 🔐 Segurança e Validação
- **Autenticação de Usuários**: Sistema de login seguro
- **Validação de Entrada**: Sanitização de dados de formulários
- **Validação de Arquivos**: Verificação de tipos e tamanhos de upload
- **Proteção contra Injeção**: Validação de IPs e comandos

## 🛠️ Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonagem)

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd Projeto-TVs
```

### 2. Criar Ambiente Virtual
```bash
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente
Edite as configurações no arquivo `app.py`:
```python
# Chave da API do clima (OpenWeatherMap)
api_key = 'sua_chave_api_aqui'

# Cidade para previsão do tempo
city = 'Sua Cidade, br'

# Chave secreta da aplicação
app.secret_key = 'sua_chave_secreta_segura'
```

### 5. Executar a Aplicação
```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 📱 Como Usar

### Primeiro Acesso
1. Acesse `http://localhost:5000/login`
2. Use as credenciais padrão:
   - **Email**: admin@example.com
   - **Senha**: admin
3. ⚠️ **IMPORTANTE**: Altere essas credenciais em produção!

### Gerenciando Dispositivos
1. Vá para "Gerenciar Dispositivos"
2. Adicione TVs informando IP, nome e localização
3. Teste a conectividade com cada dispositivo
4. Configure o status (ativo/inativo/manutenção)

### Criando Conteúdo
1. Acesse o "Painel de Administração"
2. Selecione as TVs de destino
3. Escolha o tipo de conteúdo:
   - **Notícia**: Texto simples até 250 caracteres
   - **Evento com Imagem**: Título, descrição e imagem
   - **Evento com Vídeo**: Título, descrição e vídeo
4. Configure datas de início e fim (opcional)

### Monitoramento
- **Publicações Ativas**: Visualize todo o conteúdo ativo
- **Status dos Dispositivos**: Monitore conectividade
- **Painel Principal**: Veja como o conteúdo aparece nas TVs

## 🔧 Configurações Avançadas

### Horários de Intervalo
Configure os horários no arquivo `app.py`:
```python
HORARIOS_EVENTOS = {
    "primeiro intervalo": {
        'inicio': time(9, 15),  # 9h15
        'duracao': timedelta(minutes=20),
        'tipo': 'intervalo',
        'turno': 'manha'
    },
    # ... outros horários
}
```

### Limites de Upload
- **Imagens**: Máximo 10MB (JPG, PNG, GIF, WebP)
- **Vídeos**: Máximo 50MB (MP4, AVI, MOV, WMV, WebM)

### Agendamento Climático
O sistema busca dados climáticos automaticamente nos horários:
- 6h10, 8h00, 12h00, 13h00, 15h00, 17h00, 18h00, 19h00, 21h00, 22h00, 22h50

## 📊 Estrutura do Banco de Dados

### Tabelas Principais
- **Dispositivo**: TVs cadastradas
- **Usuario**: Usuários do sistema
- **Noticia**: Notícias rápidas
- **Evento**: Eventos com imagem/vídeo
- **Mensagem_Temporaria**: Mensagens temporárias

### Backup
O banco SQLite é salvo em `dispositivos.db`. Faça backups regulares deste arquivo.

## 🔒 Segurança

### Medidas Implementadas
- ✅ Sanitização de entrada de dados
- ✅ Validação de tipos de arquivo
- ✅ Proteção contra injeção de comandos
- ✅ Validação de IPs
- ✅ Limitação de tamanho de uploads
- ✅ Timeouts em operações de rede

### Recomendações de Produção
- [ ] Alterar credenciais padrão
- [ ] Usar HTTPS (SSL/TLS)
- [ ] Configurar firewall adequado
- [ ] Implementar logging robusto
- [ ] Usar banco de dados mais robusto (PostgreSQL/MySQL)
- [ ] Configurar backup automático

## 🐛 Solução de Problemas

### Problemas Comuns

**Erro de conectividade com dispositivos:**
- Verifique se o IP está correto
- Confirme se o dispositivo está na mesma rede
- Teste o ping manualmente

**Falha no upload de arquivos:**
- Verifique o tamanho do arquivo
- Confirme o formato (extensão)
- Verifique permissões da pasta `static/uploads`

**Dados climáticos não aparecem:**
- Verifique sua chave da API OpenWeatherMap
- Confirme a conectividade com a internet
- Verifique o arquivo `clima.json`

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

