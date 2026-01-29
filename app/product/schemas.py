from pydantic import BaseModel, Field


########### CATEGORY ###############

class CategoryBase(BaseModel):
    name: str= Field(description="Name of the category", min_length=3)

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: int
    name: str

    model_config = {"from_attributes": True}