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
    trackId: str | None = None


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
    transaction_id: str | None = None


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


class Transaction(BaseModel):

    amount: float | None = 0
    chat_id: int | None
    points: float | None = 0
    product_id: str | None
    quantity: float | None = 0
    status: str | None
    trackId: str | None
    txID: str | None
    user_id: str | None = None


class User(BaseModel):

    first_name: str | None
    points: float | None = 0
    user_id: str | None = None
    user_name: str | None
