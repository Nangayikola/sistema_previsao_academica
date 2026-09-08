import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "ml", "dados_treino.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "modelo_previsao.pkl")

def main():
    if not os.path.exists(CSV_PATH):
        print("❌ Ficheiro de dados não encontrado. Execute primeiro preparar_dados.py")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"📊 Dados carregados: {len(df)} registos")

    # Features e target
    features = ['media', 'faltas_totais', 'num_avaliacoes', 'desvio_padrao', 'tendencia', 'disciplina_id', 'semestre']
    X = df[features]
    y = df['aprovado']

    # Divisão treino/teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Treino
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    # Avaliação
    y_pred = model.predict(X_test)
    print("\n📈 Relatório de Classificação:")
    print(classification_report(y_test, y_pred))
    print(f"✅ Acurácia: {accuracy_score(y_test, y_pred):.4f}")
    print(f"📊 Matriz de Confusão:\n{confusion_matrix(y_test, y_pred)}")

    # Guardar modelo
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Modelo guardado em: {MODEL_PATH}")
    print("📌 Importância das features:")
    for feat, imp in zip(features, model.feature_importances_):
        print(f"   {feat}: {imp:.4f}")

if __name__ == "__main__":
    main()