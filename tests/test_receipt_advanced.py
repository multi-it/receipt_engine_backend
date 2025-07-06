import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password, create_access_token

@pytest.fixture
async def test_user_with_multiple_receipts(test_session: AsyncSession):
    user = UserModel(
        fullname="Test User",
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword123")
    )
    test_session.add(user)
    await test_session.flush()
    
    receipts = []
    for i in range(3):
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
            name=f"Product {i+1}",
            price=Decimal("42.75"),
            quantity=Decimal("2"),
            total=Decimal("85.50")
        )
        test_session.add(item)
        receipts.append(receipt)
    
    await test_session.commit()
    await test_session.refresh(user)
    return user, receipts

class TestReceiptAdvanced:
    async def test_get_receipts_with_filters(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?payment_type=cash", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        cash_receipts = [r for r in data["items"] if r["payment"]["type"] == "cash"]
        assert len(cash_receipts) >= 1

    async def test_search_receipts_by_product_name(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?search=Product", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 1

    async def test_sort_receipts(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?sort_by=created_at&sort_order=desc", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) >= 1

    async def test_get_receipt_stats(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts/stats", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_receipts" in data
        assert data["total_receipts"] >= 3

    async def test_complex_filters_combination(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?payment_type=cash&sort_by=total&sort_order=asc", headers=headers)
        assert response.status_code == 200

    async def test_pagination_with_filters(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?page=1&size=2", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2

    async def test_invalid_filter_parameters(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?sort_by=invalid_field", headers=headers)
        assert response.status_code in [200, 422]

    async def test_empty_search_results(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token(user_id=user.id, username=user.username)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?search=NonexistentProduct", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_unauthorized_access_to_advanced_features(self, test_client: AsyncClient):
        response = await test_client.get("/receipts?payment_type=cash")
        assert response.status_code == 403
        
        response = await test_client.get("/receipts/stats")
        assert response.status_code == 403
