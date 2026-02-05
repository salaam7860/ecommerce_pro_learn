from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, status, File, Form, HTTPException, Query

from app.account.dependency import require_admin
from app.account.models import User
from app.db.config import SessionDep
from app.product.schemas import PaginatedProductOut, ProductCreate, ProductOut
from app.product.services import create_product, get_all_products, get_item_by_slug, search_product








router = APIRouter(prefix="/api/products", tags=["Products"])


@router.post("/create-product", response_model=ProductOut)
async def product_create(session: SessionDep,
    title: str  = Form(...), 
    description: str | None= Form(Form),
    price: float= Form(...),
    stock_quantity: int = Form(...),
    category_ids: Annotated[list[int], Form()] = [],
    image:UploadFile |None = File(None),
    admin_user: User = Depends(require_admin)):
    
    data = ProductCreate(
        title=title,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_ids=category_ids,
    )
    return await create_product(session, data, image)


@router.get("", response_model=PaginatedProductOut)
async def product_get_all(session: SessionDep, category_name: list[str]|None=Query(default=None), limit: int = Query(default=5, ge=1,le=100), page: int =Query(default=1, ge=1)):
    return await get_all_products(session, category_name,limit, page)

@router.get("/search", response_model=PaginatedProductOut)
async def product_search(
                         session: SessionDep, 
                         category_name: list[str]|None=Query(default=None),
                         title: str |None=Query(default=None),
                         description: str|None=Query(default=None),
                         min_price: float|None=Query(default=None),
                         max_price: float|None=Query(default=None),
                         limit: int = 5,
                         page: int = 1
):
    return await search_product(session=session, 
                                category_name=category_name,
                                title=title,
                                description=description, 
                                min_price=min_price, 
                                max_price=max_price, 
                                limit=limit, 
                                page=page)


@router.get("/{slug}", response_model=ProductOut)
async def product_by_slug(session:SessionDep, slug: str):
    return await get_item_by_slug(session, slug)

