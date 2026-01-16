from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference



app = FastAPI(title="Fastapi E-Commerce Backend")


@app.get("/")
async def root():
    return {"message": "Fastapi E-Commerce API"}



# BACKEND TESTING
@app.get("/scalar", include_in_schema=False)
def get_scalar():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="TESTING"
    )
