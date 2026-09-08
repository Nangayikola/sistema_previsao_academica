import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central.db")

# ---- Cursos (ID, nome, duração em anos, área) ----
cursos = [
    # Engenharia
    {"id": 1, "nome": "Engenharia Informática", "duracao_anos": 5, "area": "Engenharia"},
    {"id": 2, "nome": "Engenharia Eletrotécnica", "duracao_anos": 5, "area": "Engenharia"},
    {"id": 3, "nome": "Engenharia Mecânica", "duracao_anos": 5, "area": "Engenharia"},
    {"id": 4, "nome": "Engenharia Civil", "duracao_anos": 5, "area": "Engenharia"},
    # Saúde
    {"id": 5, "nome": "Medicina", "duracao_anos": 6, "area": "Saúde"},
    {"id": 6, "nome": "Enfermagem", "duracao_anos": 4, "area": "Saúde"},
    {"id": 7, "nome": "Farmácia", "duracao_anos": 5, "area": "Saúde"},
    {"id": 8, "nome": "Psicologia", "duracao_anos": 5, "area": "Saúde"},
    # Negócios
    {"id": 9, "nome": "Gestão de Empresas", "duracao_anos": 4, "area": "Negócios"},
    {"id": 10, "nome": "Economia", "duracao_anos": 4, "area": "Negócios"},
    {"id": 11, "nome": "Marketing", "duracao_anos": 4, "area": "Negócios"},
    {"id": 12, "nome": "Contabilidade", "duracao_anos": 4, "area": "Negócios"},
    # Artes
    {"id": 13, "nome": "Artes Plásticas", "duracao_anos": 4, "area": "Artes"},
    {"id": 14, "nome": "Música", "duracao_anos": 4, "area": "Artes"},
    {"id": 15, "nome": "Design Gráfico", "duracao_anos": 4, "area": "Artes"},
    {"id": 16, "nome": "Cinema e Audiovisual", "duracao_anos": 4, "area": "Artes"},
]

