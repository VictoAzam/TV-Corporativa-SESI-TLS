# Guia do Usuário - Sistema de Painel Digital SESI

## 🎯 Introdução

O Sistema de Painel Digital SESI é uma plataforma web que permite gerenciar e exibir conteúdo em televisões e painéis digitais da instituição. Este guia explica como usar todas as funcionalidades do sistema.

## 🚀 Primeiros Passos

### Acessando o Sistema

#### Visualização Pública
- **URL:** Acesse o endereço fornecido pela administração
- **Modo Automático:** O sistema roda automaticamente, alternando entre:
  1. **Painel Principal** - Eventos, notícias e informações
  2. **Clima** - Previsão do tempo local
  3. **Padlet** - Mural virtual interativo
  4. **Avisos** - Alertas de intervalo e saídas (quando aplicável)

#### Área Administrativa
- **Acesso Rápido:** Pressione `F2` na tela principal
- **URL Direta:** `/login`
- **Credenciais:** Fornecidas pela administração de TI

## 🖥️ Interface Principal

### Painel Principal
![Painel Principal](screenshots/painel-principal.png)

**Componentes:**
- **Relógio Digital:** Data e hora atuais
- **Área de Mídia:** Exibe imagens/vídeos dos eventos
- **Notícias Rápidas:** Texto em movimento na parte inferior
- **QR Codes:** Para links relacionados aos eventos

### Página do Clima
![Página do Clima](screenshots/clima.png)

**Informações Exibidas:**
- Temperatura atual
- Condições climáticas
- Chance de chuva
- Velocidade do vento
- Ícone do tempo

### Página Padlet
![Página Padlet](screenshots/padlet.png)

**Características:**
- Mural virtual em tela cheia
- QR Code para acesso mobile
- Conteúdo colaborativo da comunidade escolar

### Avisos de Intervalo
![Avisos](screenshots/aviso-intervalo.png)

**Tipos de Avisos:**
- **Aviso Antecipado:** 15 minutos antes do intervalo
- **Durante Intervalo:** Com contagem regressiva
- **Aviso de Saída:** 5 minutos antes do fim do turno

## 👥 Área Administrativa

### Fazendo Login

1. **Acesse a área administrativa:**
   - Pressione `F2` na tela principal, ou
   - Navegue para `/login`

2. **Insira suas credenciais:**
   - Email: `admin@example.com` (padrão)
   - Senha: `admin` (padrão)
   
3. **IMPORTANTE:** Altere as credenciais padrão no primeiro acesso!

### Dashboard Administrativo

Após o login, você terá acesso ao menu principal:

- **📝 Adicionar Conteúdo** - Criar novos eventos e notícias
- **📋 Publicações Ativas** - Gerenciar conteúdo em exibição
- **📺 Dispositivos** - Gerenciar TVs e painéis
- **🚪 Logout** - Sair do sistema

## 📝 Gerenciando Conteúdo

### Adicionando Notícias Rápidas

1. **Acesse:** Adicionar Conteúdo
2. **Selecione:** Tipo "Notícia Rápida"
3. **Preencha:**
   - **Texto:** Máximo 250 caracteres
   - **Dispositivos:** Selecione onde exibir
   - **Agendamento:** (Opcional) Data de início/fim

4. **Publique:** Clique em "Publicar Conteúdo"

**Dicas:**
- Use textos claros e diretos
- Evite caracteres especiais
- Teste em diferentes dispositivos

### Adicionando Eventos com Imagem

1. **Selecione:** Tipo "Evento com Imagem"
2. **Preencha os campos obrigatórios:**
   - **Título:** Nome do evento (máx. 50 caracteres)
   - **Descrição:** Detalhes do evento (máx. 250 caracteres)

3. **Upload de Imagem:**
   - Clique na área de upload
   - Selecione arquivo (JPG, PNG, GIF)
   - Visualize o preview

4. **Campos opcionais:**
   - **Link QR Code:** URL para mais informações
   - **Cor de Fundo:** Personalizar visual
   - **Agendamento:** Data/hora específicas

5. **Selecione dispositivos** e publique

**Formatos suportados:**
- Imagens: JPG, PNG, GIF
- Tamanho máximo: 10MB
- Resolução recomendada: 1920x1080px

### Adicionando Eventos com Vídeo

1. **Selecione:** Tipo "Evento com Vídeo"
2. **Preencha:**
   - **Título:** Nome do evento
   - **Descrição:** (Opcional) Contexto adicional

3. **Upload de Vídeo:**
   - Arraste arquivo ou clique para selecionar
   - Aguarde o upload completo
   - Visualize o preview

