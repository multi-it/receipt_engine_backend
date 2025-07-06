from typing import List
from decimal import Decimal
from datetime import datetime
from app.domain.entities.receipt import Receipt, ReceiptItem, Payment
from app.domain.schemas.receipt import ReceiptResponse


class ReceiptFormatter:
    """Service for formatting receipts into text representation."""
    
    def __init__(self, line_width: int = 40):
        self.line_width = line_width
    
    def format_receipt_text(self, receipt: ReceiptResponse) -> str:
        """Format receipt to text view."""
        lines = []
        
        # Header
        lines.append(self._center("RECEIPT"))
        lines.append(self._center("Store #1"))
        lines.append("-" * self.line_width)
        
        # Items
        for item in receipt.products:
            # Quantity and price line
            qty_price = f"{float(item.quantity):.2f} x ${float(item.price):.2f}"
            lines.append(qty_price)
            
            # Name and total line
            name_width = self.line_width - 15  # Space for amount
            name = item.name[:name_width] if len(item.name) > name_width else item.name
            total_str = f"${float(item.total):.2f}"
            
            # Align name and total
            spacing = " " * (self.line_width - len(name) - len(total_str))
            lines.append(f"{name}{spacing}{total_str}")
        
        lines.append("-" * self.line_width)
        
        # Totals
        total_str = f"TOTAL: ${float(receipt.total):.2f}"
        lines.append(total_str)
        
        # Payment information
        payment_method = "Card" if receipt.payment.type == "cashless" else "Cash"
        payment_str = f"{payment_method}: ${float(receipt.payment.amount):.2f}"
        lines.append(payment_str)
        
        change_str = f"Change: ${float(receipt.rest):.2f}"
        lines.append(change_str)
        
        lines.append("-" * self.line_width)
        
        # Footer
        lines.append(self._center(receipt.created_at.strftime("%d.%m.%Y %H:%M")))
        lines.append(self._center("Thank you for your purchase!"))
        
        return "\n".join(lines)
    
    def _center(self, text: str) -> str:
        """Center text."""
        return text.center(self.line_width)
