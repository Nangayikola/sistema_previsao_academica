from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import pika
import json
import os
from dotenv import load_dotenv
import jwt
import bcrypt
from datetime import datetime, timedelta
import uuid

load_dotenv()

app = FastAPI()

# ---- Configuração JWT ----
SECRET_KEY = os.getenv("SECRET_KEY", "chave-secreta-mudar-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# ---- Banco SQLite centralizado ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'central.db')}"
print(f"📂 Serviço de Coleta a usar: {DATABASE_URL}")
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ---- Modelos ----
class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    username = sa.Column(sa.String, unique=True, nullable=False, index=True)
    password_hash = sa.Column(sa.String, nullable=False)
    role = sa.Column(sa.String, nullable=False)  # 'estudante' ou 'professor'
    nome = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=True)

class Disciplina(Base):
    __tablename__ = "disciplinas"
    id = sa.Column(sa.Integer, primary_key=True)
    codigo = sa.Column(sa.String, unique=True, nullable=False)
    nome = sa.Column(sa.String, nullable=False)
    semestre = sa.Column(sa.String, nullable=False)  # ex: "2025.1"
    creditos = sa.Column(sa.Integer, default=0)

class Nota(Base):
    __tablename__ = "notas"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    disciplina_id = sa.Column(sa.Integer, sa.ForeignKey("disciplinas.id"))
    nota = sa.Column(sa.Float)
    faltas = sa.Column(sa.Integer, default=0)
    semestre = sa.Column(sa.String, nullable=False)
    data_avaliacao = sa.Column(sa.String, nullable=True)

class Previsao(Base):
    __tablename__ = "previsoes"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    disciplina_id = sa.Column(sa.Integer, sa.ForeignKey("disciplinas.id"))
    semestre = sa.Column(sa.String, nullable=False)
    risco = sa.Column(sa.String)  # alto, medio, baixo
    media_estimada = sa.Column(sa.Float)
    recomendacao = sa.Column(sa.Text)
    data_calculo = sa.Column(sa.String)

class PrevisaoSemestre(Base):
    __tablename__ = "previsoes_semestre"
    id = sa.Column(sa.Integer, primary_key=True)
    aluno_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"))
    semestre = sa.Column(sa.String, nullable=False)
    media_global = sa.Column(sa.Float)
    total_faltas = sa.Column(sa.Integer)
    disciplinas_em_risco = sa.Column(sa.Integer)
    risco_global = sa.Column(sa.String)  # alto, medio, baixo
    recomendacao_geral = sa.Column(sa.Text)
    data_calculo = sa.Column(sa.String)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---- Autenticação ----
security = HTTPBearer()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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

# ---- Modelos de entrada ----
class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str  # 'estudante' ou 'professor'
    nome: str
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class NotaSemestreInput(BaseModel):
    disciplina_codigo: str
    nota: float
    faltas: int = 0

class DadosSemestreAluno(BaseModel):
    matricula: str  # username do aluno
    semestre: str  # ex: "2025.1"
    disciplinas: List[NotaSemestreInput]

# ---- RabbitMQ ----
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
def get_rabbit_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='previsao_queue', durable=True)
    return channel

# ---- Endpoints de Autenticação ----
@app.post("/auth/register")
async def register(data: RegisterRequest):
    # Verifica se o username já existe
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username já registado")
        
        # Cria utilizador
        hashed = hash_password(data.password)
        user = User(
            username=data.username,
            password_hash=hashed,
            role=data.role,
            nome=data.nome,
            email=data.email
        )
        session.add(user)
        await session.commit()
        return {"message": "Utilizador registado com sucesso"}

@app.post("/auth/login")
async def login(data: LoginRequest):
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.username == data.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"access_token": token, "token_type": "bearer", "role": user.role, "nome": user.nome}

# ---- Endpoints de Registo de Semestre (apenas professores) ----
@app.post("/aluno/semestre")
async def registar_semestre(dados: DadosSemestreAluno, professor: User = Depends(get_current_professor)):
    async with AsyncSessionLocal() as session:
        # Busca o aluno (username = matricula)
        result = await session.execute(sa.select(User).where(User.username == dados.matricula, User.role == "estudante"))
        aluno = result.scalar_one_or_none()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Para cada disciplina, insere ou atualiza nota
        for item in dados.disciplinas:
            # Busca ou cria disciplina
            result_disc = await session.execute(
                sa.select(Disciplina).where(Disciplina.codigo == item.disciplina_codigo)
            )
            disciplina = result_disc.scalar_one_or_none()
            if not disciplina:
                # Cria disciplina com semestre (pode ser melhor definir separadamente)
                disciplina = Disciplina(
                    codigo=item.disciplina_codigo,
                    nome=item.disciplina_codigo,  # placeholder
                    semestre=dados.semestre
                )
                session.add(disciplina)
                await session.flush()
            
            # Verifica se já existe nota para este aluno, disciplina e semestre
            result_nota = await session.execute(
                sa.select(Nota).where(
                    Nota.aluno_id == aluno.id,
                    Nota.disciplina_id == disciplina.id,
                    Nota.semestre == dados.semestre
                )
            )
            nota_existente = result_nota.scalar_one_or_none()
            if nota_existente:
                nota_existente.nota = item.nota
                nota_existente.faltas = item.faltas
            else:
                nova_nota = Nota(
                    aluno_id=aluno.id,
                    disciplina_id=disciplina.id,
                    nota=item.nota,
                    faltas=item.faltas,
                    semestre=dados.semestre,
                    data_avaliacao=datetime.now().isoformat()
                )
                session.add(nova_nota)
        
        await session.commit()
    
    # Publicar mensagem no RabbitMQ
    channel = get_rabbit_channel()
    evento = {
        "aluno_id": aluno.id,
        "matricula": aluno.username,
        "semestre": dados.semestre,
        "disciplinas": [{"codigo": d.disciplina_codigo} for d in dados.disciplinas]
    }
    channel.basic_publish(exchange='', routing_key='previsao_queue', body=json.dumps(evento))
    channel.connection.close()
    
    return {"status": "aceite", "message": f"Dados do semestre {dados.semestre} registados e em processamento"}

