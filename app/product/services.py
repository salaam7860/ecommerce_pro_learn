from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select


from app.product.models import Product, Category
from app.product.schemas import CategoryCreate, CategoryOut


##############################################
################ CATEGORY ####################
##############################################

# create Category
async def create_category(session: AsyncSession, category: CategoryCreate)->CategoryOut:
    category = Category(name=category.name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category

# Get all Category
async def get_all_cat(session: AsyncSession)-> list[CategoryOut]:
    stmt = select(Category)
    cat = await session.execute(stmt)
    return cat.scalars().all()

# Get Single Category
async def get_single_cat(session: AsyncSession, id: int)->CategoryOut:
    stmt = select(Category).where(Category.id == id)
    result = await session.scalars(stmt)
    cat = result.one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid ID.")
    return cat


async def delete_cat(session: AsyncSession, id: int)->bool:
    stmt = await session.get(Category, id)
    if not stmt:
        return False
    await session.delete(stmt)
    await session.commit()
    return True
    

    