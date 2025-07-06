from typing import List
from decimal import Decimal
from datetime import datetime
from app.domain.entities.receipt import Receipt, ReceiptItem, Payment
from app.domain.schemas.receipt import ReceiptResponse

class ReceiptFormatter:
    def __init__(self, line_width: int = 40):
        self.line_width = line_width
    
    def format_receipt_text(self, receipt: ReceiptResponse) -> str:
        lines = []
        
        lines.append(self._center("RECEIPT"))
        lines.append("-" * self.line_width)
        lines.append(self._center("Store #1"))
        lines.append("-" * self.line_width)
        
        for item in receipt.products:
            name = item.name[:25] if len(item.name) > 25 else item.name
            price_line = f"{float(item.quantity):.2f} x ${float(item.price):.2f}"
            lines.append(price_line)
            
            total_str = f"${float(item.total):.2f}"
            spacing = " " * (self.line_width - len(name) - len(total_str))
            lines.append(f"{name}{spacing}{total_str}")
        
        lines.append("-" * self.line_width)
        
        total_str = f"TOTAL: ${float(receipt.total):.2f}"
        lines.append(total_str)
        
        payment_method = "Card" if receipt.payment.type == "cashless" else "Cash"
        payment_str = f"{payment_method}: ${float(receipt.payment.amount):.2f}"
        lines.append(payment_str)
        
        change_str = f"Change: ${float(receipt.rest):.2f}"
        lines.append(change_str)
        
        lines.append("-" * self.line_width)
        lines.append(self._center(receipt.created_at.strftime("%m/%d/%Y %H:%M")))
        lines.append(self._center("Thank you for your purchase!"))
        
        return "\n".join(lines)
    
    def _center(self, text: str) -> str:
        return text.center(self.line_width)
