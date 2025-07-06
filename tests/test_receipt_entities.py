import pytest
from decimal import Decimal
from datetime import datetime
from app.domain.entities.receipt import Receipt, ReceiptItem, Payment, PaymentType

class TestReceiptItem:
    def test_create_receipt_item_with_total_calculation(self):
        item = ReceiptItem(
            name="Test Product",
            price=Decimal("10.50"),
            quantity=Decimal("2.0")
        )
        assert item.total == Decimal("21.00")
    
    def test_validate_receipt_item_success(self):
        item = ReceiptItem(
            name="Valid Product",
            price=Decimal("10.50"),
            quantity=Decimal("2.0")
        )
        item.validate()
    
    def test_validate_receipt_item_empty_name(self):
        item = ReceiptItem(
            name="",
            price=Decimal("10.50"),
            quantity=Decimal("2.0")
        )
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            item.validate()

class TestReceipt:
    def test_create_receipt_with_items(self):
        items = [
            ReceiptItem(name="Product 1", price=Decimal("10.00"), quantity=Decimal("2")),
            ReceiptItem(name="Product 2", price=Decimal("15.50"), quantity=Decimal("1"))
        ]
        payment = Payment(type=PaymentType.CASH, amount=Decimal("50.00"))
        receipt = Receipt(items=items, payment=payment)
        
        assert len(receipt.items) == 2
        assert receipt.payment.amount == Decimal("50.00")
    
    def test_validate_receipt_success(self):
        items = [
            ReceiptItem(name="Product 1", price=Decimal("10.00"), quantity=Decimal("2")),
        ]
        payment = Payment(type=PaymentType.CASH, amount=Decimal("50.00"))
        receipt = Receipt(items=items, payment=payment)
        
        receipt.validate()
        
        assert receipt.total == Decimal("20.00")
        assert receipt.rest == Decimal("30.00")
