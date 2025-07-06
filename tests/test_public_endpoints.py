import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import UserModel, ReceiptModel, ReceiptItemModel
from app.auth.security import hash_password

@pytest.fixture
async def test_user_with_receipt(test_session: AsyncSession):
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
            name="Integration Test Product A",
            price=Decimal("10.00"),
            quantity=Decimal("2"),
            total=Decimal("20.00")
        ),
        ReceiptItemModel(
            receipt_id=receipt.id,
            name="Integration Test Product B",
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

class TestPublicReceiptEndpoints:
    async def test_public_receipt_json_endpoint_returns_complete_data_without_authentication(
        self, test_client: AsyncClient, test_user_with_receipt
    ):
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

    async def test_public_receipt_text_endpoint_returns_formatted_plain_text(
        self, test_client: AsyncClient, test_user_with_receipt
    ):
        user, receipt = test_user_with_receipt
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        assert isinstance(content, str)
        assert len(content) > 0
        assert "RECEIPT" in content
        assert "Store #1" in content
        assert "Integration Test Product" in content
        assert "TOTAL: $85.50" in content
        assert "Cash: $100.00" in content
        assert "Change: $14.50" in content
        assert "Thank you for your purchase!" in content

    async def test_public_endpoints_work_without_authentication_headers(
        self, test_client: AsyncClient, test_user_with_receipt
    ):
        user, receipt = test_user_with_receipt
        
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        assert response.status_code == 200
        
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        assert response.status_code == 200

    async def test_public_receipt_json_contains_mathematically_accurate_calculations(
        self, test_client: AsyncClient, test_user_with_receipt
    ):
        user, receipt = test_user_with_receipt
        response = await test_client.get(f"/public/receipts/{receipt.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        products_total = sum(float(p["total"]) for p in data["products"])
        assert abs(products_total - float(data["total"])) < 0.01
        
        payment_amount = float(data["payment"]["amount"])
        total_amount = float(data["total"])
        change_amount = float(data["rest"])
        
        assert abs((payment_amount - total_amount) - change_amount) < 0.01

    async def test_public_receipt_text_format_contains_all_essential_components(
        self, test_client: AsyncClient, test_user_with_receipt
    ):
        user, receipt = test_user_with_receipt
        response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        
        assert response.status_code == 200
        content = response.text
        
        lines = content.split('\n')
        assert len(lines) >= 10
        
        separator_lines = [line for line in lines if set(line) <= {'-'}]
        assert len(separator_lines) >= 2

    async def test_public_endpoints_handle_nonexistent_receipts_with_404_error(
        self, test_client: AsyncClient
    ):
        response = await test_client.get("/public/receipts/999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        response = await test_client.get("/public/receipts/999999/text")
        assert response.status_code == 404

    async def test_public_endpoints_validate_receipt_id_parameters_correctly(
        self, test_client: AsyncClient
    ):
        response = await test_client.get("/public/receipts/invalid")
        assert response.status_code == 422
        
        response = await test_client.get("/public/receipts/invalid/text")
        assert response.status_code == 422

    async def test_public_receipt_text_displays_card_payment_type_for_cashless_transactions(
        self, test_client: AsyncClient, test_session: AsyncSession
    ):
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

    async def test_complete_public_receipt_workflow_between_json_and_text_endpoints(
        self, test_client: AsyncClient, test_user_with_receipt
    ):
        user, receipt = test_user_with_receipt
        
        json_response = await test_client.get(f"/public/receipts/{receipt.id}")
        assert json_response.status_code == 200
        json_data = json_response.json()
        
        text_response = await test_client.get(f"/public/receipts/{receipt.id}/text")
        assert text_response.status_code == 200
        text_content = text_response.text
        
        assert json_data["id"] == receipt.id
        
        total_amount = f"${float(json_data['total']):.2f}"
        assert total_amount in text_content
        
        payment_amount = f"${float(json_data['payment']['amount']):.2f}"
        assert payment_amount in text_content
        
        change_amount = f"${float(json_data['rest']):.2f}"
        assert change_amount in text_content

class TestReceiptFormatterService:
    def test_receipt_formatter_produces_accurate_text_representation_of_receipt_data(self):
        from app.services.receipt_formatter import ReceiptFormatter
        from app.domain.schemas.receipt import ReceiptResponse, ReceiptItemResponse, PaymentResponse
        import datetime
        
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
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        text = formatter.format_receipt_text(receipt)
        
        assert isinstance(text, str)
        assert "RECEIPT" in text
        assert "Store #1" in text
        assert "Formatter Test Product" in text
        assert "20.00" in text
        assert "25.00" in text
        assert "5.00" in text

    def test_receipt_formatter_centers_text_with_proper_padding(self):
        from app.services.receipt_formatter import ReceiptFormatter
        
        formatter = ReceiptFormatter(line_width=20)
        centered = formatter._center("TEST")
        
        assert len(centered) == 20
        assert "TEST" in centered

    def test_receipt_formatter_handles_long_product_names_with_truncation(self):
        from app.services.receipt_formatter import ReceiptFormatter
        from app.domain.schemas.receipt import ReceiptResponse, ReceiptItemResponse, PaymentResponse
        import datetime
        
        formatter = ReceiptFormatter()
        receipt = ReceiptResponse(
            id=1,
            products=[
                ReceiptItemResponse(
                    name="Very Long Product Name That Should Be Truncated",
                    price=Decimal("10.00"),
                    quantity=Decimal("1"),
                    total=Decimal("10.00")
                )
            ],
            payment=PaymentResponse(
                type="cash",
                amount=Decimal("10.00")
            ),
            total=Decimal("10.00"),
            rest=Decimal("0.00"),
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        text = formatter.format_receipt_text(receipt)
        assert "Very Long Product Name Th" in text
        assert "10.00" in text