# ---- Endpoint de Consulta de Boletim (estudante vê os seus dados, professor vê de qualquer aluno) ----
@app.get("/aluno/boletim/{semestre}")
async def boletim_semestre(semestre: str, current_user: User = Depends(get_current_user), matricula: Optional[str] = None):
    # Se for estudante, usa a própria matrícula; se for professor, pode passar matricula como query param
    if current_user.role == "estudante":
        aluno_username = current_user.username
    else:
        if not matricula:
            raise HTTPException(status_code=400, detail="Para professores, é necessário fornecer matricula como query param")
        aluno_username = matricula
    
    async with AsyncSessionLocal() as session:
        # Busca o aluno
        result_aluno = await session.execute(
            sa.select(User).where(User.username == aluno_username, User.role == "estudante")
        )
        aluno = result_aluno.scalar_one_or_none()
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
        
        # Busca todas as notas do aluno no semestre
        result_notas = await session.execute(
            sa.select(Nota, Disciplina)
            .join(Disciplina, Nota.disciplina_id == Disciplina.id)
            .where(Nota.aluno_id == aluno.id, Nota.semestre == semestre)
        )
        notas = result_notas.all()
        
        if not notas:
            return {"semestre": semestre, "disciplinas": [], "resumo": None}
        
        disciplinas_data = []
        total_notas = 0
        total_faltas = 0
        count = 0
        disciplinas_em_risco = 0
        
        for nota, disciplina in notas:
            # Busca previsão para esta disciplina e semestre
            result_previsao = await session.execute(
                sa.select(Previsao).where(
                    Previsao.aluno_id == aluno.id,
                    Previsao.disciplina_id == disciplina.id,
                    Previsao.semestre == semestre
                )
            )
            previsao = result_previsao.scalar_one_or_none()
            
            disciplinas_data.append({
                "disciplina": disciplina.nome,
                "codigo": disciplina.codigo,
                "nota": nota.nota,
                "faltas": nota.faltas,
                "risco": previsao.risco if previsao else None,
                "media_estimada": previsao.media_estimada if previsao else None,
                "recomendacao": previsao.recomendacao if previsao else None
            })
            
            total_notas += nota.nota
            total_faltas += nota.faltas
            count += 1
            if previsao and previsao.risco in ["alto", "medio"]:
                disciplinas_em_risco += 1
        
        media_global = total_notas / count if count > 0 else 0
        
        # Busca previsão agregada (se já tiver sido calculada)
        result_agregado = await session.execute(
            sa.select(PrevisaoSemestre).where(
                PrevisaoSemestre.aluno_id == aluno.id,
                PrevisaoSemestre.semestre == semestre
            )
        )
        previsao_agregada = result_agregado.scalar_one_or_none()
        
        resumo = {
            "media_global": round(media_global, 2),
            "total_faltas": total_faltas,
            "disciplinas_em_risco": disciplinas_em_risco,
            "risco_global": previsao_agregada.risco_global if previsao_agregada else None,
            "recomendacao_geral": previsao_agregada.recomendacao_geral if previsao_agregada else None,
            "data_calculo": previsao_agregada.data_calculo if previsao_agregada else None
        }
        
        return {"semestre": semestre, "disciplinas": disciplinas_data, "resumo": resumo}

# ---- Endpoints legados (mantidos para compatibilidade, mas podem ser descontinuados) ----
@app.post("/aluno/dados")
async def receber_dados_legado(dados: DadosAluno, professor: User = Depends(get_current_professor)):
    # Adapta para o novo modelo (sem semestre, usa semestre default)
    # Vamos manter apenas para não quebrar testes antigos
    return {"status": "descontinuado", "message": "Use /aluno/semestre"}

@app.get("/alunos")
async def listar_alunos(current_user: User = Depends(get_current_user)):
    if current_user.role != "professor":
        raise HTTPException(status_code=403, detail="Apenas professores podem listar alunos")
    async with AsyncSessionLocal() as session:
        result = await session.execute(sa.select(User).where(User.role == "estudante"))
        alunos = result.scalars().all()
        return [{"id": a.id, "username": a.username, "nome": a.nome} for a in alunos]

@app.get("/notas/{matricula}")
async def listar_notas_legado(matricula: str, current_user: User = Depends(get_current_user)):
    # Legado, pode ser removido ou adaptado
    return {"message": "Endpoint legado. Use /aluno/boletim/{semestre}?matricula=..."}

@app.get("/previsoes/{matricula}")
async def listar_previsoes_legado(matricula: str, current_user: User = Depends(get_current_user)):
    # Legado
    return {"message": "Endpoint legado. Use /aluno/boletim/{semestre}?matricula=..."}

# ---- Inicialização da base de dados ----
@app.on_event("startup")
async def startup():
    await init_db()