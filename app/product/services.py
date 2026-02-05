from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from sqlalchemy.orm import selectinload


from app.product.models import Product, Category
from app.product.schemas import CategoryCreate, CategoryOut, PaginatedProductOut, ProductCreate, ProductOut
from app.product.utils import generate_slug, save_upload_file


##############################################
################ CATEGORY ####################
##############################################

# create Category
async def create_category(session: AsyncSession, category: CategoryCreate)->CategoryOut:
    stmt = select(Category).where(Category.name == category.name)
    result = await session.scalars(stmt)
    if result.one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This category already exists.")
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
    

##############################################
################ PRODUCT #####################
##############################################

# PRODUCT CREATE
async def create_product(session: AsyncSession, product_data: ProductCreate, image_url: UploadFile | None = None)->ProductOut:
    # CHECK NEGATIVE STOCK QUANTITY
    if product_data.stock_quantity < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock quantity can not be negative")
    image_path = await save_upload_file(image_url, "images")

    categories = [] 
    if product_data.category_ids:
        category_stmt = select(Category).where(Category.id.in_(product_data.category_ids))
        category_result = await session.execute(category_stmt)
        categories = category_result.scalars().all()
    
    product_dict = product_data.model_dump(exclude={"category_ids"})

    if not product_dict.get("slug"):
        product_dict["slug"] = generate_slug(product_dict.get("title"))
    
    new_product = Product(**product_dict, image_url=image_path, categories=categories)

    session.add(new_product)
    await session.commit()
    await session.refresh(new_product, ["categories"])

    return new_product


# PRODUCT GET
async def get_all_products(session: AsyncSession, category_name: list[str] | None = None, limit: int = 5, page: int = 1) -> dict:
    stmt = select(Product).options(selectinload(Product.categories))

    if category_name:
        stmt = stmt.join(Product.categories).where(Category.name.in_(category_name)).distinct()
    
    count_stmt = stmt.with_only_columns(func.count(Product.id)).order_by(None)

    total = await session.scalar(count_stmt)

    stmt = stmt.limit(limit).offset((page-1)*limit)

    result = await session.execute(stmt)

    products = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": products
    }


# SEARCH PRODUCT 
async def search_product(session: AsyncSession, 
                         category_name: list[str]|None=None,
                         title: str |None=None,
                         description: str|None=None,
                         min_price: float|None=None,
                         max_price: float|None=None,
                         limit: int = 5,
                         page: int = 1
                        )-> dict: 
#   FETCH PRODUCT FROM DB
    stmt = select(Product).options(selectinload(Product.categories))                   

    if category_name:
        stmt = stmt.join(Product.categories).where(Category.name.in_(category_name)).distinct()

    filter = []

    if title: 
        filter.append(Product.title.like(f"%{title}%"))
    if description and description.strip():
        filter.append(Product.description.like(f"%{description.strip()}%")) # Product.description.ilike("%iphone%")


    
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise HTTPException(
                status_code=400,
                detail="min_price cannot be greater than max_price"
        )
    
    if min_price is not None:
        filter.append(Product.price >= min_price)
    if max_price is not None:
        filter.append(Product.price <= max_price)

    if filter:
        stmt = stmt.where(and_(*filter))

    count_stmt = stmt.with_only_columns(func.count(Product.id)).order_by(None)

    total = await session.scalar(count_stmt)

    stmt = stmt.limit(limit).offset((page-1)*limit)

    result = await session.execute(stmt)

    products = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": products
    }

# FETCH SINGLE PRODUCT USING SLUG 
async def get_item_by_slug(session: AsyncSession, slug: str)-> ProductOut|None:
    stmt = select(Product).options(selectinload(Product.categories)).where(Product.slug == slug) # us kay against categories bhi utha lo 
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return ProductOut.model_validate(product)

    

# PROUCT UPDATE
# PRODUCT PATCH
# PRODUCT DELETE







