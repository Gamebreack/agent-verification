def can_view(user_tenant: str | None, resource_tenant: str | None) -> bool:
    return bool(user_tenant and resource_tenant)
