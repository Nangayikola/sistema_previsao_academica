from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./previsao.db"

engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Previsao(Base):
    __tablename__ = "previsoes"
    id = sa.Column(sa.Integer, primary_key=True)
    matricula = sa.Column(sa.String)
    disciplina_codigo = sa.Column(sa.String)
    risco = sa.Column(sa.String)
    media_estimada = sa.Column(sa.Float)
    recomendacao = sa.Column(sa.String)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

class NotaInput(BaseModel):
    disciplina_codigo: str
    nota: float
    faltas: int = 0
    data: str

class DadosAluno(BaseModel):
    matricula: str
    nome: str
    notas: List[NotaInput]

def calcular_risco(notas: List[float], faltas: int = 0, total_aulas: int = 40) -> tuple:
    if not notas:
        return "alto", 0.0, "Sem notas registadas."
    media = sum(notas) / len(notas)
    perc_faltas = faltas / total_aulas if total_aulas > 0 else 0
    
    if media < 5.0 or perc_faltas > 0.25:
        risco = "alto"
        rec = "Procurar monitoria e regularizar faltas imediatamente."
    elif media < 6.5:
        risco = "medio"
        rec = "Dedicar estudo extra e evitar faltas."
    else:
        risco = "baixo"
        rec = "Parabéns! Continue assim."
    
    return risco, round(media, 2), rec

@app.post("/prever")
async def prever_risco(dados: DadosAluno):
    # Agrupa notas e faltas por disciplina
    notas_por_disciplina = {}
    faltas_por_disciplina = {}
    
    for nota in dados.notas:
        # Captura faltas (considera o valor da primeira ocorrência por disciplina)
        if nota.disciplina_codigo not in faltas_por_disciplina:
            faltas_por_disciplina[nota.disciplina_codigo] = nota.faltas
        # Agrupa notas
        notas_por_disciplina.setdefault(nota.disciplina_codigo, []).append(nota.nota)

    resultados = []
    async with AsyncSessionLocal() as session:
        for disc_cod, lista_notas in notas_por_disciplina.items():
            faltas = faltas_por_disciplina.get(disc_cod, 0)
            risco, media, rec = calcular_risco(lista_notas, faltas)
            previsao = Previsao(
                matricula=dados.matricula,
                disciplina_codigo=disc_cod,
                risco=risco,
                media_estimada=media,
                recomendacao=rec
            )
            session.add(previsao)
            resultados.append({
                "disciplina": disc_cod,
                "risco": risco,
                "media_estimada": media,
                "recomendacao": rec
            })
        await session.commit()
    return {"resultados": resultados}

@app.on_event("startup")
async def startup():
    await init_db()