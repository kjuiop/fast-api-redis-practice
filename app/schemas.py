from pydantic import BaseModel


class LoginRequest(BaseModel):
    user_id: str


class UserProfileUpdate(BaseModel):
    name: str
    email: str
    tier: str