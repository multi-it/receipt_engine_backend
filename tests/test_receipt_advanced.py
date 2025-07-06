import pytest
from decimal import Decimal
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import create_access_token

@pytest.fixture
async def test_user_with_multiple_receipts(test_session: AsyncSession):
    user = UserModel(
        fullname="Test User",
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    test_session.add(user)
    await test_session.flush()
    
    receipts_data = [
        {
            "payment_type": "cash",
            "payment_amount": Decimal("100.00"),
            "total": Decimal("85.50"),
            "rest": Decimal("14.50"),
            "items": [
                {"name": "Milk", "price": Decimal("25.50"), "quantity": Decimal("2"), "total": Decimal("51.00")},
                {"name": "Bread", "price": Decimal("34.50"), "quantity": Decimal("1"), "total": Decimal("34.50")}
            ]
        },
        {
            "payment_type": "cashless",
            "payment_amount": Decimal("50.00"),
            "total": Decimal("45.00"),
            "rest": Decimal("5.00"),
            "items": [
                {"name": "Coffee", "price": Decimal("45.00"), "quantity": Decimal("1"), "total": Decimal("45.00")}
            ]
        },
        {
            "payment_type": "cash",
            "payment_amount": Decimal("200.00"),
            "total": Decimal("175.00"),
            "rest": Decimal("25.00"),
            "items": [
                {"name": "Cheese", "price": Decimal("150.00"), "quantity": Decimal("1"), "total": Decimal("150.00")},
                {"name": "Butter", "price": Decimal("25.00"), "quantity": Decimal("1"), "total": Decimal("25.00")}
            ]
        }
    ]
    
    created_receipts = []
    for receipt_data in receipts_data:
        receipt = ReceiptModel(
            user_id=user.id,
            payment_type=receipt_data["payment_type"],
            payment_amount=receipt_data["payment_amount"],
            total=receipt_data["total"],
            rest=receipt_data["rest"]
        )
        test_session.add(receipt)
        await test_session.flush()
        
        for item_data in receipt_data["items"]:
            item = ReceiptItemModel(
                receipt_id=receipt.id,
                name=item_data["name"],
                price=item_data["price"],
                quantity=item_data["quantity"],
                total=item_data["total"]
            )
            test_session.add(item)
        
        created_receipts.append(receipt)
    
    await test_session.commit()
    await test_session.refresh(user)
    
    return user, created_receipts

class TestReceiptAdvanced:
    async def test_get_receipts_with_filters(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?payment_type=cash", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["payment"]["type"] == "cash" for item in data["items"])
        
        response = await test_client.get("/receipts?min_total=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert float(data["items"][0]["total"]) >= 100
        
        response = await test_client.get("/receipts?min_total=40&max_total=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert 40 <= float(item["total"]) <= 100
    
    async def test_search_receipts_by_product_name(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?search=Milk", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert any("Milk" in product["name"] for product in data["items"][0]["products"])
        
        response = await test_client.get("/receipts?search=Coff", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert any("Coffee" in product["name"] for product in data["items"][0]["products"])
    
    async def test_sort_receipts(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?sort_by=total&sort_order=asc", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        
        totals = [float(item["total"]) for item in data["items"]]
        assert totals == sorted(totals)
        
        response = await test_client.get("/receipts?sort_by=total&sort_order=desc", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        
        totals = [float(item["total"]) for item in data["items"]]
        assert totals == sorted(totals, reverse=True)
    
    async def test_get_receipt_stats(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_receipts"] == 3
        assert float(data["total_amount"]) == 305.50
        assert abs(float(data["average_amount"]) - 101.83) < 0.01
        assert float(data["max_amount"]) == 175.00
        assert float(data["min_amount"]) == 45.00
        
        payment_stats = data["payment_type_stats"]
        assert len(payment_stats) == 2
        
        cash_stats = next(stat for stat in payment_stats if stat["type"] == "cash")
        assert cash_stats["count"] == 2
        assert float(cash_stats["total"]) == 260.50
        
        cashless_stats = next(stat for stat in payment_stats if stat["type"] == "cashless")
        assert cashless_stats["count"] == 1
        assert float(cashless_stats["total"]) == 45.00
    
    async def test_complex_filters_combination(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?payment_type=cash&min_total=80", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        
        for item in data["items"]:
            assert item["payment"]["type"] == "cash"
            assert float(item["total"]) >= 80
    
    async def test_pagination_with_filters(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?payment_type=cash&page=1&size=1", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["size"] == 1
        assert data["total_pages"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is False
    
    async def test_invalid_filter_parameters(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?sort_by=invalid_field", headers=headers)
        assert response.status_code == 422
        
        response = await test_client.get("/receipts?sort_order=invalid_order", headers=headers)
        assert response.status_code == 422
    
    async def test_empty_search_results(self, test_client: AsyncClient, test_user_with_multiple_receipts):
        user, receipts = test_user_with_multiple_receipts
        token = create_access_token({"user_id": user.id, "username": user.username})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await test_client.get("/receipts?search=NonExistentProduct", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
    
    async def test_unauthorized_access_to_advanced_features(self, test_client: AsyncClient):
        response = await test_client.get("/receipts/stats")
        assert response.status_code == 403
        
        response = await test_client.get("/receipts?search=test")
        assert response.status_code == 403
