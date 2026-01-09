import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address_validation import AddressValidationBatch, AddressValidationItem
from app.schemas.addresses import (
    AddressIn,
    AddressOut,
    AddressValidationResultOut,
    ValidationMessage,
)

class AddressValidationService:
    def _normalize(self, addr: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}

        for key, value in addr.items():
            if isinstance(value, str):
                v = value.strip()

                if key == "address_residential_indicator":
                    v = v.lower()
                    if v not in {"unknown", "yes", "no"}:
                        v = "unknown"
                    normalized[key] = v
                    continue

                if key == "country_code":
                    normalized[key] = v.upper()
                    continue

                if key == "email":
                    normalized[key] = v.lower()
                    continue

                normalized[key] = v.upper()
            else:
                normalized[key] = value

        if "address_residential_indicator" not in normalized:
            normalized["address_residential_indicator"] = "unknown"

        return normalized


    def _status_and_messages(self, addr: AddressIn) -> tuple[str, list[ValidationMessage]]:
        msgs: list[ValidationMessage] = []
        if addr.country_code.upper() == "US" and not addr.postal_code:
            msgs.append(
                ValidationMessage(code="missing_postal_code", message="postal_code is recommended for US", level="warning")
            )
        return ("verified", msgs)
    
    async def create_queued_batch(self, session, addresses: list[AddressIn]) -> uuid.UUID:
        payload = [a.model_dump() for a in addresses]

        async with session.begin():
            batch = AddressValidationBatch(status="queued", request_payload=payload)
            session.add(batch)
            await session.flush()
            return batch.id

    async def process_existing_batch(self, session, batch_id: uuid.UUID) -> None:
        batch = await session.get(AddressValidationBatch, batch_id)
        if batch is None or not batch.request_payload:
            async with session.begin():
                if batch is not None:
                    batch.status = "failed"
            return

        addresses = [AddressIn.model_validate(a) for a in batch.request_payload]

        async with session.begin():
            existing = await session.execute(
                select(AddressValidationItem.id).where(AddressValidationItem.batch_id == batch_id).limit(1)
            )
            if existing.first() is not None:
                batch.status = "completed"
                return

            for addr in addresses:
                original_dict = addr.model_dump()
                matched_dict = self._normalize(original_dict)
                status, messages = self._status_and_messages(addr)

                session.add(
                    AddressValidationItem(
                        batch_id=batch_id,
                        status=status,
                        original_address=original_dict,
                        matched_address=matched_dict,
                        messages=[m.model_dump() for m in messages],
                    )
                )

            batch.status = "completed"

    async def validate_and_store(
        self, session: AsyncSession, addresses: list[AddressIn]
    ) -> tuple[uuid.UUID, list[AddressValidationResultOut]]:
        results: list[AddressValidationResultOut] = []

        async with session.begin():
            batch = AddressValidationBatch(status="completed")
            session.add(batch)
            await session.flush()

            for addr in addresses:
                original_dict = addr.model_dump()
                matched_dict = self._normalize(original_dict)

                status, messages = self._status_and_messages(addr)
                messages_json = [m.model_dump() for m in messages]

                item = AddressValidationItem(
                    batch_id=batch.id,
                    status=status,
                    original_address=original_dict,
                    matched_address=matched_dict,
                    messages=messages_json,
                )
                session.add(item)

                results.append(
                    AddressValidationResultOut(
                        status=status,
                        original_address=AddressOut.model_validate(original_dict),
                        matched_address=AddressOut.model_validate(matched_dict),
                        messages=messages,
                    )
                )

        return batch.id, results


    async def get_batch_results(self, session: AsyncSession, batch_id: uuid.UUID) -> list[AddressValidationResultOut]:
        q = select(AddressValidationItem).where(AddressValidationItem.batch_id == batch_id).order_by(AddressValidationItem.created_at)
        rows = (await session.execute(q)).scalars().all()

        out: list[AddressValidationResultOut] = []
        for r in rows:
            out.append(
                AddressValidationResultOut(
                    status=r.status,
                    original_address=r.original_address,
                    matched_address=r.matched_address,
                    messages=[ValidationMessage.model_validate(m) for m in (r.messages or [])],
                )
            )
        return out