4. **Configure:**
   - **Link QR Code:** (Opcional)
   - **Agendamento:** (Opcional)
   - **Dispositivos:** Onde exibir

**Formatos suportados:**
- Vídeos: MP4, AVI, MOV
- Tamanho máximo: 100MB
- Resolução recomendada: 1920x1080px
- Duração recomendada: 30-60 segundos

### Agendamento de Conteúdo

**Para agendar publicações:**

1. **Ative agendamento** marcando a opção
2. **Data/Hora de Início:**
   - Selecione data e hora
   - Use formato 24h
   
3. **Data/Hora de Fim:** (Opcional)
   - Quando o conteúdo deve sair do ar
   - Deixe em branco para exibição indefinida

**Exemplos práticos:**
- **Evento pontual:** Festa junina dia 24/06 das 14h às 18h
- **Campanha:** Matrículas abertas de 01/11 a 30/11
- **Aviso urgente:** Publicação imediata, sem data de fim

## 📋 Gerenciando Publicações

### Visualizando Conteúdo Ativo

1. **Acesse:** Publicações Ativas
2. **Visualize:** Lista de todo conteúdo em exibição
3. **Informações mostradas:**
   - Tipo de conteúdo (notícia/evento)
   - Título/texto
   - Dispositivos onde está sendo exibido
   - Data de criação
   - Status (ativo/agendado)

### Editando Conteúdo

1. **Localize** o item na lista
2. **Clique em "Editar"**
3. **Modifique** campos necessários
4. **Atualize** dispositivos selecionados
5. **Salve** as alterações

**Nota:** Alterações são aplicadas imediatamente

### Excluindo Conteúdo

1. **Localize** o item a ser removido
2. **Clique em "Excluir"**
3. **Confirme** a exclusão
4. **Conteúdo removido** de todos os dispositivos

**⚠️ Atenção:** Exclusão é irreversível!

## 📺 Gerenciando Dispositivos

### Visualizando Dispositivos

**Acesse:** Dispositivos → Listar Dispositivos

**Informações exibidas:**
- Nome do dispositivo
- Local de instalação
- Endereço IP
- Status (Online/Offline)
- Última conexão
- Ações disponíveis

### Adicionando Novo Dispositivo

1. **Acesse:** Dispositivos → Adicionar Dispositivo
2. **Preencha os campos:**
   - **Nome:** Identificação (ex: "TV Recepção")
   - **Local:** Localização (ex: "Hall Principal")
   - **IP:** Endereço de rede (ex: "192.168.1.100")
   - **Status:** Ativo/Inativo/Manutenção
   - **Observações:** Informações adicionais

3. **Teste a conexão** antes de salvar
4. **Salve** o dispositivo

**Dicas para IP:**
- Use IPs fixos para estabilidade
- Documente a rede da escola
- Teste conectividade regularmente

### Editando Dispositivos

1. **Localize** o dispositivo na lista
2. **Clique em "Editar"**
3. **Modifique** informações necessárias
4. **Teste conexão** se alterou IP
5. **Salve** as alterações

### Testando Conectividade

**Para cada dispositivo:**
1. **Clique** no botão "Testar"
2. **Aguarde** o resultado:
   - ✅ **Verde:** Dispositivo online
   - ❌ **Vermelho:** Dispositivo offline
   - ⏱️ **Amarelo:** Timeout de conexão

**Solução de problemas:**
- Verificar se dispositivo está ligado
- Confirmar conexão de rede
- Validar endereço IP
- Contatar suporte técnico se necessário

## ⏰ Sistema de Avisos Automáticos

### Como Funciona

O sistema monitora automaticamente os horários escolares e exibe avisos:

**Tipos de avisos:**
1. **15 minutos antes** do intervalo
2. **Durante** o intervalo (com countdown)
3. **5 minutos antes** do fim do intervalo
4. **5 minutos antes** da saída

### Horários Configurados

**Turno da Manhã:**
- Fund I: 8h20 às 8h55 (35 min)
- Fund II e Médio: 9h30 às 9h45 (15 min)
- Saída: 12h35

**Turno da Tarde:**
- Contraturno: 14h00
- Fund I: 14h40 às 14h55 (15 min)
- Fund II: 15h30 às 15h45 (15 min)
- Saída: 18h35

**Turno da Noite:**
- Saída: 22h50

**Nota:** Horários podem ser ajustados pela administração

### Personalização de Avisos

**Mensagens automáticas incluem:**
- Nome do evento (ex: "Primeiro Intervalo")
- Tempo restante
- Tipo de aviso (início/fim/saída)
- Contagem regressiva visual

