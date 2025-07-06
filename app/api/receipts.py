from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import date
from typing import Optional, List, Dict, Any

from app.database.connection import get_session
from app.database.models import ReceiptModel, ReceiptItemModel, UserModel
from app.domain.schemas.receipt import (
    ReceiptCreate,
    ReceiptResponse,
    ReceiptListResponse,
    ReceiptItemResponse,
    PaymentResponse,
    ReceiptStatsResponse,
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/receipts", tags=["Receipts"])


def _to_schema(r: ReceiptModel) -> ReceiptResponse:
    return ReceiptResponse(
        id=r.id,
        products=[
            ReceiptItemResponse(
                name=i.name,
                price=i.price,
                quantity=i.quantity,
                total=i.total,
            )
            for i in r.items
        ],
        payment=PaymentResponse(type=r.payment_type, amount=r.payment_amount),
        total=r.total,
        rest=r.rest,
        created_at=r.created_at,
    )


@router.post(
    "",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/",
    response_model=ReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_receipt(
    receipt_data: ReceiptCreate,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReceiptResponse:
    total = sum(
        Decimal(str(i.price)) * Decimal(str(i.quantity)) for i in receipt_data.products
    )
    rest = Decimal(str(receipt_data.payment.amount)) - total
    if rest < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount is insufficient",
        )

    db_receipt = ReceiptModel(
        user_id=current_user.id,
        payment_type=receipt_data.payment.type.value,
        payment_amount=receipt_data.payment.amount,
        total=total,
        rest=rest,
    )
    session.add(db_receipt)
    await session.flush()

    for p in receipt_data.products:
        session.add(
            ReceiptItemModel(
                receipt_id=db_receipt.id,
                name=p.name,
                price=p.price,
                quantity=p.quantity,
                total=Decimal(str(p.price)) * Decimal(str(p.quantity)),
            )
        )

    await session.commit()
    await session.refresh(db_receipt)

    stmt = (
        select(ReceiptModel)
        .options(selectinload(ReceiptModel.items))
        .where(ReceiptModel.id == db_receipt.id)
    )
    receipt = (await session.execute(stmt)).scalar()
    return _to_schema(receipt)


@router.get("")
@router.get("/")
async def get_receipts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    min_total: Optional[Decimal] = Query(None, ge=0),
    max_total: Optional[Decimal] = Query(None, ge=0),
    payment_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReceiptListResponse:
    valid_sort_fields, valid_sort_orders = {"created_at", "total", "payment_amount"}, {
        "asc",
        "desc",
    }
    if sort_by not in valid_sort_fields or sort_order not in valid_sort_orders:
        raise HTTPException(status_code=422, detail="Invalid sorting parameters")

    offset = (page - 1) * size
    stmt = select(ReceiptModel).where(ReceiptModel.user_id == current_user.id)
    cnt = select(func.count(ReceiptModel.id)).where(ReceiptModel.user_id == current_user.id)

    if date_from:
        stmt = stmt.where(ReceiptModel.created_at >= date_from)
        cnt = cnt.where(ReceiptModel.created_at >= date_from)
    if date_to:
        stmt = stmt.where(ReceiptModel.created_at <= date_to)
        cnt = cnt.where(ReceiptModel.created_at <= date_to)
    if min_total is not None:
        stmt = stmt.where(ReceiptModel.total >= min_total)
        cnt = cnt.where(ReceiptModel.total >= min_total)
    if max_total is not None:
        stmt = stmt.where(ReceiptModel.total <= max_total)
        cnt = cnt.where(ReceiptModel.total <= max_total)
    if payment_type:
        stmt = stmt.where(ReceiptModel.payment_type == payment_type)
        cnt = cnt.where(ReceiptModel.payment_type == payment_type)
    if search:
        subq = select(ReceiptItemModel.receipt_id).where(ReceiptItemModel.name.ilike(f"%{search}%"))
        stmt = stmt.where(ReceiptModel.id.in_(subq))
        cnt = cnt.where(ReceiptModel.id.in_(subq))

    col = (
        ReceiptModel.created_at
        if sort_by == "created_at"
        else ReceiptModel.total
        if sort_by == "total"
        else ReceiptModel.payment_amount
    )
    stmt = stmt.order_by(desc(col) if sort_order == "desc" else col)
    stmt = stmt.options(selectinload(ReceiptModel.items)).offset(offset).limit(size)

    total = (await session.execute(cnt)).scalar()
    receipts = (await session.execute(stmt)).scalars().all()

    items = [_to_schema(r) for r in receipts]
    total_pages = (total + size - 1) // size
    return ReceiptListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/stats")
async def get_stats(
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReceiptStatsResponse:
    s = (
        await session.execute(
            select(
                func.count(ReceiptModel.id),
                func.sum(ReceiptModel.total),
                func.avg(ReceiptModel.total),
                func.max(ReceiptModel.total),
                func.min(ReceiptModel.total),
            ).where(ReceiptModel.user_id == current_user.id)
        )
    ).first()

    p_rows = (
        await session.execute(
            select(
                ReceiptModel.payment_type,
                func.count(ReceiptModel.id),
                func.sum(ReceiptModel.total),
            )
            .where(ReceiptModel.user_id == current_user.id)
            .group_by(ReceiptModel.payment_type)
        )
    ).all()

    return ReceiptStatsResponse(
        total_receipts=s[0] or 0,
        total_amount=s[1] or Decimal("0"),
        average_amount=s[2] or Decimal("0"),
        max_amount=s[3] or Decimal("0"),
        min_amount=s[4] or Decimal("0"),
        payment_type_stats=[{"type": t, "count": c, "total": ttl} for t, c, ttl in p_rows],
    )


@router.get("/{receipt_id}")
async def get_receipt(
    receipt_id: int,
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReceiptResponse:
    stmt = (
        select(ReceiptModel)
        .options(selectinload(ReceiptModel.items))
        .where(ReceiptModel.id == receipt_id, ReceiptModel.user_id == current_user.id)
    )
    receipt = (await session.execute(stmt)).scalar()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return _to_schema(receipt)
