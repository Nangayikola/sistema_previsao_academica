# Sistema de Previsão Académica

Este diretório contém a arquitetura distribuída do sistema:

* `servico_coleta`: API FastAPI, autenticação, banco SQLite e boletim;
* `servico_previsao`: consumidor RabbitMQ, treino automático e cálculo de risco;
* `dashboard`: interface Streamlit para professores e estudantes;
* `ml`: scripts auxiliares de preparação, treino e avaliação.

## Execução rápida

```powershell
docker compose up -d

cd servico_coleta
uvicorn app:app --port 8000 --reload

cd ..\servico_previsao
python app.py

cd ..\dashboard
streamlit run app.py
```

Instale as dependências de cada serviço com `pip install -r requirements.txt`. O serviço de previsão requer `scikit-learn` e `joblib` para treinar o modelo automático.

## Aprendizagem automática

Antes de processar uma mensagem, o serviço consulta as notas completas, treina um Random Forest e calcula a probabilidade de aprovação. O boletim mostra essa probabilidade e as métricas históricas da disciplina. Com poucos dados, é usado o fallback estatístico e o terminal informa `Modelo ML: fallback`.

Consulte `http://localhost:8000/health` para confirmar o estado da API e do banco.
