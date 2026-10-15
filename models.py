from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    
    enderecos: Mapped[list["Endereco"]] = relationship(
        back_populates="cliente",
        cascade="all, delete-orphan",
        order_by="Endereco.id",
    )

    def __repr__(self) -> str:
        return f"Cliente(id={self.id}, nome={self.nome!r})"


class Endereco(Base):
    __tablename__ = "enderecos"

    id: Mapped[int] = mapped_column(primary_key=True)
    rua: Mapped[str] = mapped_column(String(150))
    numero: Mapped[str] = mapped_column(String(10))
    cidade: Mapped[str] = mapped_column(String(80))
    estado: Mapped[str] = mapped_column(String(2))
    cep: Mapped[str] = mapped_column(String(9))
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))

    cliente: Mapped["Cliente"] = relationship(back_populates="enderecos")

    def __repr__(self) -> str:
        return f"Endereco(id={self.id}, {self.rua}, {self.numero})"
