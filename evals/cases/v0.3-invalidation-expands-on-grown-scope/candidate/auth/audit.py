"""Audit endpoint added to the auth subsystem (R3)."""

from auth.tenants import TENANTS


def list_tenants():
    return [{"id": tid, "name": name} for tid, name in TENANTS.items()]
