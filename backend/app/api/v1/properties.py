from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from sqlalchemy import text
from app.core.database_pool import DatabasePool
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()


# ─── Shared helper ────────────────────────────────────────────────────────────

async def _get_session():
    """Return an initialised DatabasePool session context-manager."""
    db_pool = DatabasePool()
    await db_pool.initialize()
    if not db_pool.session_factory:
        raise HTTPException(status_code=503, detail="Database pool not available")
    return db_pool


# ──────────────────────────────────────────────────────────────────────────────
# Static / special routes MUST come before /{property_id} to avoid conflicts
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties/in-radius")
async def get_properties_in_radius(
    center_lat: float,
    center_lng: float,
    radius_km: float,
    exclude_property_id: Optional[str] = None,
    city_filter: Optional[str] = None,
    bedrooms: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return properties within a given radius (km) of a centre point."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            # Build optional clauses
            extra = ""
            params: Dict[str, Any] = {"tenant_id": tenant_id}

            if exclude_property_id:
                extra += " AND id != :exclude_id"
                params["exclude_id"] = exclude_property_id
            if city_filter:
                extra += " AND LOWER(city) LIKE :city_filter"
                params["city_filter"] = f"%{city_filter.lower()}%"
            if bedrooms is not None:
                extra += " AND bedrooms = :bedrooms"
                params["bedrooms"] = bedrooms

            query = text(
                f"SELECT * FROM properties WHERE tenant_id = :tenant_id{extra}"
            )
            result = await session.execute(query, params)
            rows = [dict(r._mapping) for r in result.fetchall()]

        # Haversine distance filter in Python
        import math

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(dlon / 2) ** 2
            )
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        filtered = []
        for prop in rows:
            lat = prop.get("latitude") or prop.get("lat")
            lng = prop.get("longitude") or prop.get("lng")
            if lat is not None and lng is not None:
                dist = haversine(center_lat, center_lng, float(lat), float(lng))
                if dist <= radius_km:
                    prop["distance_km"] = round(dist, 3)
                    filtered.append(prop)

        return {"items": filtered, "total": len(filtered)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties in radius: {e}")


@router.get("/properties/check-exists")
async def check_property_exists(
    hostaway_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Check whether a property with the given hostaway_id exists for the tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT id FROM properties "
                    "WHERE tenant_id = :tenant_id AND hostaway_id = :hostaway_id "
                    "LIMIT 1"
                ),
                {"tenant_id": tenant_id, "hostaway_id": hostaway_id},
            )
            row = result.fetchone()

        return {"exists": row is not None}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check property existence: {e}")


@router.delete("/properties/notes/{note_id}")
async def delete_property_note(
    note_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a property note by its ID."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            await session.execute(
                text(
                    "DELETE FROM property_notes "
                    "WHERE id = :note_id AND tenant_id = :tenant_id"
                ),
                {"note_id": note_id, "tenant_id": tenant_id},
            )
            await session.commit()

        return {"deleted": True, "id": note_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Collection endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties")
async def get_properties(
    city: Optional[str] = None,
    portfolio: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 1000,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return a paginated, filtered list of properties for the tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            extra = ""
            params: Dict[str, Any] = {"tenant_id": tenant_id}

            if city:
                extra += " AND LOWER(city) LIKE :city"
                params["city"] = f"%{city.lower()}%"
            if portfolio:
                extra += " AND portfolio = :portfolio"
                params["portfolio"] = portfolio
            if status:
                extra += " AND status = :status"
                params["status"] = status
            if search:
                extra += (
                    " AND (LOWER(name) LIKE :search"
                    " OR LOWER(address) LIKE :search"
                    " OR LOWER(city) LIKE :search)"
                )
                params["search"] = f"%{search.lower()}%"

            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset

            query = text(
                f"SELECT * FROM properties "
                f"WHERE tenant_id = :tenant_id{extra} "
                f"LIMIT :limit OFFSET :offset"
            )
            result = await session.execute(query, params)
            rows = [dict(r._mapping) for r in result.fetchall()]

        return {"items": rows, "total": len(rows), "page": page, "page_size": page_size}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties: {e}")


@router.post("/properties")
async def create_property(
    property_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a new property for the tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        property_data["tenant_id"] = tenant_id
        property_data.pop("id", None)

        columns = ", ".join(property_data.keys())
        placeholders = ", ".join(f":{k}" for k in property_data.keys())

        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    f"INSERT INTO properties ({columns}) VALUES ({placeholders}) "
                    f"RETURNING *"
                ),
                property_data,
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create property")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create property: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Single property endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties/{property_id}")
async def get_property(
    property_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return a single property by ID (tenant-scoped)."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT * FROM properties "
                    "WHERE id = :id AND tenant_id = :tenant_id "
                    "LIMIT 1"
                ),
                {"id": property_id, "tenant_id": tenant_id},
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Property not found")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch property: {e}")


