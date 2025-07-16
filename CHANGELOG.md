# Changelog - Sistema de Painel Digital SESI

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [2.2.0] - 2025-01-15

### Modificado
- **Horários de intervalo** atualizados conforme nova grade curricular:
  - Fund I manhã: 8h20-8h55 (35 min)
  - Fund II e Médio manhã: 9h30-9h45 (15 min)  
  - Fund I tarde: 14h40-14h55 (15 min)
  - Fund II tarde: 15h30-15h45 (15 min)
  - Contraturno: 14h00 (horário de referência)
- **Mensagens de aviso** agora mostram o nome específico do intervalo:
  - "Intervalo Fund I - Manhã em andamento"
  - "Intervalo Fund II e Médio - Manhã em andamento"
  - "Intervalo Fund I - Tarde em andamento"
  - "Intervalo Fund II - Tarde em andamento"
- **Documentação** atualizada com novos horários
- **Sistema de avisos** adaptado para múltiplos intervalos por turno

## [2.1.0] - 2025-07-15

### Adicionado
- **Sistema de avisos automáticos** para intervalos e saídas
- **Integração completa do Padlet** como página na rotação
- **QR codes automáticos** para eventos com links
- **Debug logs** extensivos para troubleshooting
- **Validação de IP** para dispositivos
- **Sistema de backup** automático
- **Documentação completa** (README, guias técnicos e do usuário)

### Modificado
- **Rotação de páginas** otimizada com timing de 30 segundos
- **Interface administrativa** mais intuitiva
- **Sistema de upload** com preview em tempo real
- **Validações de segurança** aprimoradas
- **Performance** da animação de notícias melhorada

### Corrigido
- **Bug do aviso-intervalo** não aparecendo na rotação
- **Problema de variáveis JavaScript** entre páginas
- **Conflito de horários** entre turnos
- **Memory leak** na animação de notícias
- **Problemas de responsividade** em dispositivos móveis

## [2.0.0] - 2024-12-01

### Adicionado
- **Sistema de rotação automática** entre páginas
- **Página dedicada do clima** com dados da OpenWeatherMap
- **Upload de vídeos** para eventos
- **Agendamento de conteúdo** com data/hora
- **Gerenciamento de dispositivos** (Raspberry Pi)
- **Sistema de autenticação** completo
- **API endpoints** para integração externa

### Modificado
- **Arquitetura** completamente reescrita em Flask
- **Interface** modernizada com CSS Grid
- **Banco de dados** migrado para SQLAlchemy
- **Sistema de arquivos** reorganizado

### Removido
- Dependência de bibliotecas legadas
- Código duplicado e não utilizado

## [1.5.0] - 2024-08-15

### Adicionado
- **Notícias rápidas** com animação horizontal
- **QR codes** para eventos
- **Cores personalizáveis** para eventos
- **Sistema de cache** para dados do clima

### Modificado
- **Performance** da interface melhorada
- **Responsive design** aprimorado

### Corrigido
- Problemas de sincronização entre dispositivos
- Bugs menores na interface

## [1.4.0] - 2024-06-01

### Adicionado
- **Upload de imagens** para eventos
- **Prévia de conteúdo** antes da publicação
- **Validação de formatos** de arquivo

### Modificado
- **Sistema de arquivos** otimizado
- **Interface de upload** melhorada

## [1.3.0] - 2024-04-15

### Adicionado
- **Gerenciamento de eventos** com título e descrição
- **Sistema de status** para publicações
- **Logs de atividade** do sistema

### Corrigido
- Problemas de encoding de caracteres
- Bugs na exibição de conteúdo

## [1.2.0] - 2024-02-01

### Adicionado
- **Sistema administrativo** web
- **Autenticação de usuários**
- **CRUD completo** para dispositivos

### Modificado
- **Interface** adaptada para administração
- **Segurança** aprimorada

## [1.1.0] - 2023-12-01

### Adicionado
- **Múltiplos dispositivos** suportados
- **Configuração via web** básica
- **Logs de sistema**

### Corrigido
- Estabilidade da conexão
- Performance geral

## [1.0.0] - 2023-10-01

### Adicionado
- **Sistema base** de painel digital
- **Exibição de conteúdo** estático
- **Relógio digital** em tempo real
- **Interface básica** para uma TV

---

## Tipos de Mudanças

- **Adicionado** para novas funcionalidades
- **Modificado** para mudanças em funcionalidades existentes
- **Descontinuado** para funcionalidades que serão removidas
- **Removido** para funcionalidades removidas
- **Corrigido** para correção de bugs
- **Segurança** para vulnerabilidades corrigidas

---

## Roadmap - Próximas Versões

### [2.2.0] - Planejado para Q1 2025
- [ ] **Dashboard de analytics** para administradores
- [ ] **Notificações push** para dispositivos
- [ ] **API REST** completa para integrações
- [ ] **Sistema de templates** para eventos
- [ ] **Suporte a múltiplos idiomas**

### [2.3.0] - Planejado para Q2 2025
- [ ] **Integração com Google Calendar**
- [ ] **Sistema de enquetes** em tempo real
- [ ] **Chat/comentários** no Padlet integrado
- [ ] **Modo escuro** para interface
- [ ] **App mobile** para administração

### [3.0.0] - Planejado para Q4 2025
- [ ] **Microserviços** architecture
- [ ] **Cache distribuído** (Redis)
- [ ] **Load balancing** para múltiplas instâncias
- [ ] **Machine Learning** para otimização de conteúdo
- [ ] **Integração com sistemas** da escola (SGA)

---

## Contribuidores

- **Desenvolvimento Principal:** [Nome do Desenvolvedor]
- **Design UI/UX:** [Nome do Designer]
- **Infraestrutura:** [Nome do DevOps]
- **Testes:** [Nome do QA]

---

## Agradecimentos

- Equipe SESI Três Lagoas
- Comunidade Flask
- Contribuidores de código aberto
- Beta testers e usuários finais
