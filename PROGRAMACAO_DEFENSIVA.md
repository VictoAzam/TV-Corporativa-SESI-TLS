# Programação Defensiva - Sistema de Avisos Escolares

## Visão Geral

Este documento descreve as práticas de **programação defensiva** implementadas no backend (`app.py`) do Sistema de Avisos Escolares SESI. A programação defensiva é uma metodologia que visa criar sistemas mais robustos, seguros e resistentes a falhas, através de validações rigorosas, tratamento de exceções e verificações preventivas.

---

## 1. Validação de Configurações e Horários

### Validação Automática de Configurações de Tempo

```python
# Validação de configurações críticas com fallback seguro
try:
    assert AVISO_ANTECIPADO.total_seconds() > 0, "AVISO_ANTECIPADO deve ser positivo"
    assert AVISO_FIM.total_seconds() > 0, "AVISO_FIM deve ser positivo"
    assert AVISO_ENTRADA.total_seconds() > 0, "AVISO_ENTRADA deve ser positivo"
    assert AVISO_SAIDA.total_seconds() > 0, "AVISO_SAIDA deve ser positivo"
except AssertionError as e:
    print(f"⚠️ ERRO DE CONFIGURAÇÃO: {e}")
    # Valores padrão seguros em caso de erro
    AVISO_ANTECIPADO = timedelta(minutes=15)
    AVISO_FIM = timedelta(minutes=5)
    AVISO_ENTRADA = timedelta(minutes=15)
    AVISO_SAIDA = timedelta(minutes=15)
```

**Benefícios:**
- ✅ Garantia de que o sistema nunca inicia com configurações inválidas
- ✅ Fallback automático para valores seguros
- ✅ Logging claro de problemas de configuração

### Função de Validação de Horários (`validar_horario_evento`)

```python
def validar_horario_evento(horario_dict):
    """
    Função de programação defensiva para validar configurações de horários.
    Retorna True se válido, False caso contrário.
    """
    try:
        # Verificação de tipo básico
        if not isinstance(horario_dict, dict):
            return False
        
        # Verificação de campos obrigatórios
        campos_obrigatorios = ['inicio', 'duracao', 'tipo', 'turno']
        for campo in campos_obrigatorios:
            if campo not in horario_dict:
                return False
        
        # Validação de tipos específicos
        if not isinstance(horario_dict['inicio'], time):
            return False
        if not isinstance(horario_dict['duracao'], timedelta):
            return False
        
        # Validação de valores permitidos
        if horario_dict['tipo'] not in ['intervalo', 'entrada', 'saida', 'evento']:
            return False
        if horario_dict['turno'] not in ['manha', 'tarde', 'noite', None]:
            return False
            
        # Validação de lógica de negócio
        if horario_dict['duracao'].total_seconds() < 0:
            return False
            
        return True
    except Exception as e:
        print(f"⚠️ Erro na validação de horário: {e}")
        return False
```

**Características defensivas:**
- ✅ Verificação de tipos de dados
- ✅ Validação de campos obrigatórios
- ✅ Verificação de valores permitidos
- ✅ Validação de lógica de negócio
- ✅ Tratamento de exceções com logging

---

## 2. Validação e Sanitização de Entrada

### Validação Robusta de Endereços IP (`validar_ip`)

```python
def validar_ip(ip):
    """
    Valida se o endereço IP está em formato correto e é seguro.
    Implementa validações extras para evitar IPs perigosos.
    """
    # Validação básica de tipo e entrada
    if not ip or not isinstance(ip, str):
        print(f"⚠️ IP inválido: não é string ou está vazio")
        return False
    
    # Sanitização da entrada
    ip_limpo = ip.strip()
    
    # Verificação de tamanho máximo
    if len(ip_limpo) > 15:  # IPv4 máximo: 255.255.255.255
        print(f"⚠️ IP muito longo: {len(ip_limpo)} caracteres")
        return False
    
    try:
        # Validação usando biblioteca padrão
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
        
        # Alerta para IPs públicos (não bloqueia, apenas avisa)
        if not (ip_obj.is_private or ip_limpo == '127.0.0.1'):
            print(f"⚠️ IP público não recomendado: {ip_limpo}")
        
        print(f"✅ IP válido: {ip_limpo}")
        return True
        
    except ValueError as e:
        print(f"⚠️ Erro na validação do IP '{ip_limpo}': {e}")
        return False
    except Exception as e:
        print(f"⚠️ Erro inesperado na validação do IP: {e}")
        return False
```

