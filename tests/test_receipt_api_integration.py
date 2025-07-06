import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password, create_access_token

@pytest.fixture
async def test_user_with_receipts(test_session: AsyncSession):
    user = UserModel(
        fullname="Test User",
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword123")
    )
    test_session.add(user)
    await test_session.flush()
    
    receipt = ReceiptModel(
        user_id=user.id,
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
    await test_session.refresh(user)
    await test_session.refresh(receipt)
    return user, receipt

class TestReceiptAPI:
    async def test_create_receipt_success(self, test_client: AsyncClient, test_user: UserModel):
        token = create_access_token({"user_id": test_user.id, "username": test_user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        receipt_data = {
            "products": [
                {
                    "name": "Test Product",
                    "price": 10.50,
                    "quantity": 2.0
                }
            ],
            "payment": {
                "type": "cash",
                "amount": 50.00
            }
        }
        
        response = await test_client.post("/receipts/", json=receipt_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert float(data["total"]) == 21.00
        assert float(data["payment"]["amount"]) == 50.00
        assert float(data["rest"]) == 29.00
        assert len(data["products"]) == 1
    
    async def test_create_receipt_insufficient_payment(self, test_client: AsyncClient, test_user: UserModel):
        token = create_access_token({"user_id": test_user.id, "username": test_user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        receipt_data = {
            "products": [
                {
                    "name": "Expensive Product",
                    "price": 100.00,
                    "quantity": 1.0
                }
            ],
            "payment": {
                "type": "cash",
                "amount": 50.00
            }
        }
        
        response = await test_client.post("/receipts/", json=receipt_data, headers=headers)
        
        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()
    
    async def test_get_receipts_list(self, test_client: AsyncClient, test_user_with_receipts):
        user, receipt = test_user_with_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert "page" in data
        assert "total_pages" in data
    
    async def test_get_receipt_by_id(self, test_client: AsyncClient, test_user_with_receipts):
        user, receipt = test_user_with_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get(f"/receipts/{receipt.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == receipt.id
        assert float(data["total"]) == float(receipt.total)
        assert len(data["products"]) == 2
    
    async def test_unauthorized_access(self, test_client: AsyncClient):
        response = await test_client.get("/receipts/")
        assert response.status_code == 403  # Исправлено: 403 вместо 401
        
        response = await test_client.post("/receipts/", json={})
        assert response.status_code == 403  # Исправлено: 403 вместо 401
