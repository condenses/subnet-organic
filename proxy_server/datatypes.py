from pydantic import BaseModel, field_validator


class RegisterPayload(BaseModel):
    port: int


class OrganicPayload(BaseModel):
    context: str
    tier: str
    target_model: str
    miner_uid: int = -1
    top_incentive: float = 0.9

    @field_validator("context")
    @classmethod
    def validate_context_length(cls, v):
        if len(v) >= 25000:
            raise ValueError("context must be less than 25000 characters")
        return v


class MessagesPayload(BaseModel):
    messages: list[dict]
    top_incentive: float = 0.4
    miner_uid: int = -1


class Validator(BaseModel):
    endpoint: str
    stake: float


class ValidatorRegisterData(BaseModel):
    ss58_address: str
    ip_address: str
    port: int
    _id: str
    endpoint: str
    message: str
