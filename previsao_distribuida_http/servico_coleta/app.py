import os
import json
import jwt
import bcrypt
import pika
import sqlalchemy as sa
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

app = FastAPI(title="Serviço de Coleta de Dados Académicos")

# ============================================================================
# CONFIGURAÇÕES E CHAVES DE SEGURANÇA
# ============================================================================
SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-mudar-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'central.db')}"
print(f"📂 Serviço de Coleta a usar BD: {DATABASE_URL}")

# ============================================================================
# BANCO DE DADOS - ORM E MODELOS
# ============================================================================
engine = create_async_engine(DATABASE_URL, echo=False)
Base = declarative_base()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    username = sa.Column(sa.String, unique=True, nullable=False, index=True)
    password_hash = sa.Column(sa.String, nullable=False)
    role = sa.Column(sa.String, nullable=False)
    nome = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=True)


class AnoAcademico(Base):
    __tablename__ = "anos_academicos"
    id = sa.Column(sa.Integer, primary_key=True)
    nome = sa.Column(sa.String, unique=True, nullable=False)
    ativo = sa.Column(sa.Boolean, default=True)


class Semestre(Base):
    __tablename__ = "semestres"
    id = sa.Column(sa.Integer, primary_key=True)
    ano_academico_id = sa.Column(sa.Integer, sa.ForeignKey("anos_academicos.id"))
    nome = sa.Column(sa.String, nullable=False)  # Ex: "I" ou "II"
    ano_academico = sa.orm.relationship("AnoAcademico")


class Disciplina(Base):
    __tablename__ = "disciplinas"
    id = sa.Column(sa.Integer, primary_key=True)
    codigo = sa.Column(sa.String, unique=True, nullable=False)
    nome = sa.Column(sa.String, nullable=False)
    semestre_id = sa.Column(sa.Integer, sa.ForeignKey("semestres.id"))
    creditos = sa.Column(sa.Integer, default=0)
    semestre = sa.orm.relationship("Semestre")


class Nota(Base):
    __tablename__ = "notas"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    disciplina_id = sa.Column(sa.Integer, sa.ForeignKey("disciplinas.id"))
    parcial1 = sa.Column(sa.Float, nullable=True)
    parcial2 = sa.Column(sa.Float, nullable=True)
    exame = sa.Column(sa.Float, nullable=True)
    faltas = sa.Column(sa.Integer, default=0)
    ano_letivo = sa.Column(sa.String, nullable=False)


class Previsao(Base):
    __tablename__ = "previsoes"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    disciplina_id = sa.Column(sa.Integer, sa.ForeignKey("disciplinas.id"))
    ano_letivo = sa.Column(sa.String, nullable=False)
    media_parcial = sa.Column(sa.Float)
    media_final = sa.Column(sa.Float)
    risco = sa.Column(sa.String)
    recomendacao = sa.Column(sa.Text)
    data_calculo = sa.Column(sa.String)


class PrevisaoSemestre(Base):
    __tablename__ = "previsoes_semestre"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    ano_letivo = sa.Column(sa.String, nullable=False)
    semestre_nome = sa.Column(sa.String, nullable=False)
    media_global = sa.Column(sa.Float)
    total_faltas = sa.Column(sa.Integer)
    disciplinas_em_risco = sa.Column(sa.Integer)
    risco_global = sa.Column(sa.String)
    recomendacao_geral = sa.Column(sa.Text)
    data_calculo = sa.Column(sa.String)


# ============================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS E MIGRAÇÕES LEVES
# ============================================================================
async def add_column_if_not_exists(engine, table_name, column_def):
    async with engine.connect() as conn:
        result = await conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        column_name = column_def.split()[0]
        if column_name not in columns:
            await conn.execute(sa.text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))
            await conn.commit()
            print(f"✅ Coluna '{column_name}' adicionada à tabela '{table_name}'")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await add_column_if_not_exists(engine, "previsoes_semestre", "data_calculo TEXT")