## 🎨 Personalização Visual

### Cores de Fundo para Eventos

**Paleta disponível:**
- 🔵 Azul (#667eea) - Padrão
- 🟢 Verde (#28a745) - Informativo
- 🟡 Amarelo (#ffc107) - Atenção
- 🔴 Vermelho (#dc3545) - Urgente
- 🟣 Roxo (#6f42c1) - Destaque

**Como usar:**
1. No formulário de evento
2. Selecione a cor desejada
3. Visualize o preview
4. Publique normalmente

### QR Codes Automáticos

**Geração automática quando:**
- Campo "Link QR Code" preenchido
- URL válida fornecida
- Evento publicado

**Aparência:**
- Tamanho: 128x128 pixels
- Posição: Canto inferior direito
- Cores: Preto sobre branco
- Funciona offline após geração

## 📱 Acesso Mobile

### Para Administradores

**Responsividade:**
- Interface adaptada para tablets
- Menus otimizados para touch
- Upload simplificado

**Limitações mobile:**
- Upload de vídeos grandes
- Algumas funcionalidades avançadas
- Recomenda-se usar desktop

### Para Usuários

**Padlet:**
- Escaneie QR Code da tela
- Acesse diretamente pelo smartphone
- Contribua com conteúdo
- Visualize criações da comunidade

## 🔐 Segurança e Boas Práticas

### Gerenciamento de Senhas

1. **Altere credenciais padrão** imediatamente
2. **Use senhas fortes:**
   - Mínimo 8 caracteres
   - Letras maiúsculas e minúsculas
   - Números e símbolos
   - Evite informações pessoais

3. **Não compartilhe** credenciais
4. **Faça logout** após uso

### Uso Responsável

**Conteúdo apropriado:**
- Linguagem respeitosa
- Informações verificadas
- Imagens adequadas
- Respeito às diretrizes da escola

**Tamanhos de arquivo:**
- Otimize imagens antes do upload
- Prefira vídeos curtos e compactados
- Monitore espaço de armazenamento

### Backup e Recuperação

**Responsabilidades:**
- **Administração TI:** Backup automático
- **Usuários:** Manter cópias locais de mídias importantes
- **Todos:** Reportar problemas imediatamente

## 🆘 Suporte e Troubleshooting

### Problemas Comuns

#### "Erro ao fazer upload"
**Possíveis causas:**
- Arquivo muito grande
- Formato não suportado
- Problema de conexão

**Soluções:**
- Reduza tamanho do arquivo
- Verifique formato (JPG, PNG, MP4)
- Tente novamente em alguns minutos

#### "Dispositivo não responde"
**Verificações:**
- Dispositivo ligado?
- Cabo de rede conectado?
- IP correto no cadastro?

**Ações:**
- Teste conectividade
- Contate administração de rede
- Verifique status na lista de dispositivos

#### "Conteúdo não aparece na TV"
**Possíveis causas:**
- Dispositivo não selecionado
- Problema de sincronização
- Conteúdo agendado para futuro

**Soluções:**
- Verifique seleção de dispositivos
- Aguarde próximo ciclo de rotação (30s)
- Confirme datas de agendamento

### Contatos de Suporte

**Suporte Técnico:**
- 📧 Email: suporte.ti@sesi.com.br
- 📱 WhatsApp: (67) 99999-9999
- 🕐 Horário: 7h às 18h (dias úteis)

**Suporte Pedagógico:**
- 📧 Email: pedagogico@sesi.com.br
- 📱 Telefone: (67) 3333-4444

**Emergências:**
- Para problemas críticos durante eventos
- Contate coordenação diretamente
- Use canal de comunicação interna

---

## 📚 Resumo de Comandos Rápidos

| Ação | Como Fazer |
|------|------------|
| Acessar admin | Pressionar F2 ou ir para /login |
| Adicionar notícia | Admin → Adicionar Conteúdo → Notícia |
| Adicionar evento | Admin → Adicionar Conteúdo → Imagem/Vídeo |
| Ver publicações | Admin → Publicações Ativas |
| Gerenciar TVs | Admin → Dispositivos |
| Testar TV | Dispositivos → Botão "Testar" |
| Editar conteúdo | Publicações Ativas → Editar |
| Excluir conteúdo | Publicações Ativas → Excluir |
| Fazer logout | Menu superior → Logout |

---

**Este guia cobre as principais funcionalidades do sistema. Para dúvidas específicas ou recursos avançados, consulte a equipe de suporte técnico.** 

**Última atualização:** Dezembro 2024  
**Versão do sistema:** 2.0
