from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ---- Banco SQLite centralizado (caminho absoluto para a raiz do projeto) ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = "sqlite+aiosqlite:///C:/Users/felis/OneDrive/Documentos/GitHub/sistema_previsao_academica/previsao_distribuida_http/central.db"
print(f"📂 Serviço de Coleta a usar: {DATABASE_URL}")
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ---- Modelos ----
class Aluno(Base):
    __tablename__ = "alunos"
    id = sa.Column(sa.Integer, primary_key=True)
    matricula = sa.Column(sa.String, unique=True, nullable=False)
    nome = sa.Column(sa.String, nullable=False)

class Disciplina(Base):
    __tablename__ = "disciplinas"
    id = sa.Column(sa.Integer, primary_key=True)
    codigo = sa.Column(sa.String, unique=True, nullable=False)

class Nota(Base):
    __tablename__ = "notas"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_matricula = sa.Column(sa.String, sa.ForeignKey("alunos.matricula"))
    disciplina_codigo = sa.Column(sa.String, sa.ForeignKey("disciplinas.codigo"))
    nota = sa.Column(sa.Float)
    faltas = sa.Column(sa.Integer, default=0)
    data_avaliacao = sa.Column(sa.String)

class Previsao(Base):
    __tablename__ = "previsoes"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_matricula = sa.Column(sa.String, sa.ForeignKey("alunos.matricula"))
    disciplina_codigo = sa.Column(sa.String, sa.ForeignKey("disciplinas.codigo"))
    risco = sa.Column(sa.String)
    media_estimada = sa.Column(sa.Float)
    recomendacao = sa.Column(sa.Text)
    data_calculo = sa.Column(sa.String)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---- Modelos de entrada ----
class NotaInput(BaseModel):
    disciplina_codigo: str
    nota: float
    faltas: int = 0
    data: str

class DadosAluno(BaseModel):
    matricula: str
    nome: str
    notas: List[NotaInput]

# ---- RabbitMQ ----
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
def get_rabbit_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='previsao_queue', durable=True)
    return channel

@app.on_event("startup")
async def startup():
    await init_db()

@app.post("/aluno/dados")
async def receber_dados(dados: DadosAluno):
    async with AsyncSessionLocal() as session:
        # Inserir/atualizar aluno
        aluno = Aluno(matricula=dados.matricula, nome=dados.nome)
        await session.merge(aluno)
        
        for nota in dados.notas:
            # Verifica se a disciplina já existe (evita UNIQUE constraint)
            result = await session.execute(
                sa.select(Disciplina).where(Disciplina.codigo == nota.disciplina_codigo)
            )
            disciplina_existente = result.scalar_one_or_none()
            if not disciplina_existente:
                disc = Disciplina(codigo=nota.disciplina_codigo)
                session.add(disc)
            
            # Inserir nota
            nova_nota = Nota(
                aluno_matricula=dados.matricula,
                disciplina_codigo=nota.disciplina_codigo,
                nota=nota.nota,
                faltas=nota.faltas,
                data_avaliacao=nota.data
            )
            session.add(nova_nota)
        await session.commit()

    channel = get_rabbit_channel()
    evento = {
        "matricula": dados.matricula,
        "disciplinas": [{"codigo": n.disciplina_codigo} for n in dados.notas]
    }
    channel.basic_publish(exchange='', routing_key='previsao_queue', body=json.dumps(evento))
    channel.connection.close()

    return {"status": "aceite", "message": "Dados recebidos e em processamento"}

@app.get("/alunos")
async def listar_alunos():
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(Aluno))
        alunos = result.scalars().all()
        return [{"matricula": a.matricula, "nome": a.nome} for a in alunos]

@app.get("/notas/{matricula}")
async def listar_notas(matricula: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(Nota).where(Nota.aluno_matricula == matricula))
        notas = result.scalars().all()
        return [{"disciplina": n.disciplina_codigo, "nota": n.nota, "faltas": n.faltas, "data": n.data_avaliacao} for n in notas]

@app.get("/previsoes/{matricula}")
async def listar_previsoes(matricula: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(Previsao).where(Previsao.aluno_matricula == matricula))
        prevs = result.scalars().all()
        return [{"disciplina": p.disciplina_codigo, "risco": p.risco, "media_estimada": p.media_estimada, "recomendacao": p.recomendacao, "data": p.data_calculo} for p in prevs]