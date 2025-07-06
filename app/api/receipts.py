from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.database.connection import get_session
from app.database.models import ReceiptModel, ReceiptItemModel, UserModel
from app.domain.schemas.receipt import (
    ReceiptCreate, ReceiptResponse, ReceiptListResponse,
    ReceiptItemResponse, PaymentResponse
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/receipts", tags=["Receipts"])

@router.post("/", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(
    receipt_data: ReceiptCreate,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    total = sum(Decimal(str(item.price)) * Decimal(str(item.quantity)) for item in receipt_data.products)
    rest = Decimal(str(receipt_data.payment.amount)) - total
    
    if rest < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount is insufficient"
        )
    
    db_receipt = ReceiptModel(
        user_id=current_user.id,
        payment_type=receipt_data.payment.type.value,
        payment_amount=receipt_data.payment.amount,
        total=total,
        rest=rest
    )
    
    session.add(db_receipt)
    await session.flush()
    
    for item in receipt_data.products:
        item_total = Decimal(str(item.price)) * Decimal(str(item.quantity))
        db_item = ReceiptItemModel(
            receipt_id=db_receipt.id,
            name=item.name,
            price=item.price,
            quantity=item.quantity,
            total=item_total
        )
        session.add(db_item)
    
    await session.commit()
    await session.refresh(db_receipt)
    
    stmt = select(ReceiptModel).options(selectinload(ReceiptModel.items)).where(ReceiptModel.id == db_receipt.id)
    result = await session.execute(stmt)
    receipt = result.scalar()
    
    return ReceiptResponse(
        id=receipt.id,
        products=[
            ReceiptItemResponse(
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                total=item.total
            ) for item in receipt.items
        ],
        payment=PaymentResponse(
            type=receipt.payment_type,
            amount=receipt.payment_amount
        ),
        total=receipt.total,
        rest=receipt.rest,
        created_at=receipt.created_at
    )

@router.get("/", response_model=ReceiptListResponse)
async def get_receipts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    offset = (page - 1) * size
    
    count_stmt = select(func.count(ReceiptModel.id)).where(ReceiptModel.user_id == current_user.id)
    count_result = await session.execute(count_stmt)
    total = count_result.scalar()
    
    stmt = (
        select(ReceiptModel)
        .options(selectinload(ReceiptModel.items))
        .where(ReceiptModel.user_id == current_user.id)
        .order_by(desc(ReceiptModel.created_at))
        .offset(offset)
        .limit(size)
    )
    
    result = await session.execute(stmt)
    receipts = result.scalars().all()
    
    receipts_list = [
        ReceiptResponse(
            id=receipt.id,
            products=[
                ReceiptItemResponse(
                    name=item.name,
                    price=item.price,
                    quantity=item.quantity,
                    total=item.total
                ) for item in receipt.items
            ],
            payment=PaymentResponse(
                type=receipt.payment_type,
                amount=receipt.payment_amount
            ),
            total=receipt.total,
            rest=receipt.rest,
            created_at=receipt.created_at
        ) for receipt in receipts
    ]
    
    total_pages = (total + size - 1) // size
    has_next = page < total_pages
    has_prev = page > 1
    
    return ReceiptListResponse(
        items=receipts_list,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: int,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stmt = (
        select(ReceiptModel)
        .options(selectinload(ReceiptModel.items))
        .where(
            ReceiptModel.id == receipt_id,
            ReceiptModel.user_id == current_user.id
        )
    )
    
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
            ) for item in receipt.items
        ],
        payment=PaymentResponse(
            type=receipt.payment_type,
            amount=receipt.payment_amount
        ),
        total=receipt.total,
        rest=receipt.rest,
        created_at=receipt.created_at
    )
