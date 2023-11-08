from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


class BaseResponse(BaseModel):

    message: str
    status: int


class Category(BaseModel):

    category_id: str | None = None
    category_name: str
    subcategory: list | None


class CategoryResponse(BaseModel):

    result: List[Category]
    page: int
    limit: int
    total: int


class Inventory(BaseModel):

    file_name: str | None
    file_path: str | None
    inventory_id: str | None = None
    product_id: str | None
    status: str | None


class Product(BaseModel):

    category_id: str | None
    category_name: str | None
    description: str | None
    inventory: int | None = 0
    points: float | None = 0
    price: float | None = 0
    product_id: str | None = None
    product_name: str | None
    subcategory_id: str | None
    subcategory_name: str | None


class ProductResponse(BaseModel):

    result: List[Product]
    page: int
    limit: int
    total: int


class RedeemableCategory(BaseModel):

    category_id: str | None = None
    category_name: str


class RedeemableCategoryResponse(BaseModel):

    result: List[RedeemableCategory]
    page: int
    limit: int
    total: int


class RedeemableInventory(BaseModel):

    file_name: str | None
    file_path: str | None
    inventory_id: str | None = None
    product_id: str | None
    status: str | None


class RedeemableProduct(BaseModel):

    category_id: str | None
    category_name: str | None
    description: str | None
    inventory: int | None = 0
    points: float | None = 0
    product_id: str | None = None
    product_name: str | None


class RedeemableProductResponse(BaseModel):

    result: List[RedeemableProduct]
    page: int
    limit: int
    total: int


class Subcategory(BaseModel):

    category_id: str | None = None
    subcategory_id: str | None = None
    subcategory_name: str


class User(BaseModel):

    first_name: str | None
    points: float | None = 0
    user_id: str | None = None
    user_name: str | None


class CategoryEnum(Enum):
    product = 'product'
    sub_category = 'subcategory'
    point = 'point'


class ItemIn(BaseModel):
    item_id: str | None = None
    item_name: str
    item_description: str
    points: float
    redeem_points: float
    inventory: int
    price: float
    category: CategoryEnum
    created_date: str | datetime | None = None
    has_children: bool = False


class PaginatedItemListResponse(BaseModel):
    result: List[ItemIn]
    page: int
    limit: int
    total: int


class Relationship(BaseModel):
    parent_id: str
    child_id: str


class ResModel(BaseModel):
    item_id: str
    purchased: bool
    location: str
