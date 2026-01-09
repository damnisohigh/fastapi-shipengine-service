import uuid

from app.core.db.database import async_session_factory
from app.models.address_validation import AddressValidationBatch
from app.services.address_validation import AddressValidationService


async def validate_addresses_batch(ctx, batch_id: str) -> None:
    service = AddressValidationService()
    batch_uuid = uuid.UUID(batch_id)

    async with async_session_factory() as session:
        async with session.begin():
            batch = await session.get(AddressValidationBatch, batch_uuid)
            if batch is None:
                return
            if batch.status == "completed":
                return
            batch.status = "processing"

        await service.process_existing_batch(session, batch_uuid)
