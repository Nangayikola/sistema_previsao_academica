"""
Script para avaliar o modelo guardado com novos dados ou teste.
"""
import pandas as pd
import joblib
import os
from sklearn.metrics import classification_report, accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'ml', 'dados_treino.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'modelo_previsao.pkl')

# Carregar modelo
model = joblib.load(MODEL_PATH)
print(f"🧠 Modelo carregado de: {MODEL_PATH}")

# Carregar dados (pode ser um conjunto de validação separado)
df = pd.read_csv(DATA_PATH)

# Separar features e target (mesmas colunas do treino)
exclude_cols = ['aprovado', 'aluno_id', 'disciplina_id', 'semestre']
feature_cols = [col for col in df.columns if col not in exclude_cols]
X = df[feature_cols]
y = df['aprovado']

y_pred = model.predict(X)
print("\n📊 Avaliação no conjunto completo:")
print(classification_report(y, y_pred))
print(f"✅ Acurácia: {accuracy_score(y, y_pred):.4f}")