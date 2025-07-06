import pytest
import time
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password, create_access_token

@pytest.fixture
async def test_user_with_many_receipts(test_session: AsyncSession):
    user = UserModel(
        fullname="Performance Test User",
        username="perfuser",
        email="perf@example.com",
        password_hash=hash_password("perfpassword123")
    )
    test_session.add(user)
    await test_session.flush()
    
    for i in range(50):
        receipt = ReceiptModel(
            user_id=user.id,
            payment_type="cash" if i % 2 == 0 else "cashless",
            payment_amount=Decimal("100.00"),
            total=Decimal("85.50"),
            rest=Decimal("14.50")
        )
        test_session.add(receipt)
        await test_session.flush()
        
        item = ReceiptItemModel(
            receipt_id=receipt.id,
            name=f"Performance Product {i}",
            price=Decimal("42.75"),
            quantity=Decimal("2"),
            total=Decimal("85.50")
        )
        test_session.add(item)
    
    await test_session.commit()
    await test_session.refresh(user)
    return user

class TestReceiptPerformance:
    async def test_large_list_performance(self, test_client: AsyncClient, test_user_with_many_receipts):
        user = test_user_with_many_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        response = await test_client.get("/receipts?size=50", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0

    async def test_complex_search_performance(self, test_client: AsyncClient, test_user_with_many_receipts):
        user = test_user_with_many_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        response = await test_client.get("/receipts?search=Performance&payment_type=cash&sort_by=total", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 2.0

    async def test_stats_performance(self, test_client: AsyncClient, test_user_with_many_receipts):
        user = test_user_with_many_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        response = await test_client.get("/receipts/stats", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 1.0
