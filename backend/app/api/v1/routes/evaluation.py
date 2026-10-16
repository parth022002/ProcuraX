from fastapi import APIRouter, HTTPException, status

router = APIRouter(tags=["evaluation"])


@router.post("/evaluation/run")
def scaffold_endpoint_evaluation():
    """Benchmark execution. Scaffold only; implement against docs/API_CONTRACTS.md."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This ProcuraX capability is scaffolded but not implemented yet. See docs/IMPLEMENTATION_PLAN.md.",
    )
