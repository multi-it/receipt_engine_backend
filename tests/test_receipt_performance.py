import pytest
import time
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import create_access_token

@pytest.fixture
async def test_user_with_many_receipts(test_session: AsyncSession):
    user = UserModel(
        fullname="Performance Test User",
        username="perfuser",
        email="perf@example.com",
        password_hash="hashed_password"
    )
    test_session.add(user)
    await test_session.flush()
    
    for i in range(50):
        receipt = ReceiptModel(
            user_id=user.id,
            payment_type="cash" if i % 2 == 0 else "cashless",
            payment_amount=Decimal(f"{100 + i}.00"),
            total=Decimal(f"{90 + i}.00"),
            rest=Decimal("10.00")
        )
        test_session.add(receipt)
        await test_session.flush()
        
        for j in range(3):
            item = ReceiptItemModel(
                receipt_id=receipt.id,
                name=f"Product {i}-{j}",
                price=Decimal(f"{30 + j}.00"),
                quantity=Decimal("1.0"),
                total=Decimal(f"{30 + j}.00")
            )
            test_session.add(item)
    
    await test_session.commit()
    await test_session.refresh(user)
    
    return user

class TestReceiptPerformance:
    async def test_large_list_performance(self, test_client: AsyncClient, test_user_with_many_receipts):
        user = test_user_with_many_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        response = await test_client.get("/receipts?size=50", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 50
        
        execution_time = end_time - start_time
        assert execution_time < 2.0
    
    async def test_complex_search_performance(self, test_client: AsyncClient, test_user_with_many_receipts):
        user = test_user_with_many_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        response = await test_client.get(
            "/receipts?search=Product&payment_type=cash&min_total=90&sort_by=total",
            headers=headers
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        execution_time = end_time - start_time
        assert execution_time < 3.0
    
    async def test_stats_performance(self, test_client: AsyncClient, test_user_with_many_receipts):
        user = test_user_with_many_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        response = await test_client.get("/receipts/stats", headers=headers)
        end_time = time.time()
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_receipts"] == 50
        
        execution_time = end_time - start_time
        assert execution_time < 1.0
