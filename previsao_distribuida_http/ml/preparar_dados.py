import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CSV = os.path.join(BASE_DIR, "ml", "dados_treino.csv")

def gerar_dados_sinteticos(n=1000):
    np.random.seed(42)
    dados = []
    for _ in range(n):
        # Média entre 2 e 18 (maioria entre 5 e 12)
        media = np.random.uniform(2, 18)
        # Faltas: maioritariamente baixas, mas com alguns casos extremos
        faltas = np.random.poisson(5)
        # Número de avaliações
        num_avaliacoes = np.random.randint(1, 7)
        # Desvio padrão das notas (0 a 5)
        desvio = np.random.uniform(0, 4)
        # Tendência (melhoria ou piora ao longo do tempo)
        tendencia = np.random.uniform(-3, 3)
        # Disciplina (1 a 18)
        disciplina_id = np.random.randint(1, 19)
        # Semestre (0=I, 1=II)
        semestre = np.random.randint(0, 2)

        # Regra realista para aprovação
        prob_aprov = 1 / (1 + np.exp(-(media - 5.5) / 2))
        if faltas > 15:
            prob_aprov *= 0.2
        if media > 12:
            prob_aprov = min(prob_aprov * 1.3, 0.95)
        if media < 4:
            prob_aprov *= 0.1
        aprovado = 1 if np.random.random() < prob_aprov else 0

        dados.append({
            'media': media,
            'faltas_totais': faltas,
            'num_avaliacoes': num_avaliacoes,
            'desvio_padrao': desvio,
            'tendencia': tendencia,
            'disciplina_id': disciplina_id,
            'semestre': semestre,
            'aprovado': aprovado
        })
    return pd.DataFrame(dados)

def main():
    print("📂 A gerar dados sintéticos com variabilidade...")
    df = gerar_dados_sinteticos(1000)
    print(f"📊 Total de registos: {len(df)}")
    print(f"🔹 Aprovados: {df['aprovado'].sum()} | Reprovados: {len(df) - df['aprovado'].sum()}")
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Dados guardados em: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()