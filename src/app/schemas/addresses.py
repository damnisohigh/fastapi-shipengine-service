from typing import Literal

from pydantic import BaseModel, Field


class AddressIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    company_name: str | None = None

    address_line1: str = Field(min_length=1)
    address_line2: str | None = None
    address_line3: str | None = None

    city_locality: str = Field(min_length=1)
    state_province: str = Field(min_length=1)
    postal_code: str | int | None = None
    country_code: str = Field(min_length=2, max_length=2)

    address_residential_indicator: Literal["unknown", "yes", "no"] | None = "unknown"


class AddressOut(AddressIn):
    pass


class ValidationMessage(BaseModel):
    code: str
    message: str
    level: Literal["info", "warning", "error"] = "info"


class AddressValidationResultOut(BaseModel):
    status: Literal["verified", "unverified", "error"]
    original_address: AddressOut
    matched_address: AddressOut
    messages: list[ValidationMessage] = []
