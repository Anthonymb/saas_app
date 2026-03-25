from pydantic import BaseModel


class PaymentWebhookRequest(BaseModel):
    event_type: str
    provider_ref: str
    metadata: dict | None = None