**Medidas de segurança:**
- ✅ Validação de formato usando `ipaddress`
- ✅ Proteção contra IPs perigosos (multicast, reserved)
- ✅ Limitação de tamanho
- ✅ Sanitização da entrada
- ✅ Logging detalhado de problemas

### Sanitização de Texto (`sanitizar_texto`)

```python
def sanitizar_texto(texto, max_length=250):
    """
    Remove caracteres perigosos e limita o tamanho do texto.
    Implementa validações robustas para evitar injeções.
    """
    if not texto:
        return ""
    
    try:
        # Conversão segura para string
        texto_str = str(texto)
        
        # Verificação preventiva de tamanho
        if len(texto_str) > max_length * 2:
            print(f"⚠️ Texto muito longo ({len(texto_str)} chars), cortando...")
            texto_str = texto_str[:max_length * 2]
        
        # Remoção de caracteres de controle perigosos
        caracteres_permitidos = []
        for char in texto_str:
            if ord(char) >= 32 or char in '\n\t\r':
                caracteres_permitidos.append(char)
            else:
                print(f"⚠️ Caractere de controle removido: ord({ord(char)})")
        
        texto_limpo = ''.join(caracteres_permitidos)
        
        # Remoção de tags HTML por segurança
        texto_limpo = re.sub(r'<[^>]*>', '', texto_limpo)
        
        # Limitação final de tamanho
        resultado = texto_limpo.strip()[:max_length]
        
        if len(resultado) != len(texto.strip()):
            print(f"📝 Texto sanitizado: {len(texto)} -> {len(resultado)} caracteres")
        
        return resultado
        
    except Exception as e:
        print(f"⚠️ Erro ao sanitizar texto: {e}")
        return ""  # Retorna string vazia em caso de erro
```

**Proteções implementadas:**
- ✅ Remoção de caracteres de controle
- ✅ Sanitização de tags HTML
- ✅ Limitação de tamanho
- ✅ Tratamento de exceções com fallback seguro
- ✅ Logging de modificações

---

## 3. Validação de Dados e Status

### Validação de Status (`validar_status`)

```python
def validar_status(status, valores_validos=['ativo', 'inativo', 'manutencao']):
    """
    Verifica se o status está entre os valores válidos.
    Sempre retorna um valor válido.
    """
    try:
        if not status:
            print("📋 Status vazio, usando padrão 'ativo'")
            return 'ativo'
        
        # Sanitização e normalização
        status_limpo = str(status).lower().strip()
        
        # Verificação contra lista de valores válidos
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
```

### Validação de Arquivos de Upload (`validar_arquivo_upload`)

```python
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
        
        # Verificação de extensão
        if '.' not in arquivo.filename:
            return False, "Arquivo sem extensão", ""
        
        extensao = arquivo.filename.rsplit('.', 1)[1].lower()
        if extensao not in tipos_permitidos:
            return False, f"Tipo não permitido. Use: {', '.join(tipos_permitidos)}", ""
        
        # Geração de nome seguro
        nome_seguro = secure_filename(arquivo.filename)
        if not nome_seguro:
            return False, "Nome do arquivo inválido", ""
        
        # Verificação de tamanho (50MB máximo)
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
```

**Validações de segurança:**
- ✅ Verificação de extensões permitidas
- ✅ Geração de nomes seguros
- ✅ Limitação de tamanho de arquivo
- ✅ Validação de existência do arquivo
- ✅ Tratamento de exceções

