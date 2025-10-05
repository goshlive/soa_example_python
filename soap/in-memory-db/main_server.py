# main_server.py
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Float, Boolean, Array
from spyne import ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

# Use zeep to call the separate microservice
from zeep import Client as ZeepClient

# ------------------------
# In-memory "database"
# ------------------------
_customers = {}   # id -> {id, name}
_orders = {}      # id -> {id, customer_id, product, qty, unit_price, subtotal, tax, shipping, total}
_next_customer_id = 1
_next_order_id = 1

# ------------------------
# Types
# ------------------------
class Customer(ComplexModel):
    id = Integer
    name = Unicode

class Order(ComplexModel):
    id = Integer
    customer_id = Integer
    product = Unicode
    qty = Integer
    unit_price = Float
    subtotal = Float
    tax = Float
    shipping = Float
    total = Float

class OrderSummary(ComplexModel):
    order_id = Integer
    customer_name = Unicode
    product = Unicode
    qty = Integer
    unit_price = Float
    subtotal = Float
    tax = Float
    shipping = Float
    total = Float
    note = Unicode

# ------------------------
# Utility Service (stateless helpers)
# ------------------------
class UtilityService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def normalize_name(ctx, s):
        s = (s or "").strip()
        return " ".join(w.capitalize() for w in s.split())

    @rpc(Float, Integer, _returns=Float)
    def calc_subtotal(ctx, unit_price, qty):
        up = float(unit_price or 0.0)
        q = int(qty or 0)
        return round(up * q, 2)

# ------------------------
# Entity Service (CRUD). Uses Utility internally.
# ------------------------
class EntityService(ServiceBase):
    @rpc(Unicode, _returns=Integer)
    def create_customer(ctx, name):
        global _next_customer_id
        # Call UtilityService to normalize the name
        norm_name = UtilityService.normalize_name(ctx, name)
        cid = _next_customer_id
        _customers[cid] = {"id": cid, "name": norm_name}
        _next_customer_id += 1
        return cid

    @rpc(Unicode, _returns=Integer)
    def get_or_create_customer_by_name(ctx, name):
        norm = UtilityService.normalize_name(ctx, name)
        for c in _customers.values():
            if c["name"] == norm:
                return c["id"]
        return EntityService.create_customer(ctx, norm)

    @rpc(Integer, _returns=Customer)
    def get_customer(ctx, customer_id):
        c = _customers.get(customer_id)
        if not c:
            return Customer(id=-1, name="NOT_FOUND")
        return Customer(id=c["id"], name=c["name"])

    @rpc(_returns=Array(Customer))
    def list_customers(ctx):
        return [Customer(id=c["id"], name=c["name"]) for c in _customers.values()]

    @rpc(Integer, Unicode, Integer, Float, _returns=Integer)
    def create_order(ctx, customer_id, product, qty, unit_price):
        global _next_order_id
        # Use Utility to compute subtotal
        subtotal = UtilityService.calc_subtotal(ctx, unit_price, qty)
        oid = _next_order_id
        _orders[oid] = {
            "id": oid,
            "customer_id": int(customer_id),
            "product": product or "",
            "qty": int(qty or 0),
            "unit_price": float(unit_price or 0.0),
            "subtotal": float(subtotal),
            "tax": 0.0, "shipping": 0.0, "total": float(subtotal),
        }
        _next_order_id += 1
        return oid

    @rpc(Integer, _returns=Order)
    def get_order(ctx, order_id):
        o = _orders.get(order_id)
        if not o:
            return Order(id=-1, customer_id=-1, product="NOT_FOUND", qty=0, unit_price=0.0,
                         subtotal=0.0, tax=0.0, shipping=0.0, total=0.0)
        return Order(**o)

    @rpc(_returns=Array(Order))
    def list_orders(ctx):
        return [Order(**o) for o in _orders.values()]

# ------------------------
# Task Service (Business Process Orchestration)
# Calls Entity + Utility + external Microservice (SOAP).
# ------------------------
MICRO_WSDL = "http://localhost:8001/?wsdl"

class TaskService(ServiceBase):
    @rpc(Unicode, Unicode, Integer, Float, Unicode, Float, _returns=OrderSummary)
    def process_order(ctx, customer_name, product, qty, unit_price, ship_to_country, est_weight_kg):
        """
        High-level business task:
        1) Ensure customer exists (Entity)
        2) Create order (Entity uses Utility for subtotal)
        3) Call Microservice to get VAT & shipping
        4) Update order totals (Entity)
        5) Return a business-friendly summary
        """
        # 1) entity: get or create customer
        customer_id = EntityService.get_or_create_customer_by_name(ctx, customer_name)
        customer = EntityService.get_customer(ctx, customer_id)

        # 2) entity: create order with basic numbers
        order_id = EntityService.create_order(ctx, customer_id, product, qty, unit_price)
        order = EntityService.get_order(ctx, order_id)

        # 3) micro: call external SOAP for VAT + shipping
        micro = ZeepClient(wsdl=MICRO_WSDL)
        vat_rate = micro.service.get_vat_rate((ship_to_country or ""))
        shipping = micro.service.get_shipping_quote(float(est_weight_kg or 0.0))

        tax = round(order.subtotal * float(vat_rate or 0.0), 2)
        total = round(order.subtotal + tax + float(shipping or 0.0), 2)

        # 4) update order totals (simulate a tiny "update" inside our store)
        o = _orders[order_id]
        o["tax"] = tax
        o["shipping"] = float(shipping)
        o["total"] = total

        # 5) summary
        note = f"VAT {vat_rate*100:.1f}% for {ship_to_country.upper() if ship_to_country else 'N/A'}"
        return OrderSummary(
            order_id=order_id,
            customer_name=customer.name,
            product=order.product,
            qty=order.qty,
            unit_price=order.unit_price,
            subtotal=order.subtotal,
            tax=tax,
            shipping=float(shipping),
            total=total,
            note=note,
        )

# ------------------------
# Expose all three services in one SOAP endpoint
# ------------------------
app = Application(
    services=[EntityService, UtilityService, TaskService],
    tns="urn:examples.main",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_app = WsgiApplication(app)

if __name__ == "__main__":
    server = make_server("0.0.0.0", 8000, wsgi_app)
    print("Main SOAP server on http://localhost:8000  (WSDL at ?wsdl)")
    print("Services: EntityService, UtilityService, TaskService")
    server.serve_forever()
