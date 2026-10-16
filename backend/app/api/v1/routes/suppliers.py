from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from app.services.supplier_service import supplier_service

router = APIRouter(tags=["suppliers"])


@router.get("/suppliers")
def list_suppliers():
    """List all registered suppliers via SupplierService."""
    return supplier_service.list_suppliers()


@router.get("/suppliers/{supplier_id}/360")
def get_supplier_360(supplier_id: str):
    """Retrieve full 360 historical facts, PO metrics, defect trends, and capacity via SupplierService."""
    data = supplier_service.get_supplier_360(supplier_id)
    if data is not None:
        return data

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier {supplier_id} not found.")


