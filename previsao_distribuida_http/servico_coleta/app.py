from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import httpx
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = "sqlite+aiosqlite:///./coleta.db"

engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Aluno(Base):
    __tablename__ = "alunos"
    id = sa.Column(sa.Integer, primary_key=True)
    matricula = sa.Column(sa.String, unique=True)
    nome = sa.Column(sa.String)

class Nota(Base):
    __tablename__ = "notas"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_matricula = sa.Column(sa.String, sa.ForeignKey("alunos.matricula"))
    disciplina_codigo = sa.Column(sa.String)
    nota = sa.Column(sa.Float)
    faltas = sa.Column(sa.Integer, default=0) 
    data = sa.Column(sa.String)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()
PREVISAO_URL = "http://localhost:8001/prever"

class NotaInput(BaseModel):
    disciplina_codigo: str
    nota: float
    faltas: int = 0
    data: str

class DadosAluno(BaseModel):
    matricula: str
    nome: str
    notas: List[NotaInput]

@app.on_event("startup")
async def startup():
    await init_db()

@app.post("/aluno/dados")
async def receber_dados(dados: DadosAluno):
    async with AsyncSessionLocal() as session:
        # salvar aluno
        aluno = Aluno(matricula=dados.matricula, nome=dados.nome)
        session.add(aluno)
        for nota in dados.notas:
            nova_nota = Nota(
                aluno_matricula=dados.matricula,
                disciplina_codigo=nota.disciplina_codigo,
                nota=nota.nota,
                data=nota.data
            )
            session.add(nova_nota)
        await session.commit()

    # chamar serviço de previsão
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(PREVISAO_URL, json=dados.dict())
            response.raise_for_status()
            previsao = response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Serviço de previsão indisponível: {e}")

    return {"status": "dados recebidos", "previsao": previsao}