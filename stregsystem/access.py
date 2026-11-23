import ipaddress
import logging
from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden

try:
    from oauth2_provider.decorators import protected_resource
except ImportError:
    # Ships with the OIDC provider; without it, token-protected endpoints are refused.
    protected_resource = None

logger = logging.getLogger(__name__)


def _forbidden(request, *args, **kwargs):
    return HttpResponseForbidden('Not available from this network.')


def client_ip(request):
    """
    The client IP as the nearest proxy saw it. Proxies append to X-Forwarded-For, so the last
    entry is the peer address; anything before it is client supplied.
    """
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[-1].strip()
    return forwarded or request.META.get('REMOTE_ADDR', '')


def is_onsite(request):
    try:
        ip = ipaddress.ip_address(client_ip(request))
    except ValueError:
        return False
    for cidr in settings.ONSITE_CIDRS:
        try:
            if ip in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            logger.warning('Ignoring invalid ONSITE_CIDRS entry: %r', cidr)
    return False


def onsite_only(view):
    """Restricts an endpoint to the club network."""

    @wraps(view)
    def _view(request, *args, **kwargs):
        if is_onsite(request):
            return view(request, *args, **kwargs)
        return _forbidden(request)

    return _view


def onsite_or_scope(scope):
    """Allows off-site requests with an OIDC token carrying the given scope."""

    def decorator(view):
        @wraps(view)
        def _view(request, *args, **kwargs):
            if is_onsite(request):
                return view(request, *args, **kwargs)
            if protected_resource is None:
                return _forbidden(request)
            return protected_resource(scopes=[scope])(view)(request, *args, **kwargs)

        return _view

    return decorator


def scope_only(scope):
    """Requires an OIDC token carrying the given scope, from any network."""

    def decorator(view):
        if protected_resource is None:
            return _forbidden
        return protected_resource(scopes=[scope])(view)

    return decorator
