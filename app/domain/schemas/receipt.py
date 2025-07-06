from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum

class PaymentType(str, Enum):
    CASH = "cash"
    CASHLESS = "cashless"

class ReceiptItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0, decimal_places=2)
    quantity: Decimal = Field(gt=0, decimal_places=3)

class ReceiptItemResponse(BaseModel):
    name: str
    price: Decimal
    quantity: Decimal
    total: Decimal

class PaymentCreate(BaseModel):
    type: PaymentType
    amount: Decimal = Field(gt=0, decimal_places=2)

class PaymentResponse(BaseModel):
    type: PaymentType
    amount: Decimal

class ReceiptCreate(BaseModel):
    products: List[ReceiptItemCreate] = Field(min_length=1)
    payment: PaymentCreate

class ReceiptResponse(BaseModel):
    id: int
    products: List[ReceiptItemResponse]
    payment: PaymentResponse
    total: Decimal
    rest: Decimal
    created_at: datetime

class ReceiptListResponse(BaseModel):
    items: List[ReceiptResponse]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ReceiptStatsResponse(BaseModel):
    total_receipts: int
    total_amount: Decimal
    average_amount: Decimal
    max_amount: Decimal
    min_amount: Decimal
    payment_type_stats: List[Dict[str, Any]]
