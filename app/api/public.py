from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import Depends
from app.database.connection import get_session
from app.database.models import ReceiptModel
from app.domain.schemas.receipt import ReceiptResponse, ReceiptItemResponse, PaymentResponse
from app.services.receipt_formatter import ReceiptFormatter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_public_receipt(
    receipt_id: int,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(ReceiptModel).options(
        selectinload(ReceiptModel.items)
    ).where(ReceiptModel.id == receipt_id)
    
    result = await session.execute(stmt)
    receipt = result.scalar()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    return ReceiptResponse(
        id=receipt.id,
        products=[
            ReceiptItemResponse(
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                total=item.total
            )
            for item in receipt.items
        ],
        payment=PaymentResponse(
            type=receipt.payment_type,
            amount=receipt.payment_amount
        ),
        total=receipt.total,
        rest=receipt.rest,
        created_at=receipt.created_at
    )

@router.get("/receipts/{receipt_id}/text", response_class=PlainTextResponse)
async def get_public_receipt_text(
    receipt_id: int,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(ReceiptModel).options(
        selectinload(ReceiptModel.items)
    ).where(ReceiptModel.id == receipt_id)
    
    result = await session.execute(stmt)
    receipt = result.scalar()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receipt not found"
        )
    
    receipt_data = ReceiptResponse(
        id=receipt.id,
        products=[
            ReceiptItemResponse(
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                total=item.total
            )
            for item in receipt.items
        ],
        payment=PaymentResponse(
            type=receipt.payment_type,
            amount=receipt.payment_amount
        ),
        total=receipt.total,
        rest=receipt.rest,
        created_at=receipt.created_at
    )
    
    formatter = ReceiptFormatter()
    return formatter.format_receipt_text(receipt_data)