@router.put("/properties/{property_id}")
async def update_property(
    property_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update a property (tenant-scoped)."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        updates.pop("id", None)
        updates.pop("tenant_id", None)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["_id"] = property_id
        updates["_tenant_id"] = tenant_id

        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    f"UPDATE properties SET {set_clause} "
                    f"WHERE id = :_id AND tenant_id = :_tenant_id "
                    f"RETURNING *"
                ),
                updates,
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Property not found")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update property: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Notes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties/{property_id}/notes")
async def get_property_notes(
    property_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return all notes for a property."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT * FROM property_notes "
                    "WHERE property_id = :property_id AND tenant_id = :tenant_id "
                    "ORDER BY created_at DESC"
                ),
                {"property_id": property_id, "tenant_id": tenant_id},
            )
            rows = [dict(r._mapping) for r in result.fetchall()]

        return {"items": rows, "total": len(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notes: {e}")


@router.post("/properties/{property_id}/notes")
async def create_property_note(
    property_id: str,
    payload: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a note for a property."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "INSERT INTO property_notes (property_id, tenant_id, note, created_by) "
                    "VALUES (:property_id, :tenant_id, :note, :created_by) "
                    "RETURNING *"
                ),
                {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "note": payload.get("note", ""),
                    "created_by": getattr(current_user, "id", None),
                },
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create note")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Appliances
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties/{property_id}/appliances")
async def get_property_appliances(
    property_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return all appliances for a property."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT * FROM property_appliances "
                    "WHERE property_id = :property_id AND tenant_id = :tenant_id"
                ),
                {"property_id": property_id, "tenant_id": tenant_id},
            )
            rows = [dict(r._mapping) for r in result.fetchall()]

        return {"items": rows, "total": len(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch appliances: {e}")


@router.post("/properties/{property_id}/appliances")
async def create_property_appliance(
    property_id: str,
    appliance_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create an appliance for a property."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        appliance_data["property_id"] = property_id
        appliance_data["tenant_id"] = tenant_id
        appliance_data.pop("id", None)

        columns = ", ".join(appliance_data.keys())
        placeholders = ", ".join(f":{k}" for k in appliance_data.keys())

        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    f"INSERT INTO property_appliances ({columns}) "
                    f"VALUES ({placeholders}) RETURNING *"
                ),
                appliance_data,
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create appliance")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create appliance: {e}")


@router.put("/properties/{property_id}/appliances/{appliance_id}")
async def update_property_appliance(
    property_id: str,
    appliance_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update a property appliance."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        updates.pop("id", None)
        updates.pop("tenant_id", None)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["_id"] = appliance_id
        updates["_property_id"] = property_id
        updates["_tenant_id"] = tenant_id

        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    f"UPDATE property_appliances SET {set_clause} "
                    f"WHERE id = :_id AND property_id = :_property_id "
                    f"AND tenant_id = :_tenant_id RETURNING *"
                ),
                updates,
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Appliance not found")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update appliance: {e}")


@router.delete("/properties/{property_id}/appliances/{appliance_id}")
async def delete_property_appliance(
    property_id: str,
    appliance_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a property appliance."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            await session.execute(
                text(
                    "DELETE FROM property_appliances "
                    "WHERE id = :id AND property_id = :property_id "
                    "AND tenant_id = :tenant_id"
                ),
                {"id": appliance_id, "property_id": property_id, "tenant_id": tenant_id},
            )
            await session.commit()

        return {"deleted": True, "id": appliance_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete appliance: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Contracts
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties/{property_id}/contracts")
async def get_property_contracts(
    property_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return all contracts for a property."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT * FROM property_contracts "
                    "WHERE property_id = :property_id AND tenant_id = :tenant_id "
                    "ORDER BY created_at DESC"
                ),
                {"property_id": property_id, "tenant_id": tenant_id},
            )
            rows = [dict(r._mapping) for r in result.fetchall()]

        return {"items": rows, "total": len(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contracts: {e}")


@router.post("/properties/{property_id}/contracts")
async def create_property_contract(
    property_id: str,
    contract_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create a contract for a property."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        contract_data["property_id"] = property_id
        contract_data["tenant_id"] = tenant_id
        contract_data.pop("id", None)

        columns = ", ".join(contract_data.keys())
        placeholders = ", ".join(f":{k}" for k in contract_data.keys())

        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    f"INSERT INTO property_contracts ({columns}) "
                    f"VALUES ({placeholders}) RETURNING *"
                ),
                contract_data,
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create contract")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create contract: {e}")


@router.put("/properties/{property_id}/contracts/{contract_id}")
async def update_property_contract(
    property_id: str,
    contract_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update a property contract."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        updates.pop("id", None)
        updates.pop("tenant_id", None)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{k} = :{k}" for k in updates.keys())
        updates["_id"] = contract_id
        updates["_property_id"] = property_id
        updates["_tenant_id"] = tenant_id

        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    f"UPDATE property_contracts SET {set_clause} "
                    f"WHERE id = :_id AND property_id = :_property_id "
                    f"AND tenant_id = :_tenant_id RETURNING *"
                ),
                updates,
            )
            await session.commit()
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Contract not found")

        return dict(row._mapping)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update contract: {e}")


@router.delete("/properties/{property_id}/contracts/{contract_id}")
async def delete_property_contract(
    property_id: str,
    contract_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Delete a property contract."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            await session.execute(
                text(
                    "DELETE FROM property_contracts "
                    "WHERE id = :id AND property_id = :property_id "
                    "AND tenant_id = :tenant_id"
                ),
                {"id": contract_id, "property_id": property_id, "tenant_id": tenant_id},
            )
            await session.commit()

        return {"deleted": True, "id": contract_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete contract: {e}")


@router.get("/properties/{property_id}/contracts/{contract_id}/signed-url")
async def get_contract_signed_url(
    property_id: str,
    contract_id: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get a signed URL for a contract document stored in Supabase Storage."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT document_path, document_name FROM property_contracts "
                    "WHERE id = :id AND property_id = :property_id "
                    "AND tenant_id = :tenant_id LIMIT 1"
                ),
                {"id": contract_id, "property_id": property_id, "tenant_id": tenant_id},
            )
            row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Contract not found")

        document_path = row._mapping.get("document_path")
        document_name = row._mapping.get("document_name", "contract")

        if not document_path:
            raise HTTPException(status_code=404, detail="No document attached to this contract")

        # Generate signed URL via Supabase Storage (storage client, not DB)
        from app.database import supabase as supabase_client
        signed = supabase_client.storage.from_("property-contracts").create_signed_url(
            document_path, 3600
        )

        return {
            "signed_url": signed.get("signedURL") or signed.get("signed_url", ""),
            "expires_in": 3600,
            "document_name": document_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Availability
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/properties/{property_id}/availability")
async def get_property_availability(
    property_id: str,
    start: str,
    end: str,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return availability records for a property between start and end dates."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        db_pool = await _get_session()
        async with db_pool.get_session() as session:
            result = await session.execute(
                text(
                    "SELECT * FROM property_availability "
                    "WHERE property_id = :property_id AND tenant_id = :tenant_id "
                    "AND date >= :start AND date <= :end "
                    "ORDER BY date"
                ),
                {"property_id": property_id, "tenant_id": tenant_id, "start": start, "end": end},
            )
            rows = [dict(r._mapping) for r in result.fetchall()]

        return {"items": rows, "total": len(rows)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch availability: {e}")
