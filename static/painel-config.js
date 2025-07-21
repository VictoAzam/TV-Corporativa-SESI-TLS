// Configurações específicas do painel
// Este arquivo é carregado apenas no painel principal

// Variáveis globais que serão definidas pelo template
window.painelConfig = {
    showAviso: false,
    eventos: []
};

// Função para inicializar o painel com dados do servidor
function inicializarPainel(config) {
    window.painelConfig = config;
    console.log('Painel inicializado com configuração:', config);
}

// Função para verificar se há eventos para mostrar
function temEventos() {
    return window.painelConfig.eventos && window.painelConfig.eventos.length > 0;
}

// Exportar para uso global
window.inicializarPainel = inicializarPainel;
window.temEventos = temEventos;