# ---- Disciplinas por Curso, Ano, Semestre ----
# Estrutura: cursos[curso_id][ano][semestre] = lista de disciplinas
disciplinas_por_curso = {
    # ========== ENGENHARIA ==========
    1: {  # Engenharia Informática
        1: {
            "I": ["Introdução à Programação", "Fundamentos de Computação", "Álgebra Linear", "Cálculo I", "Inglês Técnico I", "Comunicação e Expressão"],
            "II": ["Programação Orientada a Objetos", "Estruturas de Dados", "Cálculo II", "Física I", "Inglês Técnico II", "Metodologia Científica"]
        },
        2: {
            "I": ["Algoritmos e Complexidade", "Bases de Dados I", "Arquitetura de Computadores", "Sistemas Operativos", "Estatística e Probabilidades", "Investigação Operacional"],
            "II": ["Bases de Dados II", "Redes de Computadores I", "Engenharia de Software I", "Programação Web", "Sistemas Distribuídos", "Teoria da Computação"]
        },
        3: {
            "I": ["Engenharia de Software II", "Redes de Computadores II", "Inteligência Artificial I", "Programação Móvel", "Segurança Informática", "Empreendedorismo"],
            "II": ["Inteligência Artificial II", "Computação Gráfica", "Desenvolvimento de Jogos", "Sistemas Embebidos", "Gestão de Projetos", "Ética e Legislação"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Sistemas de Apoio à Decisão", "Tópicos Avançados em BD", "Computação na Nuvem", "Gestão de Redes"],
            "II": ["Projeto Final II", "Estágio II", "Data Science e Big Data", "Machine Learning", "Internet das Coisas", "Oficina de Inovação"]
        },
        5: {
            "I": ["Seminários de Investigação", "Elaboração de Dissertação I", "Tópicos Especiais I", "Tópicos Especiais II", "Empreendedorismo e Inovação", "Gestão de Carreira"],
            "II": ["Elaboração de Dissertação II", "Defesa de Dissertação", "Tópicos Especiais III", "Tópicos Especiais IV", "Ética Profissional", "Oficina de Projetos"]
        }
    },
    2: {  # Engenharia Eletrotécnica
        1: {
            "I": ["Circuitos Elétricos I", "Análise Matemática I", "Física I", "Desenho Técnico", "Inglês Técnico I", "Comunicação"],
            "II": ["Circuitos Elétricos II", "Análise Matemática II", "Física II", "Programação I", "Inglês Técnico II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Eletrónica I", "Teoria de Circuitos", "Máquinas Elétricas I", "Sinais e Sistemas", "Estatística", "Gestão de Projetos"],
            "II": ["Eletrónica II", "Máquinas Elétricas II", "Controlo Automático", "Microcontroladores", "Telecomunicações", "Empreendedorismo"]
        },
        3: {
            "I": ["Sistemas de Potência", "Eletrónica de Potência", "Acionamentos Elétricos", "Instrumentação", "Redes Elétricas", "Segurança"],
            "II": ["Automação Industrial", "Robótica", "Sistemas Embebidos", "Gestão de Energia", "Iluminação", "Ética e Legislação"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Manutenção", "Oficina de Inovação"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Gestão de Carreira", "Defesa de Projeto"]
        },
        5: {
            "I": ["Seminários de Investigação", "Elaboração de Dissertação I", "Tópicos Especiais I", "Tópicos Especiais II", "Empreendedorismo", "Gestão de Carreira"],
            "II": ["Elaboração de Dissertação II", "Defesa de Dissertação", "Tópicos Especiais III", "Tópicos Especiais IV", "Ética Profissional", "Oficina de Projetos"]
        }
    },
    3: {  # Engenharia Mecânica
        1: {
            "I": ["Mecânica Geral I", "Análise Matemática I", "Física I", "Desenho Técnico", "Inglês Técnico I", "Comunicação"],
            "II": ["Mecânica Geral II", "Análise Matemática II", "Física II", "Programação I", "Inglês Técnico II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Resistência dos Materiais", "Termodinâmica I", "Mecânica dos Fluidos I", "Materiais I", "Estatística", "Gestão de Projetos"],
            "II": ["Mecânica dos Sólidos", "Termodinâmica II", "Mecânica dos Fluidos II", "Materiais II", "Processos de Fabrico", "Empreendedorismo"]
        },
        3: {
            "I": ["Máquinas Térmicas", "Elementos de Máquinas", "Vibrações", "Controlo Automático", "Refrigeração e Climatização", "Segurança"],
            "II": ["Projeto de Máquinas", "Automação", "Robótica", "Manutenção Industrial", "Gestão de Energia", "Ética e Legislação"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Produção", "Oficina de Inovação"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Gestão de Carreira", "Defesa de Projeto"]
        },
        5: {
            "I": ["Seminários de Investigação", "Elaboração de Dissertação I", "Tópicos Especiais I", "Tópicos Especiais II", "Empreendedorismo", "Gestão de Carreira"],
            "II": ["Elaboração de Dissertação II", "Defesa de Dissertação", "Tópicos Especiais III", "Tópicos Especiais IV", "Ética Profissional", "Oficina de Projetos"]
        }
    },
    4: {  # Engenharia Civil
        1: {
            "I": ["Mecânica Geral", "Análise Matemática I", "Física I", "Desenho Técnico", "Inglês Técnico I", "Comunicação"],
            "II": ["Mecânica dos Solos", "Análise Matemática II", "Física II", "Programação I", "Inglês Técnico II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Resistência dos Materiais", "Hidráulica I", "Materiais de Construção I", "Topografia", "Estatística", "Gestão de Projetos"],
            "II": ["Estruturas I", "Hidráulica II", "Materiais de Construção II", "Geotecnia", "Desenho Assistido por Computador", "Empreendedorismo"]
        },
        3: {
            "I": ["Estruturas II", "Hidrologia", "Construção Civil I", "Fundações", "Segurança", "Organização de Obras"],
            "II": ["Estruturas III", "Construção Civil II", "Estradas e Aeroportos", "Saneamento", "Gestão de Obras", "Ética e Legislação"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Obras", "Oficina de Inovação"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Gestão de Carreira", "Defesa de Projeto"]
        },
        5: {
            "I": ["Seminários de Investigação", "Elaboração de Dissertação I", "Tópicos Especiais I", "Tópicos Especiais II", "Empreendedorismo", "Gestão de Carreira"],
            "II": ["Elaboração de Dissertação II", "Defesa de Dissertação", "Tópicos Especiais III", "Tópicos Especiais IV", "Ética Profissional", "Oficina de Projetos"]
        }
    },
    # ========== SAÚDE ==========
    5: {  # Medicina (6 anos)
        1: {
            "I": ["Anatomia I", "Fisiologia I", "Bioquímica I", "Histologia", "Embriologia", "Inglês Médico I"],
            "II": ["Anatomia II", "Fisiologia II", "Bioquímica II", "Genética", "Imunologia", "Inglês Médico II"]
        },
        2: {
            "I": ["Patologia I", "Farmacologia I", "Microbiologia", "Parasitologia", "Epidemiologia", "Psicologia Médica"],
            "II": ["Patologia II", "Farmacologia II", "Semiologia", "Imagiologia", "Saúde Pública", "Bioestatística"]
        },
        3: {
            "I": ["Clínica I", "Cirurgia I", "Pediatria I", "Ginecologia I", "Ética Médica", "Gestão em Saúde"],
            "II": ["Clínica II", "Cirurgia II", "Pediatria II", "Ginecologia II", "Psiquiatria", "Medicina Legal"]
        },
        4: {
            "I": ["Estágio Clínico I", "Urgências", "Oncologia", "Infectologia", "Cardiologia", "Pneumologia"],
            "II": ["Estágio Clínico II", "Neurologia", "Nefrologia", "Gastroentereologia", "Endocrinologia", "Reumatologia"]
        },
        5: {
            "I": ["Estágio Clínico III", "Dermatologia", "Oftalmologia", "Otorrino", "Ortopedia", "Saúde Mental"],
            "II": ["Estágio Clínico IV", "Medicina Familiar", "Emergência", "Cuidados Paliativos", "Medicina Transfusional", "Investigação Clínica"]
        },
        6: {
            "I": ["Internato I", "Tópicos Avançados I", "Tópicos Avançados II", "Elaboração de Dissertação I", "Gestão de Carreira", "Empreendedorismo"],
            "II": ["Internato II", "Defesa de Dissertação", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Oficina de Integração"]
        }
    },
    6: {  # Enfermagem
        1: {
            "I": ["Fundamentos de Enfermagem", "Anatomia e Fisiologia I", "Bioquímica", "Psicologia", "Inglês I", "Comunicação"],
            "II": ["Enfermagem I", "Anatomia e Fisiologia II", "Microbiologia", "Farmacologia I", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Enfermagem II", "Patologia", "Farmacologia II", "Epidemiologia", "Ética e Legislação", "Gestão em Enfermagem"],
            "II": ["Enfermagem III", "Semiologia", "Urgência e Emergência", "Saúde Pública", "Bioestatística", "Empreendedorismo"]
        },
        3: {
            "I": ["Enfermagem IV", "Enfermagem em Saúde Mental", "Enfermagem Pediátrica", "Enfermagem Obstétrica", "Gestão de Projetos", "Oficina de Inovação"],
            "II": ["Enfermagem V", "Enfermagem Oncológica", "Cuidados Paliativos", "Enfermagem Comunitária", "Tópicos Avançados", "Defesa de Projeto"]
        },
        4: {
            "I": ["Estágio I", "Estágio II", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Estágio III", "Estágio IV", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Oficina de Integração"]
        }
    },
    7: {  # Farmácia
        1: {
            "I": ["Química Geral", "Biologia Celular", "Anatomia", "Fisiologia I", "Matemática", "Inglês I"],
            "II": ["Química Orgânica", "Bioquímica", "Fisiologia II", "Microbiologia", "Estatística", "Inglês II"]
        },
        2: {
            "I": ["Química Farmacêutica I", "Farmacologia I", "Farmácia Galénica I", "Patologia", "Genética", "Ética"],
            "II": ["Química Farmacêutica II", "Farmacologia II", "Farmácia Galénica II", "Farmacognosia", "Imunologia", "Gestão de Projetos"]
        },
        3: {
            "I": ["Química Farmacêutica III", "Farmacologia III", "Farmácia Clínica I", "Saúde Pública", "Bioestatística", "Empreendedorismo"],
            "II": ["Farmacologia IV", "Farmácia Clínica II", "Toxicologia", "Farmacoeconomia", "Legislação Farmacêutica", "Oficina de Inovação"]
        },
        4: {
            "I": ["Estágio I", "Estágio II", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Estágio III", "Estágio IV", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        },
        5: {
            "I": ["Elaboração de Dissertação I", "Tópicos Especiais I", "Tópicos Especiais II", "Gestão de Farmácia", "Inovação", "Seminários de Investigação"],
            "II": ["Elaboração de Dissertação II", "Defesa de Dissertação", "Tópicos Especiais III", "Tópicos Especiais IV", "Empreendedorismo", "Oficina de Projetos"]
        }
    },
    8: {  # Psicologia
        1: {
            "I": ["Introdução à Psicologia", "Psicologia do Desenvolvimento I", "Neurociências I", "Estatística", "Inglês I", "Comunicação"],
            "II": ["Psicologia Social", "Psicologia do Desenvolvimento II", "Neurociências II", "Métodos de Investigação", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Psicopatologia I", "Psicologia da Personalidade", "Avaliação Psicológica I", "Psicologia Cognitiva", "Ética", "Gestão de Projetos"],
            "II": ["Psicopatologia II", "Psicoterapias", "Avaliação Psicológica II", "Psicologia da Saúde", "Neuropsicologia", "Empreendedorismo"]
        },
        3: {
            "I": ["Psicologia Clínica I", "Psicologia Organizacional", "Psicologia da Educação", "Intervenção em Crises", "Bioestatística", "Oficina de Inovação"],
            "II": ["Psicologia Clínica II", "Psicologia do Trabalho", "Psicologia Escolar", "Terapia Familiar", "Psicofarmacologia", "Legislação"]
        },
        4: {
            "I": ["Estágio I", "Estágio II", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Estágio III", "Estágio IV", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        },
        5: {
            "I": ["Elaboração de Dissertação I", "Tópicos Especiais I", "Tópicos Especiais II", "Psicologia Comunitária", "Inovação", "Seminários de Investigação"],
            "II": ["Elaboração de Dissertação II", "Defesa de Dissertação", "Tópicos Especiais III", "Tópicos Especiais IV", "Empreendedorismo", "Oficina de Projetos"]
        }
    },
    # ========== NEGÓCIOS ==========
    9: {  # Gestão de Empresas
        1: {
            "I": ["Introdução à Gestão", "Contabilidade I", "Matemática I", "Economia I", "Inglês I", "Comunicação"],
            "II": ["Gestão de Operações", "Contabilidade II", "Matemática II", "Economia II", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Marketing I", "Finanças I", "Recursos Humanos I", "Estatística", "Comportamento Organizacional", "Gestão de Projetos"],
            "II": ["Marketing II", "Finanças II", "Recursos Humanos II", "Sistemas de Informação", "Logística", "Empreendedorismo"]
        },
        3: {
            "I": ["Estratégia Empresarial", "Gestão Financeira Avançada", "Marketing Estratégico", "Ética e Sustentabilidade", "Gestão da Inovação", "Oficina de Inovação"],
            "II": ["Gestão Internacional", "Gestão de Riscos", "Consultoria", "Business Intelligence", "Liderança", "Gestão de Carreira"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    10: {  # Economia
        1: {
            "I": ["Microeconomia I", "Macroeconomia I", "Matemática I", "Contabilidade I", "Inglês I", "Comunicação"],
            "II": ["Microeconomia II", "Macroeconomia II", "Matemática II", "Contabilidade II", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Economia do Trabalho", "Economia Industrial", "Estatística", "Finanças", "História Económica", "Gestão de Projetos"],
            "II": ["Economia Monetária", "Economia Internacional", "Econometria I", "Política Económica", "Desenvolvimento Económico", "Empreendedorismo"]
        },
        3: {
            "I": ["Microeconomia Avançada", "Macroeconomia Avançada", "Econometria II", "Economia da Empresa", "Ética", "Oficina de Inovação"],
            "II": ["Economia da Educação", "Economia da Saúde", "Análise de Dados", "Gestão Financeira", "Business Intelligence", "Gestão de Carreira"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    11: {  # Marketing
        1: {
            "I": ["Fundamentos de Marketing", "Introdução à Gestão", "Matemática I", "Contabilidade I", "Inglês I", "Comunicação"],
            "II": ["Marketing Digital", "Comportamento do Consumidor", "Matemática II", "Contabilidade II", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Pesquisa de Marketing", "Gestão de Produto", "Gestão de Preços", "Distribuição", "Estatística", "Gestão de Projetos"],
            "II": ["Comunicação de Marketing", "Marketing Relacional", "Marketing de Serviços", "Gestão de Marcas", "Logística", "Empreendedorismo"]
        },
        3: {
            "I": ["Marketing Estratégico", "Gestão de Clientes", "Marketing Internacional", "Ética e Sustentabilidade", "Inovação", "Oficina de Inovação"],
            "II": ["Marketing Analytics", "E-commerce", "Gestão de Redes Sociais", "Branding", "Gestão de Carreira", "Seminários"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    12: {  # Contabilidade
        1: {
            "I": ["Introdução à Contabilidade", "Matemática I", "Economia I", "Inglês I", "Comunicação", "Informática I"],
            "II": ["Contabilidade Financeira", "Matemática II", "Economia II", "Inglês II", "Métodos de Pesquisa", "Informática II"]
        },
        2: {
            "I": ["Contabilidade de Custos", "Fiscalidade I", "Estatística", "Direito Fiscal", "Gestão de Projetos", "Empreendedorismo"],
            "II": ["Contabilidade de Gestão", "Fiscalidade II", "Auditoria I", "Análise de Demonstrações Financeiras", "Ética", "Gestão de Carreira"]
        },
        3: {
            "I": ["Contabilidade Avançada", "Fiscalidade III", "Auditoria II", "Controlo de Gestão", "Sistemas de Informação Contabilística", "Oficina de Inovação"],
            "II": ["Contabilidade Pública", "Consolidação de Contas", "Gestão Financeira", "Business Intelligence", "Ética Profissional", "Seminários"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    # ========== ARTES ==========
    13: {  # Artes Plásticas
        1: {
            "I": ["Desenho I", "Pintura I", "História da Arte I", "Escultura I", "Inglês I", "Comunicação"],
            "II": ["Desenho II", "Pintura II", "História da Arte II", "Escultura II", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Técnicas Mistas", "Gravura", "Fotografia I", "Teoria da Cor", "Gestão de Projetos", "Empreendedorismo"],
            "II": ["Instalação Artística", "Arte Contemporânea", "Curadoria", "Crítica de Arte", "Gestão de Carreira", "Oficina de Inovação"]
        },
        3: {
            "I": ["Arte Digital", "Performance", "Escultura Contemporânea", "Projeto Artístico I", "Ética e Legislação", "Seminários"],
            "II": ["Arte Pública", "Media Art", "Projeto Artístico II", "Gestão de Exposições", "Arteterapia", "Design Thinking"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    14: {  # Música
        1: {
            "I": ["Teoria Musical I", "História da Música I", "Prática Instrumental I", "Formação Auditiva I", "Inglês I", "Comunicação"],
            "II": ["Teoria Musical II", "História da Música II", "Prática Instrumental II", "Formação Auditiva II", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Harmonia I", "Composição I", "Regência I", "Música de Câmara I", "Gestão de Projetos", "Empreendedorismo"],
            "II": ["Harmonia II", "Composição II", "Regência II", "Música de Câmara II", "Gestão de Carreira", "Oficina de Inovação"]
        },
        3: {
            "I": ["Produção Musical", "Tecnologia Musical", "Música Eletrónica", "História da Música Contemporânea", "Ética", "Seminários"],
            "II": ["Trilha Sonora", "Música e Imagem", "Musicologia", "Projeto Musical", "Gestão de Eventos", "Design Thinking"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    15: {  # Design Gráfico
        1: {
            "I": ["Fundamentos do Design", "Desenho I", "Tipografia I", "Teoria da Cor", "Inglês I", "Comunicação"],
            "II": ["Desenho II", "Tipografia II", "História do Design I", "Ilustração", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Design Editorial", "Design de Identidade", "Fotografia I", "Software Gráfico I", "Gestão de Projetos", "Empreendedorismo"],
            "II": ["Design de Embalagem", "Design Digital", "Fotografia II", "Software Gráfico II", "Gestão de Carreira", "Oficina de Inovação"]
        },
        3: {
            "I": ["Design de Interface", "Animação", "Mídias Sociais", "Projeto Gráfico I", "Ética e Legislação", "Seminários"],
            "II": ["Design Sustentável", "Design Inclusivo", "Projeto Gráfico II", "Gestão de Marcas", "Inovação", "Design Thinking"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    },
    16: {  # Cinema e Audiovisual
        1: {
            "I": ["Introdução ao Cinema", "História do Cinema I", "Linguagem Audiovisual", "Fotografia I", "Inglês I", "Comunicação"],
            "II": ["Narrativa Audiovisual", "História do Cinema II", "Realização I", "Som I", "Inglês II", "Metodologia de Pesquisa"]
        },
        2: {
            "I": ["Argumento", "Direção de Atores", "Montagem I", "Produção I", "Gestão de Projetos", "Empreendedorismo"],
            "II": ["Documentário", "Montagem II", "Produção II", "Cinematografia", "Gestão de Carreira", "Oficina de Inovação"]
        },
        3: {
            "I": ["Animação", "Pós-Produção", "Efeitos Visuais", "Projeto Audiovisual I", "Ética e Legislação", "Seminários"],
            "II": ["Distribuição", "Marketing Cinematográfico", "Projeto Audiovisual II", "Gestão de Festivais", "Inovação", "Design Thinking"]
        },
        4: {
            "I": ["Projeto Final I", "Estágio I", "Tópicos Avançados I", "Tópicos Avançados II", "Gestão de Carreira", "Seminários"],
            "II": ["Projeto Final II", "Estágio II", "Tópicos Avançados III", "Tópicos Avançados IV", "Ética Profissional", "Defesa de Projeto"]
        }
    }
}

def popular_plano_curricular():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Criar tabelas (se não existirem)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            duracao_anos INTEGER NOT NULL,
            area TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anos_curso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curso_id INTEGER,
            numero INTEGER,
            FOREIGN KEY(curso_id) REFERENCES cursos(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semestres_curso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_id INTEGER,
            nome TEXT NOT NULL,  -- 'I' ou 'II'
            FOREIGN KEY(ano_id) REFERENCES anos_curso(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas_plano (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semestre_id INTEGER,
            codigo TEXT,
            nome TEXT NOT NULL,
            FOREIGN KEY(semestre_id) REFERENCES semestres_curso(id)
        )
    ''')
    conn.commit()

    # Limpar dados antigos (recarregar)
    cursor.execute("DELETE FROM disciplinas_plano")
    cursor.execute("DELETE FROM semestres_curso")
    cursor.execute("DELETE FROM anos_curso")
    cursor.execute("DELETE FROM cursos")
    conn.commit()

    # Inserir cursos
    for curso in cursos:
        cursor.execute(
            "INSERT INTO cursos (id, nome, duracao_anos, area) VALUES (?, ?, ?, ?)",
            (curso["id"], curso["nome"], curso["duracao_anos"], curso["area"])
        )

    # Inserir anos, semestres e disciplinas
    for curso_id, anos in disciplinas_por_curso.items():
        for ano_num, semestres in anos.items():
            # Inserir ano
            cursor.execute(
                "INSERT INTO anos_curso (curso_id, numero) VALUES (?, ?)",
                (curso_id, ano_num)
            )
            ano_id = cursor.lastrowid

            for semestre_nome, disciplinas in semestres.items():
                # Inserir semestre
                cursor.execute(
                    "INSERT INTO semestres_curso (ano_id, nome) VALUES (?, ?)",
                    (ano_id, semestre_nome)
                )
                semestre_id = cursor.lastrowid

                for disciplina in disciplinas:
                    # Gerar código simplificado (curso + ano + semestre + índice)
                    idx = disciplinas.index(disciplina) + 1
                    codigo = f"{curso_id}{ano_num}{semestre_nome}{idx:02d}"
                    cursor.execute(
                        "INSERT INTO disciplinas_plano (semestre_id, codigo, nome) VALUES (?, ?, ?)",
                        (semestre_id, codigo, disciplina)
                    )

    conn.commit()
    conn.close()
    print("✅ Plano curricular inserido com sucesso!")

if __name__ == "__main__":
    popular_plano_curricular()