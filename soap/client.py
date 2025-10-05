# client.py
from zeep import Client

main = Client(wsdl="http://localhost:8000/?wsdl")

# Task Service orchestrates other services
summary = main.service.process_order(
    "  Josh Groban  ",      # will be normalized by Utility called inside Entity
    "Widget-Pro",
    3,
    19.99,
    "ID",                   # ship-to country (VAT from microservice)
    1.4                     # estimated weight in kg (shipping from microservice)
)
print("OrderSummary:")
print(summary)

# Inspect the created resources via the Entity Service
print("\nAll customers:")
for c in main.service.list_customers():
    print(c.id, c.name)

print("\nAll orders:")
for o in main.service.list_orders():
    print(o.id, o.customer_id, o.product, o.qty, o.unit_price, o.subtotal, o.tax, o.shipping, o.total)
