from typing import List

from pydantic import BaseModel


class BaseResponse(BaseModel):

    id: str | None = None
    message: str
    status: int


class Category(BaseModel):

    category_id: str | None = None
    category_name: str
    date_created: int | None = None
    subcategory: list | None


class CategoryResponse(BaseModel):

    result: List[Category]
    page: int
    limit: int
    total: int


class Inventory(BaseModel):

    date_created: int | None = None
    file_name: str | None
    file_path: str | None
    inventory_id: str | None = None
    product_id: str | None
    status: str | None
    trackId: str | None = None


class InventoryResponse(BaseModel):

    result: List[Inventory]
    page: int
    limit: int
    total: int


class Product(BaseModel):

    category_id: str | None
    category_name: str | None
    date_created: int | None = None
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


class Promotion(BaseModel):

    address: str | None = ''
    balance: float | None = 0
    code: str | None = None
    date_created: int | None = None
    payout_amount: int | None = 0
    payout_id: str | None = None
    promotion_id: str | None = None
    total_payout: float | None = 0
    user_id: int | None


class PromotionResponse(BaseModel):

    result: List[Promotion]
    page: int
    limit: int
    total: int


class PromotionSettings(BaseModel):

    key: str | None = None
    value: str | int | None = None


class PromotionSettingsResponse(BaseModel):

    result: List[PromotionSettings]
    page: int
    limit: int
    total: int


class RedeemableCategory(BaseModel):

    category_id: str | None = None
    category_name: str
    date_created: int | None = None


class RedeemableCategoryResponse(BaseModel):

    result: List[RedeemableCategory]
    page: int
    limit: int
    total: int


class RedeemableInventory(BaseModel):

    date_created: int | None = None
    file_name: str | None
    file_path: str | None
    inventory_id: str | None = None
    product_id: str | None
    status: str | None
    transaction_id: str | None = None


class RedeemableInventoryResponse(BaseModel):

    result: List[RedeemableInventory]
    page: int
    limit: int
    total: int


class RedeemableProduct(BaseModel):

    category_id: str | None
    category_name: str | None
    date_created: int | None = None
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
    date_created: int | None = None
    subcategory_id: str | None = None
    subcategory_name: str


class SubcategoryResponse(BaseModel):

    result: List[Subcategory]
    page: int
    limit: int
    total: int


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

    date_created: int | None = None
    first_name: str | None
    points: float | None = 0
    user_id: str | None = None
    user_name: str | None
