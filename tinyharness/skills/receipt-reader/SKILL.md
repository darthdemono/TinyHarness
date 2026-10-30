---
name: receipt-reader
description: Read a photo of a receipt or invoice into rows of item, quantity and price. Use when the user shares a receipt image and wants a table or CSV.
---

# Receipt reader

1. Read every line item: item name, quantity, unit price, line total.
2. Copy numbers exactly as printed; mark unreadable ones as null instead of guessing.
3. Report the printed total and whether the line totals add up to it.
4. Keep the original language of the item names.
