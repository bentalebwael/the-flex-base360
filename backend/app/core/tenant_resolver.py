"""
Tenant resolver for authentication and tenant-scoped access.
"""
from typing import Optional, Dict, Any, List
import logging
from jose import jwt, JWTError

from ..database import supabase

logger = logging.getLogger(__name__)


class TenantResolver:
    """Resolve tenant_id without hardcoded tenant/email fallbacks."""

    @staticmethod
    def resolve_tenant_from_token(token_payload: dict) -> Optional[str]:
        """
        Extract tenant_id from JWT token payload.

        Args:
            token_payload: Decoded JWT payload

        Returns:
            Tenant ID if found, None otherwise
        """
        # Try user_metadata first (most common location)
        if 'user_metadata' in token_payload:
            tenant_id = token_payload['user_metadata'].get('tenant_id')
            if tenant_id:
                return tenant_id

        # Try app_metadata as fallback
        if 'app_metadata' in token_payload:
            tenant_id = token_payload['app_metadata'].get('tenant_id')
            if tenant_id:
                return tenant_id

        # Try root level
        tenant_id = token_payload.get('tenant_id')
        if tenant_id:
            return tenant_id

        logger.warning("No tenant_id found in token payload")
        return None

    @staticmethod
    def resolve_tenant_from_user(user_data: dict) -> Optional[str]:
        """
        Extract tenant_id from user data.

        Args:
            user_data: User data dictionary

        Returns:
            Tenant ID if found, None otherwise
        """
        # Check various possible locations
        if 'tenant_id' in user_data:
            return user_data['tenant_id']

        if 'user_metadata' in user_data:
            tenant_id = user_data['user_metadata'].get('tenant_id')
            if tenant_id:
                return tenant_id

        if 'app_metadata' in user_data:
            tenant_id = user_data['app_metadata'].get('tenant_id')
            if tenant_id:
                return tenant_id

        return None

    @staticmethod
    def _pick_preferred_tenant(tenant_rows: List[Dict[str, Any]]) -> Optional[str]:
        candidates = [row for row in (tenant_rows or []) if row.get("tenant_id")]
        if not candidates:
            return None

        def rank(row: Dict[str, Any]) -> tuple[int, str]:
            role = str(row.get("role") or "").lower()
            is_owner = bool(row.get("is_owner"))
            if is_owner or role == "owner":
                priority = 0
            elif role == "admin":
                priority = 1
            else:
                priority = 2
            return (priority, str(row.get("tenant_id")))

        return sorted(candidates, key=rank)[0]["tenant_id"]

    @staticmethod
    async def resolve_tenant_id(
        user_id: str,
        user_email: str,
        token: Optional[str] = None,
    ) -> Optional[str]:
        """
        Resolve tenant ID for a user.
        
        Args:
            user_id: User ID
            user_email: User email
            token: Optional bearer token (used to read tenant_id claims)
            
        Returns:
            Tenant ID, or None when it cannot be determined safely.
        """
        if token:
            try:
                claims = jwt.get_unverified_claims(token)
                tenant_from_token = TenantResolver.resolve_tenant_from_token(claims)
                if tenant_from_token:
                    return tenant_from_token
            except JWTError:
                logger.debug("TenantResolver: token claims unavailable for %s", user_email)
            except Exception as token_error:
                logger.warning(
                    "TenantResolver: failed to parse token for %s: %s",
                    user_email,
                    token_error,
                )

        try:
            tenant_rows_response = (
                supabase.service.table("user_tenants")
                .select("tenant_id, role, is_owner")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .execute()
            )
            tenant_rows = tenant_rows_response.data or []
            tenant_from_membership = TenantResolver._pick_preferred_tenant(tenant_rows)
            if tenant_from_membership:
                return tenant_from_membership
        except Exception as tenant_query_error:
            logger.warning(
                "TenantResolver: user_tenants lookup failed for %s (%s): %s",
                user_email,
                user_id,
                tenant_query_error,
            )

        try:
            admin_user_response = supabase.auth.admin.get_user_by_id(user_id)
            admin_user = getattr(admin_user_response, "user", None)
            if admin_user:
                user_data = {
                    "tenant_id": getattr(admin_user, "tenant_id", None),
                    "user_metadata": getattr(admin_user, "user_metadata", {}) or {},
                    "app_metadata": getattr(admin_user, "app_metadata", {}) or {},
                }
                tenant_from_user = TenantResolver.resolve_tenant_from_user(user_data)
                if tenant_from_user:
                    return tenant_from_user
        except Exception as user_lookup_error:
            logger.warning(
                "TenantResolver: admin user lookup failed for %s (%s): %s",
                user_email,
                user_id,
                user_lookup_error,
            )

        logger.warning(
            "TenantResolver: unable to resolve tenant_id for user %s (%s)",
            user_email,
            user_id,
        )
        return None

    @staticmethod
    async def update_user_tenant_metadata(user_id: str, tenant_id: str) -> None:
        """
        Update user metadata with tenant_id.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
        """
        # No-op in this resolver implementation.
        pass
