Sistema de Previsão Académica

Descrição: Sistema distribuído para prever o risco de reprovação e o baixo desempenho de alunos com base em notas e faltas, auxiliando instituições de ensino na tomada de decisão pedagógica. Oferece recomendações personalizadas de estudo e sugere áreas de carreira com base nas aptidões reais do estudante. Com autenticação JWT, o sistema distingue professores (que registam semestres e consultam todos os alunos) e estudantes (que apenas consultam o seu próprio boletim). Cada semestre é composto por 6 disciplinas, com previsão individual por disciplina e uma previsão agregada do semestre.

Tecnologias:

Backend (API): Python + FastAPI + Uvicorn

Interface: Streamlit (dashboard interativo)

Comunicação assíncrona: RabbitMQ (message broker)

Banco de dados: SQLite (centralizado)

Cliente RabbitMQ: Pika

ORM: SQLAlchemy + aiosqlite

Containerização: Docker + Docker Compose

Autenticação: JWT + bcrypt

Estrutura do projeto:

previsao_distribuida_http/
├── docker-compose.yml          # Orquestração do RabbitMQ
├── central.db                  # Banco de dados SQLite (criado automaticamente)
├── servico_coleta/             # API REST (FastAPI)
│   ├── app.py
│   └── requirements.txt
├── servico_previsao/           # Consumidor RabbitMQ (cálculo de risco)
│   ├── app.py
│   └── requirements.txt
└── dashboard/                  # Interface web (Streamlit)
    └── app.py

Como executar:

Clone o repositório: git clone https://github.com/Nangayikola/sistema_previsao_academica.git

Aceda à pasta do projeto: cd sistema_previsao_academica/previsao_distribuida_http

Suba o RabbitMQ com Docker Compose: docker compose up -d

Crie e ative os ambientes virtuais para cada serviço (coleta, previsão e dashboard) e instale as dependências (consulte o README.md completo para os comandos detalhados).

Inicie o serviço de previsão (consumidor): cd servico_previsao && python app.py

Inicie o serviço de coleta (API): cd servico_coleta && uvicorn app:app --port 8000 --reload

Inicie o dashboard: cd dashboard && streamlit run app.py

Acesse no navegador:

Dashboard: http://localhost:8501

Documentação da API: http://localhost:8000/docs

RabbitMQ (gestão): http://localhost:15672 (user: guest, pass: guest)

Como contribuir:

Faça um fork do projeto

Crie uma branch para sua alteração (git checkout -b minha-melhoria)

Commit as mudanças (git commit -m "Adiciona nova funcionalidade")

Faça push para a branch (git push origin minha-melhoria)

Abra um pull request

Desenvolvido por: Felisberto Nangayikola e Isabel Bota.