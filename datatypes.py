from pydantic import BaseModel


class RegisterPayload(BaseModel):
    port: int


class OrganicPayload(BaseModel):
    context: str
    tier: str
    target_model: str
    miner_uid: int = -1
    top_incentive: float = 0.9


class Validator(BaseModel):
    endpoint: str
    stake: float


class ValidatorRegisterData(BaseModel):
    ss58_address: str
    ip_address: str
    port: int
    _id: str
    endpoint: str
