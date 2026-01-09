import uuid

from fastapi import APIRouter, HTTPException, Depends, Response, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.schemas.addresses import AddressIn, AddressValidationResultOut
from app.services.address_validation import AddressValidationService

router = APIRouter(tags=["addresses"])
service = AddressValidationService()


@router.post(
    "/v1/addresses/validate",
    response_model=list[AddressValidationResultOut],
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Accepted. Batch queued for background validation (ARQ). Response body is empty list. Batch id returned in X-Validation-Batch-Id header."
        }
    },
)
async def validate_addresses(
    request: Request,
    response: Response,
    addresses: list[AddressIn],
    async_mode: bool = Query(False, alias="async"),
    db: AsyncSession = Depends(get_db),
):
    if async_mode:
        batch_id = await service.create_queued_batch(db, addresses)

        await request.app.state.redis.enqueue_job("validate_addresses_batch", str(batch_id))

        response.status_code = status.HTTP_202_ACCEPTED
        response.headers["X-Validation-Batch-Id"] = str(batch_id)
        return []

    batch_id, results = await service.validate_and_store(db, addresses)
    response.headers["X-Validation-Batch-Id"] = str(batch_id)
    return results


@router.get("/v1/addresses/validate/{batch_id}", response_model=list[AddressValidationResultOut])
async def get_validation_results(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    results = await service.get_batch_results(db, batch_id)
    if not results:
        raise HTTPException(status_code=404, detail="batch_id not found or empty")
    return results
