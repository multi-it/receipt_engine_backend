from datetime import datetime, timezone
from typing import List, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

class PaymentType(Enum):
    CASH = "cash"
    CASHLESS = "cashless"

@dataclass
class ReceiptItem:
    name: str
    price: Decimal
    quantity: Decimal
    total: Optional[Decimal] = None
    
    def __post_init__(self):
        if self.total is None:
            self.total = (self.price * self.quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Product name cannot be empty")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

@dataclass
class Payment:
    type: PaymentType
    amount: Decimal
    
    def validate(self) -> None:
        if self.amount <= 0:
            raise ValueError("Payment amount must be positive")

@dataclass
class Receipt:
    id: Optional[int] = None
    user_id: Optional[int] = None
    items: List[ReceiptItem] = None
    payment: Optional[Payment] = None
    total: Optional[Decimal] = None
    rest: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
    
    def calculate_totals(self) -> None:
        if not self.items:
            raise ValueError("Receipt cannot be empty")
        
        self.total = sum(item.total for item in self.items).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        if self.payment:
            if self.payment.amount < self.total:
                raise ValueError("Payment amount is insufficient")
            self.rest = (self.payment.amount - self.total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def validate(self) -> None:
        if not self.items:
            raise ValueError("Receipt must contain at least one item")
        
        for item in self.items:
            item.validate()
        
        if self.payment:
            self.payment.validate()
        
        self.calculate_totals()
