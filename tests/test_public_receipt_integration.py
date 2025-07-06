import pytest
from decimal import Decimal
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password
from app.services.receipt_formatter import ReceiptFormatter
from app.domain.schemas.receipt import ReceiptResponse, ReceiptItemResponse, PaymentResponse


@pytest.fixture
async def test_user_with_receipt(test_session: AsyncSession):
    """Create test user with receipt for public API integration tests."""
    user = UserModel(
        fullname="Public API Test User",
        username="publicapiuser",
        email="publicapi@example.com",
        password_hash=hash_password("publicapipassword")
    )
    test_session.add(user)
    await test_session.flush()
    
    receipt = ReceiptModel(
        user_id=user.id,
        payment_type="cash",
        payment_amount=Decimal("100.00"),
        total=Decimal("87.50"),
        rest=Decimal("12.50")
    )
    test_session.add(receipt)
    await test_session.flush()
    
    items = [
        ReceiptItemModel(
            receipt_id=receipt.id,
            name="Integration Test Product A",
            price=Decimal("12.50"),
            quantity=Decimal("3"),
            total=Decimal("37.50")
        ),
        ReceiptItemModel(
            receipt_id=receipt.id,
            name="Integration Test Product B",
            price=Decimal("25.00"),
            quantity=Decimal("2"),
            total=Decimal("50.00")
        )
    ]
    
    for item in items:
        test_session.add(item)
    
    await test_session.commit()
    await test_session.refresh(receipt)
    return user, receipt


class TestPublicReceiptIntegration:
    """Integration tests for public receipt view functionality."""
    
    async def test_public_receipt_json_endpoint_is_accessible_and_returns_valid_data(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt JSON endpoint is accessible and returns structurally valid data."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "products" in data
        assert "payment" in data
        assert "total" in data
        assert "rest" in data
        assert "created_at" in data
    
    async def test_public_receipt_text_endpoint_returns_properly_formatted_plain_text(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt text endpoint returns properly formatted plain text content."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        assert isinstance(content, str)
        assert len(content) > 0
    
    async def test_public_endpoints_function_without_any_authentication_requirements(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public endpoints function correctly without any authentication requirements."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        assert response.status_code == 200
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        assert response.status_code == 200
    
    async def test_public_receipt_json_contains_mathematically_accurate_receipt_data(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that public receipt JSON contains mathematically accurate and complete receipt data."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == receipt.id
        assert float(data["total"]) == float(receipt.total)
        assert float(data["rest"]) == float(receipt.rest)
        assert data["payment"]["type"] == receipt.payment_type
        assert float(data["payment"]["amount"]) == float(receipt.payment_amount)
        
        assert len(data["products"]) == 2
        product_names = [p["name"] for p in data["products"]]
        assert "Integration Test Product A" in product_names
        assert "Integration Test Product B" in product_names
    
    async def test_receipt_text_format_contains_all_essential_receipt_components(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test that receipt text format contains all essential components of a complete receipt."""
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        
        assert response.status_code == 200
        content = response.text
        
        assert "RECEIPT" in content
        assert "Store #1" in content
        # Check for product names (may be truncated in formatter)
        assert "Integration Test Product" in content  # Common part that should be visible
        assert "TOTAL: $87.50" in content
        assert "Cash: $100.00" in content
        assert "Change: $12.50" in content
        assert "Thank you for your purchase!" in content
        
        lines = content.split('\n')
        assert len(lines) > 10
        
        separator_lines = [line for line in lines if set(line) == {'-'}]
        assert len(separator_lines) >= 2
    
    async def test_receipt_formatter_service_produces_accurate_text_representation(self):
        """Test that receipt formatter service produces accurate text representation of receipt data."""
        formatter = ReceiptFormatter()
        
        receipt = ReceiptResponse(
            id=1,
            products=[
                ReceiptItemResponse(
                    name="Formatter Test Product",
                    price=Decimal("10.00"),
                    quantity=Decimal("2"),
                    total=Decimal("20.00")
                )
            ],
            payment=PaymentResponse(
                type="cash",
                amount=Decimal("25.00")
            ),
            total=Decimal("20.00"),
            rest=Decimal("5.00"),
            created_at=datetime.now(timezone.utc)
        )
        
        text = formatter.format_receipt_text(receipt)
        
        assert isinstance(text, str)
        assert "RECEIPT" in text
        assert "Formatter Test Product" in text
        assert "$20.00" in text
        assert "$25.00" in text
        assert "$5.00" in text
    
    async def test_public_endpoints_handle_nonexistent_receipts_with_proper_error_responses(
        self, 
        test_client: AsyncClient
    ):
        """Test that public endpoints handle requests for nonexistent receipts with proper error responses."""
        response = await test_client.get("/public/receipts/999999")
        assert response.status_code == 404
        
        response = await test_client.get("/public/receipts/999999/text")
        assert response.status_code == 404
    
    async def test_public_endpoints_validate_receipt_id_parameters_correctly(
        self, 
        test_client: AsyncClient
    ):
        """Test that public endpoints validate receipt ID parameters correctly and return appropriate errors."""
        response = await test_client.get("/public/receipts/invalid")
        assert response.status_code == 422
        
        response = await test_client.get("/public/receipts/invalid/text")
        assert response.status_code == 422
    
    async def test_complete_public_receipt_workflow_integration_between_json_and_text_endpoints(
        self, 
        test_client: AsyncClient, 
        test_user_with_receipt
    ):
        """Test complete integration workflow between JSON and text endpoints for public receipt viewing."""
        user, receipt = test_user_with_receipt
        
        json_response = await test_client.get(f"/public/receipts/{receipt.id}")
        assert json_response.status_code == 200
        json_data = json_response.json()
        
        text_response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        assert text_response.status_code == 200
        text_content = text_response.text
        
        assert json_data["id"] == receipt.id
        
        # Check that the receipt contains essential data consistency between JSON and text
        total_amount = f"${float(json_data['total']):.2f}"
        assert total_amount in text_content
        
        # Verify that product data from JSON appears in text (accounting for possible truncation)
        for product in json_data["products"]:
            # Check for at least the beginning of product names
            product_name_prefix = product["name"][:10]  # First 10 characters should be visible
            assert any(product_name_prefix in line for line in text_content.split('\n'))
        
        # Verify payment information consistency
        payment_amount = f"${float(json_data['payment']['amount']):.2f}"
        assert payment_amount in text_content
        
        # Verify change calculation consistency  
        change_amount = f"${float(json_data['rest']):.2f}"
        assert change_amount in text_content
