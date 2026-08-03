Sistema de Previsão Académica

Descrição:
Sistema distribuído para prever risco de reprovação e baixo desempenho de alunos com base em notas e faltas, auxiliando instituições de ensino na tomada de decisão pedagógica. Oferece recomendações personalizadas de estudo e sugere áreas de carreira com base nas aptidões reais do estudante.

Tecnologias:
- Backend (API): Python + FastAPI + Uvicorn
- Interface: Streamlit (dashboard interativo)
- Comunicação assíncrona: RabbitMQ (message broker)
- Banco de dados: SQLite (centralizado)
- Cliente RabbitMQ: Pika
- ORM: SQLAlchemy + aiosqlite
- Containerização: Docker + Docker Compose

Estrutura do projeto:
previsao_distribuida_http/
├── docker-compose.yml       # Orquestração do RabbitMQ
├── central.db               # Banco de dados SQLite (criado automaticamente)
├── servico_coleta/          # API REST (FastAPI)
│   ├── app.py
│   └── requirements.txt
├── servico_previsao/        # Consumidor RabbitMQ (cálculo de risco)
│   ├── app.py
│   └── requirements.txt
└── dashboard/               # Interface web (Streamlit)
    └── app.py

Como executar:
1. Clone o repositório: git clone https://github.com/Nangayikola/sistema_previsao_academica.git
2. Aceda à pasta do projeto: cd sistema_previsao_academica/previsao_distribuida_http
3. Suba o RabbitMQ com Docker Compose: docker compose up -d
4. Crie e ative os ambientes virtuais para cada serviço (coleta, previsão e dashboard) e instale as dependências (consulte o README.md completo para os comandos detalhados).
5. Inicie o serviço de previsão (consumidor): cd servico_previsao && python app.py
6. Inicie o serviço de coleta (API): cd servico_coleta && uvicorn app:app --port 8000 --reload
7. Inicie o dashboard: cd dashboard && streamlit run app.py
8. Acesse no navegador: Dashboard: http://localhost:8501 | Documentação da API: http://localhost:8000/docs | RabbitMQ (gestão): http://localhost:15672 (user: guest, pass: guest)

Como contribuir:
- Faça um fork do projeto
- Crie uma branch para sua alteração (git checkout -b minha-melhoria)
- Commit as mudanças (git commit -m "Adiciona nova funcionalidade")
- Faça push para a branch (git push origin minha-melhoria)
- Abra um pull request