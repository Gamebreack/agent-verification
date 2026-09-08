"""Tenant registry for the auth subsystem."""


TENANTS = {}


def add_tenant(tenant_id, name):
    TENANTS[tenant_id] = name
