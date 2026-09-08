"""Authorization helper for the auth subsystem."""

from auth.tenants import TENANTS


def authorize(tenant_id):
    return tenant_id in TENANTS