# ============================================================================
# AUTENTICAÇÃO E UTILITÁRIOS DE SEGURANÇA
# ============================================================================
security = HTTPBearer()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Utilizador não encontrado")
        return user


async def get_current_professor(current_user: User = Depends(get_current_user)):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Apenas professores podem aceder a esta funcionalidade")
    return current_user


# ============================================================================
# SCHEMAS DE ENTRADA (PYDANTIC)
# ============================================================================
class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str
    nome: str
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class NotaSemestreInput(BaseModel):
    disciplina_codigo: str
    parcial1: Optional[float] = None
    parcial2: Optional[float] = None
    exame: Optional[float] = None
    faltas: int = 0


class DadosSemestreAluno(BaseModel):
    matricula: str
    ano_letivo: str
    semestre: str  # Ex: "I" ou "II"
    disciplinas: List[NotaSemestreInput]


# ============================================================================
# INTEGRAÇÃO RABBITMQ (FILA DE MENSAGENS)
# ============================================================================
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5679))


def publish_previsao_event(evento: dict):
    """Envia o evento para a fila 'previsao_queue' garantindo o encerramento da conexão."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT))
        channel = connection.channel()
        channel.queue_declare(queue="previsao_queue", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="previsao_queue",
            body=json.dumps(evento, ensure_ascii=False),
            properties=pika.BasicProperties(delivery_mode=2),  # Torna a mensagem persistente
        )
        connection.close()
        print(f"📡 Evento publicado na fila 'previsao_queue' para o aluno ID {evento.get('aluno_id')}")
    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem para o RabbitMQ: {e}")


# ============================================================================
# ENDPOINTS DA API
# ============================================================================
@app.post("/auth/register")
async def register(data: RegisterRequest):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            raise HTTPException(400, "Username já registado")
        hashed = hash_password(data.password)
        user = User(username=data.username, password_hash=hashed, role=data.role, nome=data.nome, email=data.email)
        session.add(user)
        await session.commit()
        return {"message": "Utilizador registado com sucesso"}


@app.post("/auth/login")
async def login(data: LoginRequest):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(401, "Credenciais inválidas")
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"access_token": token, "token_type": "bearer", "role": user.role, "nome": user.nome}


@app.post("/aluno/semestre")
async def registar_semestre(dados: DadosSemestreAluno, professor: User = Depends(get_current_professor)):
    async with AsyncSessionLocal() as session:
        result_aluno = await session.execute(
            sa.select(User).where(User.username == dados.matricula, User.role == "estudante")
        )
        aluno = result_aluno.scalar_one_or_none()
        if not aluno:
            raise HTTPException(404, "Aluno não encontrado")

        result_ano = await session.execute(sa.select(AnoAcademico).where(AnoAcademico.nome == dados.ano_letivo))
        ano_obj = result_ano.scalar_one_or_none()
        if not ano_obj:
            ano_obj = AnoAcademico(nome=dados.ano_letivo)
            session.add(ano_obj)
            await session.flush()

        result_sem = await session.execute(
            sa.select(Semestre).where(Semestre.ano_academico_id == ano_obj.id, Semestre.nome == dados.semestre)
        )
        sem_obj = result_sem.scalar_one_or_none()
        if not sem_obj:
            sem_obj = Semestre(ano_academico_id=ano_obj.id, nome=dados.semestre)
            session.add(sem_obj)
            await session.flush()

        disciplinas_evento = []

        for item in dados.disciplinas:
            result_disc = await session.execute(
                sa.select(Disciplina).where(Disciplina.codigo == item.disciplina_codigo)
            )
            disc = result_disc.scalar_one_or_none()
            if not disc:
                disc = Disciplina(codigo=item.disciplina_codigo, nome=item.disciplina_codigo, semestre_id=sem_obj.id)
                session.add(disc)
                await session.flush()

            result_nota = await session.execute(
                sa.select(Nota).where(
                    Nota.aluno_id == aluno.id,
                    Nota.disciplina_id == disc.id,
                    Nota.ano_letivo == dados.ano_letivo,
                )
            )
            nota = result_nota.scalar_one_or_none()
            if nota:
                nota.parcial1 = item.parcial1
                nota.parcial2 = item.parcial2
                nota.exame = item.exame
                nota.faltas = item.faltas
            else:
                nota = Nota(
                    aluno_id=aluno.id,
                    disciplina_id=disc.id,
                    parcial1=item.parcial1,
                    parcial2=item.parcial2,
                    exame=item.exame,
                    faltas=item.faltas,
                    ano_letivo=dados.ano_letivo,
                )
                session.add(nota)

            # Prepara a lista para incluir no payload transmitido para o RabbitMQ
            disciplinas_evento.append({
                "codigo": item.disciplina_codigo,
                "parcial1": item.parcial1,
                "parcial2": item.parcial2,
                "exame": item.exame,
                "faltas": item.faltas
            })

        await session.commit()

        # Publica na fila assíncrona com os dados detalhados que o serviço de previsão necessita
        evento = {
            "aluno_id": aluno.id,
            "matricula": aluno.username,
            "ano_letivo": dados.ano_letivo,
            "semestre": dados.semestre,
            "disciplinas": disciplinas_evento,
        }
        publish_previsao_event(evento)

    return {"status": "sucesso", "mensagem": f"Dados do semestre {dados.semestre} de {dados.ano_letivo} registados e enviados para cálculo."}


@app.get("/aluno/boletim/{ano_letivo}/{semestre}")
async def boletim_semestre(
    ano_letivo: str,
    semestre: str,
    current_user: User = Depends(get_current_user),
    matricula: Optional[str] = None,
):
    if current_user.role == "estudante":
        aluno_username = current_user.username
    else:
        if not matricula:
            raise HTTPException(400, "Para professores, forneça a matrícula do aluno")
        aluno_username = matricula

    async with AsyncSessionLocal() as session:
        result_aluno = await session.execute(
            sa.select(User).where(User.username == aluno_username, User.role == "estudante")
        )
        aluno = result_aluno.scalar_one_or_none()
        if not aluno:
            raise HTTPException(404, "Aluno não encontrado")

        result_sem = await session.execute(
            sa.select(Semestre).join(AnoAcademico).where(AnoAcademico.nome == ano_letivo, Semestre.nome == semestre)
        )
        sem_obj = result_sem.scalar_one_or_none()
        if not sem_obj:
            return {"ano_letivo": ano_letivo, "semestre": semestre, "disciplinas": [], "resumo": None}

        rows = await session.execute(
            sa.select(Disciplina, Nota)
            .outerjoin(
                Nota,
                (Nota.disciplina_id == Disciplina.id)
                & (Nota.aluno_id == aluno.id)
                & (Nota.ano_letivo == ano_letivo),
            )
            .where(Disciplina.semestre_id == sem_obj.id)
        )

        disciplinas_data = []
        total_notas = 0
        total_faltas = 0
        count = 0
        disciplinas_em_risco = 0

        for disc, nota in rows.all():
            if nota is None:
                nota = Nota(parcial1=None, parcial2=None, exame=None, faltas=0)
            
            media_final = None
            if nota.parcial1 is not None and nota.parcial2 is not None and nota.exame is not None:
                media_parcial = (nota.parcial1 + nota.parcial2) / 2
                media_final = media_parcial * 0.4 + nota.exame * 0.6

            result_previsao = await session.execute(
                sa.select(Previsao).where(
                    Previsao.aluno_id == aluno.id,
                    Previsao.disciplina_id == disc.id,
                    Previsao.ano_letivo == ano_letivo,
                )
            )
            previsao = result_previsao.scalars().first()

            disciplinas_data.append({
                "codigo": disc.codigo,
                "disciplina": disc.nome,
                "parcial1": nota.parcial1,
                "parcial2": nota.parcial2,
                "exame": nota.exame,
                "media_final": round(media_final, 2) if media_final is not None else None,
                "faltas": nota.faltas,
                "risco": previsao.risco if previsao else None,
                "recomendacao": previsao.recomendacao if previsao else None,
            })

            if media_final is not None:
                total_notas += media_final
                count += 1
            total_faltas += nota.faltas
            if previsao and previsao.risco in ["ALTO", "MEDIO", "alto", "medio"]:
                disciplinas_em_risco += 1

        resumo = {
            "media_global": round(total_notas / count, 2) if count > 0 else None,
            "total_faltas": total_faltas,
            "disciplinas_em_risco": disciplinas_em_risco,
            "risco_global": None,
            "recomendacao_geral": None,
            "data_calculo": None,
        }

        result_agreg = await session.execute(
            sa.select(PrevisaoSemestre).where(
                PrevisaoSemestre.aluno_id == aluno.id,
                PrevisaoSemestre.ano_letivo == ano_letivo,
                PrevisaoSemestre.semestre_nome == semestre,
            )
        )
        agreg = result_agreg.scalars().first()
        if agreg:
            resumo["risco_global"] = agreg.risco_global
            resumo["recomendacao_geral"] = agreg.recomendacao_geral
            resumo["data_calculo"] = agreg.data_calculo

        return {"ano_letivo": ano_letivo, "semestre": semestre, "disciplinas": disciplinas_data, "resumo": resumo}


# ---- CONSULTAS AUXILIARES ----
@app.get("/alunos")
async def listar_alunos(current_user: User = Depends(get_current_user)):
    if current_user.role != "professor":
        raise HTTPException(403, "Apenas professores podem listar alunos")
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.role == "estudante"))
        alunos = result.scalars().all()
        return [{"id": a.id, "username": a.username, "nome": a.nome} for a in alunos]


@app.get("/disciplinas")
async def listar_disciplinas(current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(Disciplina))
        disciplinas = result.scalars().all()
        return [{"codigo": d.codigo, "nome": d.nome, "semestre_id": d.semestre_id, "creditos": d.creditos} for d in disciplinas]


@app.get("/anos")
async def listar_anos(current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(AnoAcademico))
        anos = result.scalars().all()
        return [{"id": a.id, "nome": a.nome} for a in anos]


@app.get("/cursos")
async def listar_cursos(current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.text("SELECT id, nome, duracao_anos, area FROM cursos ORDER BY area, nome"))
        cursos = result.mappings().all()
        return [dict(row) for row in cursos]


@app.get("/anos_curso/{curso_id}")
async def listar_anos_curso(curso_id: int, current_user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            sa.text("SELECT numero FROM anos_curso WHERE curso_id = :curso_id ORDER BY numero"),
            {"curso_id": curso_id},
        )
        anos = result.scalars().all()
        return [{"numero": num} for num in anos]


@app.get("/disciplinas_plano/{curso_id}/{ano_num}/{semestre_nome}")
async def listar_disciplinas_plano(
    curso_id: int, ano_num: int, semestre_nome: str, current_user: User = Depends(get_current_user)
):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            sa.text("""
                SELECT dp.nome, dp.codigo
                FROM disciplinas_plano dp
                JOIN semestres_curso sc ON dp.semestre_id = sc.id
                JOIN anos_curso ac ON sc.ano_id = ac.id
                WHERE ac.curso_id = :curso_id AND ac.numero = :ano_num AND sc.nome = :semestre_nome
                ORDER BY dp.nome
            """),
            {"curso_id": curso_id, "ano_num": ano_num, "semestre_nome": semestre_nome},
        )
        disciplinas = result.mappings().all()
        return [dict(d) for d in disciplinas]


# ============================================================================
# EVENTO DE INICIALIZAÇÃO DA APLICAÇÃO
# ============================================================================
@app.on_event("startup")
async def startup():
    await init_db()