# micro_server.py
from wsgiref.simple_server import make_server
from spyne import Application, rpc, ServiceBase, Integer, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

# ---------------------------------------------------
# TuitionPolicyService
# ---------------------------------------------------
# This microservice defines FIXED, NON-BREAKABLE rules
# for tuition calculation. It has no DB or business logic.
# It simply exposes pure, deterministic rules that other
# services (like TaskService) depend on.
# ---------------------------------------------------
class TuitionPolicyService(ServiceBase):
    @rpc(Integer, _returns=Float)
    def calc_tuition(ctx, credits):
        """
        Calculate tuition cost based on a fixed policy.
        Rule:
          base fee = 100.0
          cost per credit = 50.0
        """
        c = int(credits or 0)
        base_fee = 100.0
        per_credit = 50.0
        return float(base_fee + per_credit * c)

    @rpc(_returns=Integer)
    def max_credits(ctx):
        """
        Return the fixed maximum number of credits a
        student can take in one semester.
        """
        return 24

# ---------------------------------------------------
# Publish the service
# ---------------------------------------------------
micro_app = Application(
    [TuitionPolicyService],
    tns="urn:examples.micro",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

if __name__ == "__main__":
    print("Micro (Tuition Policy) SOAP server running...")
    print("URL: http://localhost:8001  (WSDL available at ?wsdl)")
    server = make_server("0.0.0.0", 8001, WsgiApplication(micro_app))
    server.serve_forever()
