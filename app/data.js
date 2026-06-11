/* ============================================================
   APURAÇÃO — dados de exemplo (genéricos)
   ============================================================ */
window.APP_DATA = (function () {
  const FOCUS = [
    { name: "Política nacional", color: "#7C5BE8" },
    { name: "Economia e mercado", color: "#FF6A24" },
    { name: "Segurança pública", color: "#FF4D6D" },
    { name: "Mobilidade urbana", color: "#2DB1A8" },
    { name: "Saúde", color: "#4D9BFF" },
    { name: "Educação", color: "#F2B705" },
    { name: "Cultura", color: "#B06BF2" },
    { name: "Meio ambiente", color: "#5BD68A" },
    { name: "Tecnologia", color: "#FF8A4D" },
    { name: "Outros", color: "#9489AD" },
  ];

  const dimensoes = [
    { key: "trend", title: "Tendências", grad: ["#FF6A24", "#FF4D6D"], desc: "Temas que estão ganhando ou perdendo relevância no debate público." },
    { key: "narrative", title: "Narrativas", grad: ["#7C5BE8", "#9B82F2"], desc: "Como os assuntos são construídos e disseminados pelo público." },
    { key: "emotion", title: "Tom Emocional", grad: ["#FF4D6D", "#FF8A4D"], desc: "Sentimento predominante e reações nas discussões digitais." },
    { key: "bias", title: "Viés Político", grad: ["#2DB1A8", "#4D9BFF"], desc: "Posicionamentos ideológicos e grau de polarização." },
    { key: "actors", title: "Atores", grad: ["#B06BF2", "#7C5BE8"], desc: "Perfis e organizações que lideram e impulsionam o debate." },
  ];

  const etapas = [
    { n: "01", title: "Coleta de Dados", desc: "Monitoramento abrangente de notícias, redes sociais e conteúdos digitais públicos em tempo real." },
    { n: "02", title: "Ciência de Dados", desc: "Tratamento, organização e identificação de padrões complexos em grandes volumes de informação." },
    { n: "03", title: "IA Proprietária", desc: "Análise semântica e classificação de narrativas com modelos exclusivos desenvolvidos pela Agita." },
    { n: "04", title: "Extração de Insights", desc: "Tradução de dados complexos em informações claras e acionáveis para suporte à decisão." },
  ];

  const pipelineSteps = [
    { id: 1, label: "Coleta", sub: "Crawling de fontes públicas", logs: [
      ["info", "Inicializando coletores de fontes públicas…"],
      ["", "→ 8 fontes habilitadas · 4 conectores ativos"],
      ["", "Coletando portais de notícias… 1.240 docs"],
      ["", "Coletando redes sociais… 3.880 posts"],
      ["ok", "Coleta concluída · 5.120 documentos brutos"],
    ]},
    { id: 2, label: "Limpeza", sub: "Normalização e deduplicação", logs: [
      ["info", "Normalizando texto e metadados…"],
      ["", "Removendo duplicatas e ruído…"],
      ["warn", "342 documentos descartados (spam/duplicata)"],
      ["ok", "Limpeza concluída · 4.778 documentos válidos"],
    ]},
    { id: 3, label: "Embeddings & Clusters", sub: "Vetorização semântica", logs: [
      ["info", "Gerando embeddings semânticos…"],
      ["", "Reduzindo dimensionalidade (UMAP)…"],
      ["", "Agrupando com HDBSCAN…"],
      ["ok", "24 clusters identificados"],
    ]},
    { id: 4, label: "Insights", sub: "Rotulagem e síntese", logs: [
      ["info", "Rotulando clusters com IA proprietária…"],
      ["", "Sintetizando narrativas e tendências…"],
      ["ok", "Pipeline finalizado · resultados disponíveis"],
    ]},
  ];

  // ---- clusters table ----
  const titlesPool = [
    "Mobilidade urbana e transporte público",
    "Debate sobre reforma tributária",
    "Investimentos em saúde digital",
    "Segurança pública nos grandes centros",
    "Educação básica e tecnologia em sala",
    "Sustentabilidade e economia verde",
    "Inovação e startups no setor de IA",
    "Cultura, eventos e economia criativa",
    "Mercado financeiro e taxa de juros",
    "Política habitacional e moradia",
    "Saneamento e infraestrutura hídrica",
    "Agronegócio e exportações",
    "Esporte e grandes competições",
    "Energia renovável e transição",
    "Trabalho, emprego e qualificação",
    "Privacidade de dados e regulação",
    "Turismo e desenvolvimento regional",
    "Saúde mental e bem-estar",
    "Mudanças climáticas e desastres",
    "Comércio eletrônico e consumo",
    "Telecomunicações e conectividade",
    "Política externa e diplomacia",
    "Justiça e reforma do judiciário",
    "Inclusão digital e acessibilidade",
  ];
  const kwPool = [
    ["Transporte","Metrô","Ônibus","Tarifa","Trânsito"],
    ["Impostos","Reforma","Congresso","Arrecadação","Empresas"],
    ["Telemedicina","SUS","Hospitais","Aplicativos","Diagnóstico"],
    ["Polícia","Crimes","Prevenção","Câmeras","Operações"],
    ["Escolas","Professores","Tablets","Aprendizagem","ENEM"],
    ["Carbono","Reciclagem","Energia","ESG","Florestas"],
    ["IA","Startups","Investimento","Inovação","Algoritmos"],
    ["Festivais","Museus","Música","Audiovisual","Patrocínio"],
    ["Juros","Selic","Inflação","Bolsa","Câmbio"],
    ["Moradia","Aluguel","Financiamento","Déficit","Habitação"],
  ];
  const descPool = [
    "Relatos e análises sobre o tema com forte presença em portais e redes sociais ao longo do período monitorado.",
    "Conjunto de documentos que abordam o assunto sob múltiplas perspectivas, com debate ativo entre diferentes atores.",
    "Narrativas que conectam o tema a impactos cotidianos, com tom predominantemente informativo e propositivo.",
    "Discussão polarizada com posicionamentos divergentes e alto engajamento em plataformas sociais.",
    "Cobertura técnica e institucional, com presença relevante de fontes oficiais e especialistas.",
  ];
  function seeded(i){ const x = Math.sin(i * 97.13) * 10000; return x - Math.floor(x); }
  const clusters = Array.from({ length: 24 }, (_, i) => {
    const focus = FOCUS[i % FOCUS.length];
    const size = Math.round(40 + seeded(i) * 170);
    const sim = Math.round((0.42 + seeded(i + 5) * 0.5) * 100) / 100;
    return {
      id: i,
      title: titlesPool[i % titlesPool.length],
      size,
      keywords: kwPool[i % kwPool.length],
      description: descPool[i % descPool.length],
      focus: focus.name,
      focusColor: focus.color,
      similar: (i + 3) % 24,
      similarity: sim,
      distinguishing: ["Vocabulário próprio", "Atores específicos", "Recorte regional"][i % 3],
      trend: ["▲ alta", "▼ queda", "= estável"][i % 3],
    };
  });

  const COLUMNS = [
    { key: "id", label: "Cluster ID" },
    { key: "title", label: "Title" },
    { key: "size", label: "Size" },
    { key: "keywords", label: "Keywords" },
    { key: "description", label: "Description" },
    { key: "focus", label: "Focus" },
    { key: "similar", label: "Most Similar Cl." },
    { key: "similarity", label: "Similarity" },
    { key: "distinguishing", label: "Distinguishing F." },
    { key: "trend", label: "Trends" },
  ];

  // ---- charts ----
  const focusCounts = [
    { name: "Outros", value: 101, color: "#9489AD" },
    { name: "Segurança pública", value: 80, color: "#FF4D6D" },
    { name: "Cultura", value: 28, color: "#B06BF2" },
    { name: "Economia e mercado", value: 23, color: "#FF6A24" },
    { name: "Política local", value: 18, color: "#7C5BE8" },
    { name: "Política nacional", value: 16, color: "#9B82F2" },
    { name: "Mobilidade urbana", value: 13, color: "#2DB1A8" },
    { name: "Meio ambiente", value: 7, color: "#5BD68A" },
    { name: "Esportes", value: 6, color: "#FF8A4D" },
    { name: "Saúde", value: 5, color: "#4D9BFF" },
  ];
  const fontes = [
    { name: "Portais de notícias", value: 42, color: "#FF6A24" },
    { name: "X / Twitter", value: 31, color: "#7C5BE8" },
    { name: "Instagram", value: 18, color: "#FF4D6D" },
    { name: "Blogs", value: 12, color: "#2DB1A8" },
    { name: "YouTube", value: 9, color: "#4D9BFF" },
    { name: "Fóruns", value: 6, color: "#F2B705" },
    { name: "Newsletters", value: 4, color: "#5BD68A" },
  ];
  const keywords = [
    { name: "segurança", value: 64, color: "#FF6A24" },
    { name: "economia", value: 51, color: "#FF7A34" },
    { name: "política", value: 47, color: "#FF8A4D" },
    { name: "saúde", value: 38, color: "#7C5BE8" },
    { name: "educação", value: 33, color: "#8B6BEC" },
    { name: "transporte", value: 27, color: "#9B82F2" },
    { name: "tecnologia", value: 22, color: "#FF4D6D" },
    { name: "cultura", value: 19, color: "#2DB1A8" },
    { name: "ambiente", value: 14, color: "#4D9BFF" },
    { name: "esporte", value: 11, color: "#F2B705" },
  ];
  const trend = {
    labels: ["Sem 1","Sem 2","Sem 3","Sem 4","Sem 5","Sem 6","Sem 7","Sem 8"],
    series: [
      { name: "Segurança pública", color: "#FF4D6D", points: [12,18,24,22,31,28,36,42] },
      { name: "Economia e mercado", color: "#FF6A24", points: [20,22,19,25,24,29,27,31] },
      { name: "Política nacional", color: "#7C5BE8", points: [30,28,26,24,21,23,20,18] },
    ],
  };

  return {
    FOCUS, dimensoes, etapas, pipelineSteps, clusters, COLUMNS,
    focusCounts, fontes, keywords, trend,
    stats: { total: 120, clusters: 24, fontes: 8, colunas: 10 },
  };
})();
