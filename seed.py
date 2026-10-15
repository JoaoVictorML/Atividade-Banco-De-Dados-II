from database import SessionLocal, init_db
from models import Base, Cliente, Endereco
from database import engine

Base.metadata.drop_all(engine)
init_db()

ana = Cliente(nome="Ana Souza", email="ana@email.com", telefone="(85) 99999-1111")
bruno = Cliente(nome="Bruno Lima", email="bruno@email.com", telefone="(88) 98888-2222")
carla = Cliente(nome="Carla Dias", email="carla@email.com")
diego = Cliente(nome="Diego Alves", email="diego@email.com", telefone="(11) 97777-3333")

ana.enderecos = [
    Endereco(rua="Rua das Flores", numero="100", cidade="Fortaleza", estado="CE", cep="60000-000"),
    Endereco(rua="Av. Beira Mar", numero="2500", cidade="Fortaleza", estado="CE", cep="60165-121"),
]
bruno.enderecos = [
    Endereco(rua="Rua do Sol", numero="45", cidade="Sobral", estado="CE", cep="62000-000"),
]
diego.enderecos = [
    Endereco(rua="Av. Paulista", numero="1000", cidade="São Paulo", estado="SP", cep="01310-100"),
]

SessionLocal.add_all([ana, bruno, carla, diego])
SessionLocal.commit()
print("Banco populado com 4 clientes e 4 endereços.")
