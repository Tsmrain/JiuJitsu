// Sistema de Internacionalización (i18n) Multilingüe para Corpo e Mente IA
// Los nombres de las técnicas son nombres propios universales de Jiu-Jitsu y no se traducen.

export const translations = {
  es: {
    // Header & Navegación
    brandSub: "IA",
    adminBtn: " Gestionar Sucursales (Admin)",
    profesorBtn: " Mis Técnicas",
    loginTooltip: "Cambiar de Rol / Iniciar Sesión",
    roleLabel: "Rol",
    
    // Status & Progress
    uploadingVideo: "Subiendo video...",
    processingIA: "IA Analizando Biomecánica...",
    processingHint: "Extrayendo keypoints con YOLO y comparando similitud vectorial en Qdrant...",

    // VideoUpload Page
    uploadTitle: "Sube tu ejecución",
    uploadSubtitle: "Selecciona el profesor de tu sucursal y la técnica que deseas practicar para comparar tu movimiento.",
    selectProfesorLabel: "1. SELECCIONA EL PROFESOR DE TU SUCURSAL:",
    selectTecnicaLabelStep: "2. SELECCIONA LA TÉCNICA A EVALUAR:",
    patronProfesor: "PATRÓN PROFESOR",
    dropText: "Arrastra tu video aquí o",
    dropClick: "haz clic para explorar",
    dropHint: "MP4, MOV o WebM (Máx 50MB)",
    btnChange: "Cambiar",
    btnAnalyze: "Analizar Técnica",
    alertValidVideo: "Por favor selecciona un archivo de video válido.",
    noProfessorsFound: "Cargando profesores de la sucursal...",
    noTecnicasFound: "Este profesor aún no tiene técnicas con video de referencia.",
    hasVideoTag: " Con Video de Referencia",
    noVideoTag: " Sin Video del Profesor",

    // FeedbackView Page
    feedbackTitle: "Análisis Biomecánico Completado",
    tecnicaEvaluada: "TÉCNICA EVALUADA",
    patronRefLabel: "Patrón de Referencia:",
    similarityLabel: "Similitud Biomecánica",
    detailSummary: "Ver Detalle Biomecánico Completo",
    btnReset: " Evaluar Otra Técnica",

    // ProfesorTecnicas Page
    tecnicasTitle: "Catálogo de Técnicas",
    btnNewTecnica: "+ Nueva Técnica",
    btnClose: "Cerrar",
    loadingTecnicas: "Cargando técnicas...",
    hasVideoStatus: " Video subido por ti",
    noVideoStatus: " No tienes video para esta técnica",
    btnEdit: " Editar",
    btnDelete: " Eliminar",
    btnReplaceVideo: " Reemplazar Video",
    btnUploadVideo: " Subir Video",
    confirmDeleteTecnica: "¿Seguro que deseas eliminar esta técnica del catálogo?",
    alertVideoUploaded: "Video subido exitosamente.",
    modalPreviewTitle: "Previsualización del Video",
    modalNewTitle: "Nueva Técnica",
    modalEditTitle: "Editar Técnica",
    labelTecnicaNombre: "Nombre de la Técnica (Nombre Propio)",
    placeholderTecnicaNombre: "Ej: Armbar, Kimura, De la Riva",
    labelNivelCinturon: "Nivel Cinturón",
    labelVideoReferencia: "Video de Referencia (Demostración del Profesor)",
    dropVideoHint: "Haz clic para seleccionar o arrastra un video de referencia",
    btnSelectVideo: " Seleccionar Video",
    btnChangeVideo: " Cambiar Video",
    btnCancel: "Cancelar",
    btnSave: "Guardar Técnica",
    savingTecnica: "Guardando...",

    // Belt Levels (Español)
    beltPrefix: "Cinturón",
    belts: {
      Blanco: "Blanco",
      Azul: "Azul",
      Morado: "Morado",
      Marrón: "Marrón",
      Negro: "Negro"
    },

    // AdminSucursales Page
    adminTitle: "Gestión de Sucursales Globales",
    btnNewBranch: "+ Nueva Sucursal",
    searchMapsPlaceholder: "Pegar enlace de Google Maps para autocompletar...",
    btnSearchLocation: " Autocompletar Ubicación",
    tableNombre: "Nombre",
    tablePais: "País",
    tableCiudad: "Ciudad",
    tableDireccion: "Dirección",
    tableAcciones: "Acciones",
    confirmDeleteBranch: "¿Seguro que deseas eliminar esta sucursal?",
    modalNewBranchTitle: "Nueva Sucursal",
    modalEditBranchTitle: "Editar Sucursal",
    labelBranchNombre: "Nombre de la Sucursal",
    labelBranchPais: "País",
    labelBranchCiudad: "Ciudad",
    labelBranchDireccion: "Dirección",

    // LoginModal Component
    tabLogin: "Iniciar Sesión",
    tabSignup: "Crear Cuenta",
    labelUserOrEmail: "Usuario o Correo Electrónico",
    placeholderUserOrEmail: "Ej. admin o usuario@ejemplo.com",
    labelPassword: "Contraseña",
    btnLogin: "Ingresar",
    btnLoggingIn: "Verificando...",
    labelNombreCompleto: "Nombre Completo",
    placeholderNombreCompleto: "Ej. Lucas Lepri",
    labelUsername: "Usuario",
    labelEmail: "Correo",
    labelUserRole: "ROL DE USUARIO:",
    labelSucursal: "Sucursal / Academia",
    btnSignupSubmit: "Crear mi Cuenta",
    btnSigningUp: "Creando cuenta...",
    roleAlumno: "alumno",
    roleProfesor: "profesor"
  },

  pt: {
    // Header & Navegación
    brandSub: "IA",
    adminBtn: " Gerenciar Filiais (Admin)",
    profesorBtn: " Minhas Técnicas",
    loginTooltip: "Alterar Função / Entrar",
    roleLabel: "Função",
    
    // Status & Progress
    uploadingVideo: "Enviando vídeo...",
    processingIA: "IA Analisando Biomecânica...",
    processingHint: "Extraindo keypoints com YOLO e comparando semelhança vetorial no Qdrant...",

    // VideoUpload Page
    uploadTitle: "Envie sua execução",
    uploadSubtitle: "Selecione o professor da sua filial e a técnica que deseja praticar para comparar seu movimento.",
    selectProfesorLabel: "1. SELECIONE O PROFESSOR DA SUA FILIAL:",
    selectTecnicaLabelStep: "2. SELECIONE A TÉCNICA A AVALIAR:",
    patronProfesor: "PADRÃO PROFESSOR",
    dropText: "Arraste seu vídeo aqui ou",
    dropClick: "clique para explorar",
    dropHint: "MP4, MOV ou WebM (Máx 50MB)",
    btnChange: "Alterar",
    btnAnalyze: "Analisar Técnica",
    alertValidVideo: "Por favor selecione um arquivo de vídeo válido.",
    noProfessorsFound: "Carregando professores da filial...",
    noTecnicasFound: "Este professor ainda não possui técnicas com vídeo de referência.",
    hasVideoTag: " Com Vídeo de Referência",
    noVideoTag: " Sem Vídeo do Professor",

    // FeedbackView Page
    feedbackTitle: "Análise Biomecânica Concluída",
    tecnicaEvaluada: "TÉCNICA AVALIADA",
    patronRefLabel: "Padrão de Referência:",
    similarityLabel: "Semelhança Biomecânica",
    detailSummary: "Ver Detalhe Biomecânico Completo",
    btnReset: " Avaliar Outra Técnica",

    // ProfesorTecnicas Page
    tecnicasTitle: "Catálogo de Técnicas",
    btnNewTecnica: "+ Nova Técnica",
    btnClose: "Fechar",
    loadingTecnicas: "Carregando técnicas...",
    hasVideoStatus: " Vídeo enviado por você",
    noVideoStatus: " Sem vídeo cadastrado",
    btnEdit: " Editar",
    btnDelete: " Excluir",
    btnReplaceVideo: " Substituir Vídeo",
    btnUploadVideo: " Enviar Vídeo",
    confirmDeleteTecnica: "Deseja remover esta técnica do catálogo?",
    alertVideoUploaded: "Vídeo enviado com sucesso.",
    modalPreviewTitle: "Pré-visualização do Vídeo",
    modalNewTitle: "Nova Técnica",
    modalEditTitle: "Editar Técnica",
    labelTecnicaNombre: "Nome da Técnica (Nome Próprio)",
    placeholderTecnicaNombre: "Ex: Armbar, Kimura, De la Riva",
    labelNivelCinturon: "Nível de Faixa",
    labelVideoReferencia: "Vídeo de Referência (Demonstração do Professor)",
    dropVideoHint: "Clique para selecionar ou arraste um vídeo de referência",
    btnSelectVideo: " Selecionar Vídeo",
    btnChangeVideo: " Alterar Vídeo",
    btnCancel: "Cancelar",
    btnSave: "Salvar Técnica",
    savingTecnica: "Salvando...",

    // Belt Levels (Português)
    beltPrefix: "Faixa",
    belts: {
      Blanco: "Branca",
      Azul: "Azul",
      Morado: "Roxa",
      Marrón: "Marrom",
      Negro: "Preta"
    },

    // AdminSucursales Page
    adminTitle: "Gerenciamento de Filiais Globais",
    btnNewBranch: "+ Nova Filial",
    searchMapsPlaceholder: "Colar link do Google Maps para preencher...",
    btnSearchLocation: " Preencher Localização",
    tableNombre: "Nome",
    tablePais: "País",
    tableCiudad: "Cidade",
    tableDireccion: "Endereço",
    tableAcciones: "Ações",
    confirmDeleteBranch: "Deseja remover esta filial?",
    modalNewBranchTitle: "Nova Filial",
    modalEditBranchTitle: "Editar Filial",
    labelBranchNombre: "Nome da Filial",
    labelBranchPais: "País",
    labelBranchCiudad: "Cidade",
    labelBranchDireccion: "Endereço",

    // LoginModal Component
    tabLogin: "Entrar",
    tabSignup: "Criar Conta",
    labelUserOrEmail: "Usuário ou E-mail",
    placeholderUserOrEmail: "Ex. admin ou usuario@exemplo.com",
    labelPassword: "Senha",
    btnLogin: "Entrar",
    btnLoggingIn: "Verificando...",
    labelNombreCompleto: "Nome Completo",
    placeholderNombreCompleto: "Ex. Lucas Lepri",
    labelUsername: "Usuário",
    labelEmail: "E-mail",
    labelUserRole: "FUNÇÃO DO USUÁRIO:",
    labelSucursal: "Filial / Academia",
    btnSignupSubmit: "Criar minha Conta",
    btnSigningUp: "Criando conta...",
    roleAlumno: "aluno",
    roleProfesor: "professor"
  }
};

export function useTranslation(language = 'es') {
  const lang = (language || 'es').toLowerCase().startsWith('pt') ? 'pt' : 'es';
  const t = translations[lang] || translations.es;
  
  const getBeltLabel = (beltKey) => {
    const beltName = t.belts[beltKey] || beltKey;
    return `${t.beltPrefix} ${beltName}`;
  };

  return { t, lang, getBeltLabel };
}
