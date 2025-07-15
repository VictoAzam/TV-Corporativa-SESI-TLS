# Contribuindo para o Sistema de Painel Digital SESI

Obrigado por considerar contribuir para o projeto! Este documento fornece diretrizes e informações para contribuidores.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Contribuir](#como-contribuir)
- [Reportando Bugs](#reportando-bugs)
- [Sugerindo Melhorias](#sugerindo-melhorias)
- [Desenvolvimento](#desenvolvimento)
- [Pull Requests](#pull-requests)
- [Padrões de Código](#padrões-de-código)

## 🤝 Código de Conduta

Este projeto segue um Código de Conduta para garantir um ambiente acolhedor e inclusivo:

### Nossos Compromissos

- **Respeito:** Tratamos todos com dignidade, independentemente de experiência, identidade ou origem
- **Colaboração:** Trabalhamos juntos para criar soluções melhores
- **Aprendizado:** Valorizamos diferentes perspectivas e experiências
- **Profissionalismo:** Mantemos um ambiente de trabalho construtivo

### Comportamentos Esperados

- ✅ Linguagem respeitosa e inclusiva
- ✅ Feedback construtivo e específico
- ✅ Foco na solução de problemas
- ✅ Reconhecimento das contribuições de outros

### Comportamentos Inaceitáveis

- ❌ Linguagem ofensiva ou discriminatória
- ❌ Ataques pessoais ou trolling
- ❌ Assédio em qualquer forma
- ❌ Compartilhamento de informações privadas sem permissão

## 🚀 Como Contribuir

Existem várias maneiras de contribuir com o projeto:

### 🐛 Reportando Bugs
- Use o sistema de Issues do GitHub
- Forneça informações detalhadas sobre o problema
- Inclua passos para reproduzir o bug

### 💡 Sugerindo Melhorias
- Descreva claramente a funcionalidade desejada
- Explique por que seria útil
- Considere diferentes abordagens

### 📖 Melhorando Documentação
- Corrija erros de digitação
- Adicione exemplos práticos
- Traduza para outros idiomas
- Melhore explicações existentes

### 💻 Contribuindo com Código
- Implemente novas funcionalidades
- Corrija bugs existentes
- Otimize performance
- Adicione testes

## 🐛 Reportando Bugs

### Antes de Reportar

1. **Verifique** se o bug já foi reportado
2. **Teste** na versão mais recente
3. **Documente** os passos para reproduzir

### Template para Bug Report

```markdown
**Descrição do Bug**
Descrição clara e concisa do problema.

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Role até '...'
4. Veja o erro

**Comportamento Esperado**
O que deveria ter acontecido.

**Comportamento Atual**
O que realmente aconteceu.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente:**
- OS: [ex: Ubuntu 20.04]
- Navegador: [ex: Chrome 91]
- Versão do Python: [ex: 3.9]
- Versão do Sistema: [ex: 2.1.0]

**Informações Adicionais**
Contexto adicional sobre o problema.
```

## 💡 Sugerindo Melhorias

### Template para Feature Request

```markdown
**Resumo da Funcionalidade**
Descrição breve da funcionalidade desejada.

**Problema Atual**
Que problema esta funcionalidade resolveria?

**Solução Proposta**
Como você imagina que funcionaria?

**Alternativas Consideradas**
Outras abordagens que você considerou?

**Contexto Adicional**
Screenshots, mockups, ou referências.

**Prioridade**
- [ ] Baixa
- [ ] Média
- [ ] Alta
- [ ] Crítica
```

## 💻 Desenvolvimento

### Configuração do Ambiente

1. **Fork** o repositório
2. **Clone** seu fork:
```bash
git clone https://github.com/seu-usuario/sesi-painel-digital.git
cd sesi-painel-digital
```

3. **Configure** ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

4. **Instale** dependências:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Se existir
```

5. **Configure** variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas configurações
```

6. **Execute** testes:
```bash
python -m pytest
```

### Estrutura de Branches

- **main:** Código estável em produção
- **develop:** Código em desenvolvimento
- **feature/nome-da-feature:** Novas funcionalidades
- **hotfix/nome-do-fix:** Correções urgentes
- **release/versao:** Preparação de releases

### Workflow de Desenvolvimento

1. **Crie** uma branch para sua feature:
```bash
git checkout -b feature/minha-nova-feature
```

2. **Desenvolva** e teste localmente
3. **Commit** com mensagens descritivas
4. **Push** para seu fork
5. **Abra** um Pull Request

## 🔄 Pull Requests

### Antes de Submeter

- [ ] ✅ Código testado localmente
- [ ] ✅ Testes passando
- [ ] ✅ Documentação atualizada
- [ ] ✅ Sem conflitos com main
- [ ] ✅ Commits com mensagens claras

### Template para Pull Request

```markdown
## Descrição
Descrição clara das mudanças implementadas.

## Tipo de Mudança
- [ ] Bug fix (correção que resolve um problema)
- [ ] Nova funcionalidade (adiciona funcionalidade sem quebrar existente)
- [ ] Breaking change (mudança que quebra funcionalidade existente)
- [ ] Documentação (apenas mudanças na documentação)

## Como Foi Testado?
Descreva os testes realizados para verificar suas mudanças.

## Checklist
- [ ] Meu código segue as diretrizes de estilo do projeto
- [ ] Fiz uma auto-revisão do meu código
- [ ] Comentei código complexo quando necessário
- [ ] Fiz mudanças correspondentes na documentação
- [ ] Minhas mudanças não geram novos warnings
- [ ] Adicionei testes que provam que minha correção é efetiva
- [ ] Testes novos e existentes passam localmente

## Screenshots (se aplicável)
Adicione screenshots das mudanças visuais.

## Issues Relacionadas
Fixes #(número da issue)
```

## 📝 Padrões de Código

### Python (Backend)

#### Estilo
- **PEP 8** para formatação
- **Type hints** para funções públicas
- **Docstrings** para módulos e funções
- **Imports** organizados (stdlib, terceiros, locais)

#### Exemplo:
```python
from typing import Optional, Dict, Any
from datetime import datetime

def get_status_intervalo() -> Dict[str, Any]:
    """
    Verifica o status dos intervalos escolares.
    
    Returns:
        Dict contendo informações sobre avisos ativos
    """
    agora_dt = datetime.now()
    # ... implementação
    return {
        "show_aviso": True,
        "mensagem_status": "Intervalo em 15 minutos"
    }
```

#### Convenções de Nomenclatura
- **Funções/variáveis:** snake_case
- **Classes:** PascalCase
- **Constantes:** UPPER_SNAKE_CASE
- **Arquivos:** snake_case.py

### JavaScript (Frontend)

#### Estilo
- **ES6+** features quando possível
- **camelCase** para variáveis e funções
- **PascalCase** para construtores
- **Comentários** para lógica complexa

#### Exemplo:
```javascript
/**
 * Gerencia a rotação automática entre páginas
 * @param {Array} paginas - Lista de páginas para rotação
 * @param {number} tempo - Tempo em ms entre rotações
 */
function gerenciarRotacao(paginas, tempo = 30000) {
    const paginaAtual = window.location.pathname;
    // ... implementação
}
```

### HTML/CSS

#### HTML
- **Semântico** e acessível
- **Indentação** de 2 espaços
- **Atributos** em lowercase
- **Alt text** para imagens

#### CSS
- **Mobile-first** approach
- **BEM** methodology quando aplicável
- **CSS Grid/Flexbox** para layouts
- **Custom properties** para temas

### SQL
- **Nomes de tabelas:** singular, snake_case
- **Colunas:** snake_case
- **Índices:** idx_tabela_coluna
- **Constraints:** pk_, fk_, uk_, ck_

## 🧪 Testes

### Tipos de Testes

1. **Unitários:** Testam funções individuais
2. **Integração:** Testam interação entre componentes
3. **End-to-End:** Testam fluxos completos
4. **Performance:** Testam velocidade e recursos

### Executando Testes

```bash
# Todos os testes
python -m pytest

# Testes específicos
python -m pytest tests/test_intervalo.py

# Com coverage
python -m pytest --cov=app

# Apenas testes rápidos
python -m pytest -m "not slow"
```

### Escrevendo Testes

```python
import pytest
from app import get_status_intervalo

def test_status_intervalo_aula_normal():
    """Testa status durante aula normal"""
    # Arrange
    # ... setup
    
    # Act
    resultado = get_status_intervalo()
    
    # Assert
    assert resultado["show_aviso"] is False
    assert "aula_normal" in resultado["tipo_evento"]
```

## 📚 Recursos Úteis

### Documentação
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [JavaScript MDN](https://developer.mozilla.org/pt-BR/)

### Ferramentas
- **IDE:** VS Code, PyCharm
- **Debug:** Flask Debug Toolbar
- **Testing:** pytest, Jest
- **Linting:** flake8, ESLint

### Comunidade
- **GitHub Issues:** Para discussões técnicas
- **Discord/Slack:** Chat em tempo real
- **Wiki:** Documentação colaborativa

## 🏆 Reconhecimento

Contribuidores são reconhecidos em:
- **README.md:** Lista de contribuidores
- **CHANGELOG.md:** Créditos por versão
- **Commits:** Histórico detalhado
- **Issues/PRs:** Discussões públicas


