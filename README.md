# 🎓 Sistema de Previsão Académica

## 📌 Descrição
O **Sistema de Previsão Académica** é uma plataforma distribuída concebida para prever o risco de reprovação e o baixo desempenho de alunos com base nas suas notas e faltas, auxiliando as instituições de ensino na tomada de decisões pedagógicas preventivas. 

O sistema oferece recomendações personalizadas de estudo e sugere áreas de carreira alinhadas com as aptidões reais do estudante. Com suporte a autenticação via JWT, a plataforma distingue os perfis de acesso:
* **Professores:** Permite o registo de semestres, atribuição de notas/faltas e consulta de relatórios de todos os alunos.
* **Estudantes:** Permite o acesso e consulta exclusiva ao seu próprio boletim e diagnósticos preditivos.

Cada semestre é composto por 6 disciplinas, contando com previsão individualizada por disciplina e uma previsão global agregada para o semestre.

## 🤖 Aprendizagem Automática

O serviço de previsão treina automaticamente um `RandomForestClassifier` com os resultados completos existentes na tabela `notas`. O treino é executado antes do processamento de novas notas e usa:

* média das avaliações;
* faltas e número de avaliações realizadas;
* desvio entre as notas e tendência de evolução;
* disciplina e resultado final histórico.

O modelo calcula a probabilidade de aprovação, que é combinada com os indicadores financeiros, participação, trabalhos de investigação e histórico do estudante. A probabilidade fica registada em `previsoes.probabilidade_aprovacao_ml` e aparece no boletim.

Quando existem menos de 12 exemplos completos ou apenas uma classe de resultado, o sistema usa o fallback estatístico e informa essa condição. Assim, poucos dados não são tratados como um modelo confiável.

O histórico da disciplina também é recalculado no momento da consulta do boletim. Isso permite comparar estudantes que cursaram a mesma disciplina, mesmo no mesmo ano letivo.

---

## 🛠️ Tecnologias Utilizadas

* **Backend (API):** Python + FastAPI + Uvicorn
* **Interface do Utilizador:** Streamlit (Dashboard Interativo)
* **Comunicação Assíncrona:** RabbitMQ (Message Broker)
* **Cliente RabbitMQ:** Pika
* **Banco de Dados & ORM:** SQLite (Centralizado) + SQLAlchemy + aiosqlite
* **Autenticação e Segurança:** JWT (JSON Web Tokens) + bcrypt
* **Containerização:** Docker + Docker Compose

---

## 📁 Estrutura do Projeto

```text
previsao_distribuida_http/
├── docker-compose.yml          # Orquestração do serviço RabbitMQ
├── central.db                  # Banco de dados SQLite (gerado automaticamente)
├── servico_coleta/             # API REST (FastAPI)
│   ├── app.py
│   └── requirements.txt
├── servico_previsao/           # Consumidor RabbitMQ (cálculo preditivo de risco)
│   ├── app.py
│   └── requirements.txt
└── dashboard/                  # Interface Web (Streamlit)
    └── app.py
```

O banco guarda ainda as métricas usadas para explicar cada previsão: `score_risco`, `taxa_aprovacao_historica`, `media_historica`, `amostras_historicas` e `probabilidade_aprovacao_ml`.

🚀 Como Executar o Projeto
1. Clonar o Repositório e Aceder à Pasta
git clone [https://github.com/Nangayikola/sistema_previsao_academica.git](https://github.com/Nangayikola/sistema_previsao_academica.git)
cd sistema_previsao_academica/previsao_distribuida_http

2. Iniciar o Broker de Mensagens (RabbitMQ)
Certifique-se de que tem o Docker instalado e a executar:
docker compose up -d

3. Configurar os Ambientes Virtuais e Dependências
Crie e ative o ambiente virtual para cada serviço antes de instalar as dependências de cada pasta (servico_coleta, servico_previsao e dashboard):
# Exemplo de criação e instalação para um módulo:
python -m venv venv
source venv/bin/activate  # No Windows use: venv\Scripts\activate
pip install -r requirements.txt

4. Executar os Serviços
4.1 Iniciar o Serviço de Previsão (Consumidor RabbitMQ):
cd servico_previsao
python app.py

4.2 Iniciar o Serviço de Coleta (API FastAPI):
cd servico_coleta
uvicorn app:app --port 8000 --reload

4.3 Iniciar o Dashboard (Streamlit):
cd dashboard
streamlit run app.py

5. Verificar o estado da API
GET http://localhost:8000/health

Uma resposta com `"status": "ok"` confirma que a API e o banco estão acessíveis. O consumidor de previsão informa no terminal `Modelo ML: ativo` quando treinou com dados suficientes; caso contrário, informa `fallback`.

## ⚠️ Limitações Atuais

* A aprendizagem usa os resultados completos que já existem no banco; a qualidade melhora à medida que novos semestres são registados.
* O modelo é retreinado em memória ao processar novas notas e não cria ainda um ficheiro versionado do modelo.
* A previsão é apoio pedagógico e não substitui a decisão académica oficial.

🤝 Como Contribuir
Faça um Fork do projeto

1. Crie uma nova branch para a sua funcionalidade:
git checkout -b minha-melhoria

2. Submeta as suas alterações (Commit):
git commit -m "Adiciona nova funcionalidade"

3. Envie para a sua branch (Push):
git push origin minha-melhoria

4. Abra um Pull Request

👨‍💻 Autores & Desenvolvedores
Desenvolvido por: Eng. Felisberto Nangayikola e Engª. Isabel Bota.