from django import http
from django.core.handlers.wsgi import WSGIRequest


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, req):
        req_headers = req
        if isinstance(req, WSGIRequest):
            req_headers = req.headers

        if req.method == 'OPTIONS' and "access-control-request-method" in req_headers:
            return self.handle_preflight(req)

        res = self.get_response(req)

        # Allow cookies to be sent for CORS requests
        res['access-control-allow-credentials'] = 'true'
        CorsMiddleware.set_origin_access(req_headers, res)

        return res

    @staticmethod
    def set_origin_access(req, res):
        res['vary'] = 'Origin'
        if 'origin' in req:
            res['access-control-allow-origin'] = req['origin']
        else:
            res['access-control-allow-origin'] = '*'

    @staticmethod
    def handle_preflight(req):
        res = http.HttpResponse()

        CorsMiddleware.set_origin_access(req, res)
        res['access-control-allow-methods'] = 'POST, GET, OPTIONS, DELETE'
        res['Access-Control-Allow-Headers'] = 'Content-type'
        res['access-control-max-age'] = '86400'

        return res
