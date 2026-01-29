from fastapi import APIRouter, status

from app.product.schemas import CategoryCreate, CategoryOut
from app.db.config import SessionDep
from app.product.services import create_category, delete_cat, get_all_cat, get_single_cat




router = APIRouter(prefix="/api/product/category", tags=["Categories"])



@router.post("/create-category", response_model=CategoryOut)
async def category_create(session: SessionDep, category: CategoryCreate):
    return await create_category(session, category)

@router.get("/all-categories", response_model=list[CategoryOut])
async def all_categories(session: SessionDep):
    return await get_all_cat(session)

@router.get("/single-cat/{id}", response_model=CategoryOut)
async def single_category(session: SessionDep, id: int):
    return await get_single_cat(session, id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def cat_delete(session: SessionDep, id: int):
    return await delete_cat(session, id)