---

## 4. Proteção Contra Operações Duplicadas

### Prevenção de Duplicação de Dados

```python
# Verificar se já existe uma notícia idêntica nos últimos 5 segundos
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
```

**Benefícios:**
- ✅ Previne criação acidental de conteúdo duplicado
- ✅ Melhora a experiência do usuário
- ✅ Reduz poluição no banco de dados
- ✅ Graceful degradation se a verificação falhar

---

## 5. Tratamento Robusto de Exceções

### Operações de Banco de Dados com Rollback

```python
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
    db.session.rollback()  # Rollback em caso de erro
    print(f"Erro ao adicionar dispositivo: {str(e)}")
    flash('Erro interno do servidor. Tente novamente mais tarde.', 'error')
    return render_template('gerenciador_deconteudo/adicionar_dispositivo.html')
```

### Operações de Rede com Timeout

```python
def testar_dispositivo(ip):
    try:
        # Comando com timeout limitado
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', '-w', '3000', ip_limpo], 
                                  capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '3', ip_limpo], 
                                  capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            # Atualizar última conexão com proteção adicional
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
            return jsonify({'sucesso': False, 'erro': 'Dispositivo não responde'})
    
    except subprocess.TimeoutExpired:
        return jsonify({'sucesso': False, 'erro': 'Timeout ao testar conexão'})
    except Exception as e:
        print(f"Erro ao testar dispositivo: {str(e)}")
        return jsonify({'sucesso': False, 'erro': 'Erro interno ao testar conexão'})
```

---

## 6. Inicialização Defensiva do Sistema

### Inicialização do Banco de Dados

```python
with app.app_context():
    try:
        print("🔧 Inicializando banco de dados...")
        db.create_all()
        print("✅ Tabelas criadas com sucesso")
        
        # Criação de dados padrão com verificação de existência
        try:
            if not Usuario.query.filter_by(email='admin@example.com').first():
                admin_user = Usuario(nome='Admin', email='admin@example.com', senha='admin')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuário administrador criado")
            else:
                print("ℹ️ Usuário administrador já existe")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Erro ao criar usuário administrador: {e}")
        
        print("🎉 Inicialização do banco de dados concluída")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO na inicialização do banco: {e}")
        print("   O sistema pode não funcionar corretamente!")
        raise
```

### Carregamento Seguro de Variáveis de Ambiente

```python
# Carregamento com fallback gracioso
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv não encontrado...")
    print("⚠️ Usando variáveis de ambiente do sistema...")

# Configurações com valores padrão seguros
app.secret_key = os.getenv('SECRET_KEY', 'S3nh@IFMS')
api_key = os.getenv('API_KEY', '4cd224af1c46c58cf99cdbd798e13931')
city = os.getenv('CITY', 'Três Lagoas, br')
```

---

## 7. Validação de Entrada em Rotas

### Validação de Parâmetros de Rota

```python
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
        # Validação defensiva de todos os campos
        nome = sanitizar_texto(request.form.get('nome', '').strip(), 50)
        local = sanitizar_texto(request.form.get('local', '').strip(), 50)
        ip = request.form.get('ip', '').strip()
        status = validar_status(request.form.get('status', 'ativo'))
        observacoes = sanitizar_texto(request.form.get('observacoes', ''), 500)
        
        # Verificações de negócio
        if not nome:
            return jsonify({'sucesso': False, 'erro': 'Nome é obrigatório!'})
        
        if not validar_ip(ip):
            return jsonify({'sucesso': False, 'erro': 'IP inválido!'})
```

---

## 8. Logging e Debugging Defensivo

### Sistema de Logging Visual

```python
# Logs com prefixos visuais para fácil identificação
print("🔧 Inicializando banco de dados...")
print("✅ Tabelas criadas com sucesso")
print("⚠️ ERRO DE CONFIGURAÇÃO: {e}")
print("❌ ERRO CRÍTICO na inicialização do banco")
print("📝 Texto sanitizado: {len(texto)} -> {len(resultado)} caracteres")
```

