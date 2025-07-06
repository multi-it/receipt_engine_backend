import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password


@pytest.fixture
async def test_user_with_receipt(test_session: AsyncSession):
    """Create test user with receipt."""
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
    await test_session.refresh(receipt)
    return user, receipt


class TestPublicReceiptAPI:
    """Test public receipt API endpoints."""
    
    async def test_public_receipt_endpoint_returns_complete_receipt_data_without_authentication(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt endpoint returns complete receipt data without requiring authentication."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == receipt.id
        assert float(data["total"]) == float(receipt.total)
        assert float(data["rest"]) == float(receipt.rest)
        assert len(data["products"]) == 2
        assert data["payment"]["type"] == "cash"
        assert float(data["payment"]["amount"]) == float(receipt.payment_amount)
    
    async def test_public_receipt_endpoint_returns_404_when_receipt_does_not_exist(
        self, 
        test_client: AsyncClient
    ):
        """Test that public receipt endpoint returns 404 status when requested receipt does not exist."""
        response = await test_client.get("/public/receipts/999999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_public_receipt_text_endpoint_returns_formatted_plain_text_receipt(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt text endpoint returns properly formatted plain text receipt."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        assert "RECEIPT" in content
        assert "Store #1" in content
        assert "Product 1" in content
        assert "Product 2" in content
        assert "TOTAL: $85.50" in content
        assert "Cash: $100.00" in content
        assert "Change: $14.50" in content
        assert "Thank you for your purchase!" in content
    
    async def test_public_receipt_text_endpoint_returns_404_when_receipt_does_not_exist(
        self, 
        test_client: AsyncClient
    ):
        """Test that public receipt text endpoint returns 404 status when requested receipt does not exist."""
        response = await test_client.get("/public/receipts/999999/text")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_public_receipt_text_displays_card_payment_type_for_cashless_transactions(
        self, 
        test_client: AsyncClient, 
        test_session: AsyncSession
    ):
        """Test that receipt text displays 'Card' payment type for cashless payment transactions."""
        user = UserModel(
            fullname="Test User",
            username="testuser2",
            email="test2@example.com",
            password_hash=hash_password("testpassword123")
        )
        test_session.add(user)
        await test_session.flush()
        
        receipt = ReceiptModel(
            user_id=user.id,
            payment_type="cashless",
            payment_amount=Decimal("50.00"),
            total=Decimal("50.00"),
            rest=Decimal("0.00")
        )
        test_session.add(receipt)
        await test_session.flush()
        
        item = ReceiptItemModel(
            receipt_id=receipt.id,
            name="Coffee",
            price=Decimal("50.00"),
            quantity=Decimal("1"),
            total=Decimal("50.00")
        )
        test_session.add(item)
        await test_session.commit()
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        
        assert response.status_code == 200
        content = response.text
        assert "Card: $50.00" in content
        assert "Change: $0.00" in content
        assert "Coffee" in content
    
    async def test_public_receipt_endpoints_work_without_any_authentication_headers(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt endpoints function correctly without any authentication headers."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        assert response.status_code == 200
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        assert response.status_code == 200
    
    async def test_public_receipt_json_contains_all_product_details_with_correct_calculations(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt JSON contains all product details with mathematically correct calculations."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        products = data["products"]
        assert len(products) == 2
        
        product1 = next(p for p in products if p["name"] == "Product 1")
        assert float(product1["price"]) == 10.00
        assert float(product1["quantity"]) == 2.00
        assert float(product1["total"]) == 20.00
        
        product2 = next(p for p in products if p["name"] == "Product 2")
        assert float(product2["price"]) == 32.75
        assert float(product2["quantity"]) == 2.00
        assert float(product2["total"]) == 65.50
