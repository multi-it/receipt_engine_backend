import pytest
from decimal import Decimal
from pydantic import ValidationError
from app.domain.schemas.receipt import (
    ReceiptItemCreate, ReceiptItemResponse, PaymentCreate, PaymentResponse,
    ReceiptCreate, ReceiptResponse, PaymentType
)

class TestReceiptItemCreate:
    def test_create_receipt_item_valid(self):
        item = ReceiptItemCreate(
            name="Test Product",
            price=Decimal("10.50"),
            quantity=Decimal("2.0")
        )
        assert item.name == "Test Product"
        assert item.price == Decimal("10.50")
        assert item.quantity == Decimal("2.0")
    
    def test_create_receipt_item_empty_name(self):
        with pytest.raises(ValidationError):
            ReceiptItemCreate(
                name="",
                price=Decimal("10.50"),
                quantity=Decimal("2.0")
            )
    
    def test_create_receipt_item_zero_price(self):
        with pytest.raises(ValidationError):
            ReceiptItemCreate(
                name="Test Product",
                price=Decimal("0"),
                quantity=Decimal("2.0")
            )
    
    def test_create_receipt_item_negative_price(self):
        with pytest.raises(ValidationError):
            ReceiptItemCreate(
                name="Test Product",
                price=Decimal("-10.50"),
                quantity=Decimal("2.0")
            )
    
    def test_create_receipt_item_zero_quantity(self):
        with pytest.raises(ValidationError):
            ReceiptItemCreate(
                name="Test Product",
                price=Decimal("10.50"),
                quantity=Decimal("0")
            )

class TestPaymentCreate:
    def test_create_payment_cash(self):
        payment = PaymentCreate(
            type=PaymentType.CASH,
            amount=Decimal("100.00")
        )
        assert payment.type == PaymentType.CASH
        assert payment.amount == Decimal("100.00")
    
    def test_create_payment_cashless(self):
        payment = PaymentCreate(
            type=PaymentType.CASHLESS,
            amount=Decimal("100.00")
        )
        assert payment.type == PaymentType.CASHLESS
    
    def test_create_payment_zero_amount(self):
        with pytest.raises(ValidationError):
            PaymentCreate(
                type=PaymentType.CASH,
                amount=Decimal("0")
            )
    
    def test_create_payment_negative_amount(self):
        with pytest.raises(ValidationError):
            PaymentCreate(
                type=PaymentType.CASH,
                amount=Decimal("-10.00")
            )

class TestReceiptCreate:
    def test_create_receipt_valid(self):
        receipt = ReceiptCreate(
            products=[
                ReceiptItemCreate(name="Product 1", price=Decimal("10.00"), quantity=Decimal("2"))
            ],
            payment=PaymentCreate(type=PaymentType.CASH, amount=Decimal("50.00"))
        )
        assert len(receipt.products) == 1
        assert receipt.payment.amount == Decimal("50.00")
    
    def test_create_receipt_empty_products(self):
        with pytest.raises(ValidationError):
            ReceiptCreate(
                products=[],
                payment=PaymentCreate(type=PaymentType.CASH, amount=Decimal("50.00"))
            )
    
    def test_create_receipt_multiple_products(self):
        receipt = ReceiptCreate(
            products=[
                ReceiptItemCreate(name="Product 1", price=Decimal("10.00"), quantity=Decimal("2")),
                ReceiptItemCreate(name="Product 2", price=Decimal("15.50"), quantity=Decimal("1"))
            ],
            payment=PaymentCreate(type=PaymentType.CASHLESS, amount=Decimal("50.00"))
        )
        assert len(receipt.products) == 2
        assert receipt.payment.type == PaymentType.CASHLESS
