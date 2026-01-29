from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, TIMESTAMP, ForeignKey, Table, Column, Text
from datetime import timezone, datetime

from app.db.base import Base




# for many-to-many you have to create association table.
product_category_table = Table(
    "product_category",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False) # some databases doesn't support text with Unique
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(default=0)
    image_url: Mapped[str]= mapped_column(String(255),nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda:datetime.now(timezone.utc))
    update_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=lambda:datetime.now(timezone.utc), onupdate=lambda:datetime.now(timezone.utc))

    categories: Mapped[list["Category"]] = relationship("Category", secondary=product_category_table, back_populates="products")
    



class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50),unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship("Product", secondary=product_category_table, back_populates="categories")

    



