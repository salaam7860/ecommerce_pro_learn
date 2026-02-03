from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference


from app.account.routers import router as account_router
from app.product.routers.category import router as category_router
from app.product.routers.product import router as product_router


app = FastAPI(title="Fastapi E-Commerce Backend")


@app.get("/")
async def root():
    return {"message": "Fastapi E-Commerce API"}

app.include_router(account_router)
app.include_router(category_router)
app.include_router(product_router)


# BACKEND TESTING
@app.get("/scalar", include_in_schema=False)
def get_scalar():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="TESTING"
    )
