import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password

@pytest.fixture
async def test_user_for_receipts(test_session: AsyncSession):
    user = UserModel(
        fullname="Test User",
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword123")
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user

class TestReceiptModel:
    async def test_create_receipt_model(self, test_session: AsyncSession, test_user_for_receipts: UserModel):
        receipt = ReceiptModel(
            user_id=test_user_for_receipts.id,
            payment_type="cash",
            payment_amount=Decimal("100.00"),
            total=Decimal("85.50"),
            rest=Decimal("14.50")
        )
        
        test_session.add(receipt)
        await test_session.commit()
        await test_session.refresh(receipt)
        
        assert receipt.id is not None
        assert receipt.user_id == test_user_for_receipts.id
        assert receipt.payment_type == "cash"
        assert receipt.payment_amount == Decimal("100.00")
        assert receipt.total == Decimal("85.50")
        assert receipt.rest == Decimal("14.50")
        assert receipt.created_at is not None
    
    async def test_receipt_user_relationship(self, test_session: AsyncSession, test_user_for_receipts: UserModel):
        receipt = ReceiptModel(
            user_id=test_user_for_receipts.id,
            payment_type="cashless",
            payment_amount=Decimal("50.00"),
            total=Decimal("45.00"),
            rest=Decimal("5.00")
        )
        
        test_session.add(receipt)
        await test_session.commit()
        
        stmt = select(ReceiptModel).where(ReceiptModel.user_id == test_user_for_receipts.id)
        result = await test_session.execute(stmt)
        saved_receipt = result.scalar()
        
        assert saved_receipt is not None
        assert saved_receipt.user_id == test_user_for_receipts.id

class TestReceiptItemModel:
    async def test_create_receipt_item_model(self, test_session: AsyncSession, test_user_for_receipts: UserModel):
        receipt = ReceiptModel(
            user_id=test_user_for_receipts.id,
            payment_type="cash",
            payment_amount=Decimal("100.00"),
            total=Decimal("85.50"),
            rest=Decimal("14.50")
        )
        test_session.add(receipt)
        await test_session.flush()
        
        receipt_item = ReceiptItemModel(
            receipt_id=receipt.id,
            name="Test Product",
            price=Decimal("10.50"),
            quantity=Decimal("2.0"),
            total=Decimal("21.00")
        )
        
        test_session.add(receipt_item)
        await test_session.commit()
        await test_session.refresh(receipt_item)
        
        assert receipt_item.id is not None
        assert receipt_item.receipt_id == receipt.id
        assert receipt_item.name == "Test Product"
        assert receipt_item.price == Decimal("10.50")
        assert receipt_item.quantity == Decimal("2.0")
        assert receipt_item.total == Decimal("21.00")
    
    async def test_receipt_items_relationship(self, test_session: AsyncSession, test_user_for_receipts: UserModel):
        receipt = ReceiptModel(
            user_id=test_user_for_receipts.id,
            payment_type="cash",
            payment_amount=Decimal("100.00"),
            total=Decimal("85.50"),
            rest=Decimal("14.50")
        )
        test_session.add(receipt)
        await test_session.flush()
        
        items = [
            ReceiptItemModel(
                receipt_id=receipt.id,
                name="Product 1",
                price=Decimal("10.00"),
                quantity=Decimal("2"),
                total=Decimal("20.00")
            ),
            ReceiptItemModel(
                receipt_id=receipt.id,
                name="Product 2",
                price=Decimal("32.75"),
                quantity=Decimal("2"),
                total=Decimal("65.50")
            )
        ]
        
        for item in items:
            test_session.add(item)
        
        await test_session.commit()
        
        stmt = select(ReceiptItemModel).where(ReceiptItemModel.receipt_id == receipt.id)
        result = await test_session.execute(stmt)
        saved_items = result.scalars().all()
        
        assert len(saved_items) == 2
        assert saved_items[0].receipt_id == receipt.id
        assert saved_items[1].receipt_id == receipt.id
    
    async def test_cascade_delete_receipt_items(self, test_session: AsyncSession, test_user_for_receipts: UserModel):
        receipt = ReceiptModel(
            user_id=test_user_for_receipts.id,
            payment_type="cash",
            payment_amount=Decimal("100.00"),
            total=Decimal("85.50"),
            rest=Decimal("14.50")
        )
        test_session.add(receipt)
        await test_session.flush()
        
        receipt_item = ReceiptItemModel(
            receipt_id=receipt.id,
            name="Test Product",
            price=Decimal("10.50"),
            quantity=Decimal("2.0"),
            total=Decimal("21.00")
        )
        test_session.add(receipt_item)
        await test_session.commit()
        
        await test_session.delete(receipt)
        await test_session.commit()
        
        stmt = select(ReceiptItemModel).where(ReceiptItemModel.receipt_id == receipt.id)
        result = await test_session.execute(stmt)
        items = result.scalars().all()
        
        assert len(items) == 0