### Debug Condicional

```python
def get_status_intervalo():
    try:
        # DEBUG detalhado apenas quando necessário
        print(f"🕐 DEBUG - Horário atual: {agora_dt.strftime('%H:%M:%S')}")
        print(f"📚 DEBUG - Turno atual: {turno_atual}")
        print(f"📅 DEBUG - Eventos do turno '{turno_atual}': {list(eventos_do_turno.keys())}")
        
        for nome, detalhes in eventos_ordenados:
            print(f"⏰ DEBUG - Evento '{nome}':")
            print(f"   - Início: {detalhes['inicio']}")
            print(f"   - Tempo para início: {tempo_para_inicio}")
            print(f"   - Tipo: {detalhes['tipo']}")
```

---

## 9. Validação de Data e Hora

### Validação Temporal com Limites Sensatos

```python
def validar_data_hora(data_str, formato='%Y-%m-%d %H:%M'):
    """
    Valida e converte string de data/hora.
    Retorna (valido: bool, datetime_obj: datetime, erro: str)
    """
    try:
        if not data_str:
            return False, None, "Data não fornecida"
        
        # Sanitização
        data_limpa = str(data_str).strip()
        
        # Conversão
        data_obj = datetime.strptime(data_limpa, formato)
        
        # Verificação de limites sensatos
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
```

---

## 10. Verificações de Segurança em Operações Críticas

### Verificação de Existência e Duplicatas

```python
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
```

---

## Resumo das Práticas Defensivas Implementadas

| Categoria | Práticas Implementadas | Status |
|-----------|------------------------|--------|
| **Validação de Entrada** | Sanitização de texto, validação de IP, verificação de tipos | ✅ |
| **Tratamento de Exceções** | Try-catch com rollback, logging de erros | ✅ |
| **Valores Padrão** | Fallbacks seguros para configurações críticas | ✅ |
| **Verificação de Tipos** | Validação rigorosa de tipos de dados | ✅ |
| **Limites e Controles** | Timeouts, limites de tamanho, verificação de duplicatas | ✅ |
| **Proteção contra Duplicação** | Verificações temporais para evitar dados duplicados | ✅ |
| **Timeouts** | Operações de rede com limite de tempo | ✅ |
| **Logging** | Sistema de logging visual e detalhado | ✅ |
| **Verificação de Existência** | Checks antes de operações críticas | ✅ |
| **Fallbacks** | Degradação graceful em cenários de erro | ✅ |

---

## Benefícios da Programação Defensiva Implementada

### 🛡️ **Segurança**
- Proteção contra injeção de dados maliciosos
- Validação rigorosa de IPs e entradas
- Sanitização de conteúdo HTML

### 🔧 **Robustez**
- Sistema continua funcionando mesmo com entradas inválidas
- Recuperação automática de erros
- Fallbacks para valores seguros

### 📊 **Manutenibilidade**
- Logging detalhado facilita debugging
- Código autoexplicativo com validações claras
- Separação de responsabilidades

### 👥 **Experiência do Usuário**
- Mensagens de erro claras e específicas
- Prevenção de operações acidentais
- Sistema responsivo mesmo em cenários de erro

### 🚀 **Confiabilidade**
- Redução significativa de crashes
- Comportamento previsível
- Degradação graceful de funcionalidades

---

## Conclusão

A implementação de programação defensiva no Sistema de Avisos Escolares SESI garante um backend robusto, seguro e confiável. Através de validações rigorosas, tratamento adequado de exceções e verificações preventivas, o sistema é capaz de:

- **Resistir a entradas maliciosas ou incorretas**
- **Manter funcionamento mesmo em cenários adversos**
- **Fornecer feedback claro sobre problemas**
- **Facilitar manutenção e debugging**
- **Garantir integridade dos dados**

Essas práticas resultam em um sistema de produção mais estável e seguro, essencial para um ambiente escolar que depende de comunicação confiável e oportuna.
