# micro_server.py
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Unicode, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

class MicroService(ServiceBase):
    @rpc(Unicode, _returns=Float)
    def get_vat_rate(ctx, country_code):
        # Super naive VAT table
        table = {"ID": 0.11, "MY": 0.08, "SG": 0.08, "US": 0.00, "GB": 0.20, "DE": 0.19}
        return float(table.get((country_code or "").upper(), 0.0))

    @rpc(Float, _returns=Float)
    def get_shipping_quote(ctx, total_weight_kg):
        # Toy shipping formula
        if total_weight_kg <= 0:
            return 0.0
        base = 3.50
        perkg = 2.25
        return base + perkg * total_weight_kg

micro_app = Application(
    services=[MicroService],
    tns="urn:examples.micro",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

if __name__ == "__main__":
    server = make_server("0.0.0.0", 8001, WsgiApplication(micro_app))
    print("Micro SOAP server on http://localhost:8001  (WSDL at ?wsdl)")
    server.serve_forever()
