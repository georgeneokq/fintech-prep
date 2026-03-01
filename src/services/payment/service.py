import logging
import json
from typing import Optional
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field, field_validator
from confluent_kafka.aio import AIOProducer
from fastapi.responses import Response
from services.base_service import BaseService
from services.payment.types import Currency
from uuid import uuid4


logger = logging.getLogger(__name__)


class PaymentMessage(BaseModel):
    from_user: str
    to_user: str
    amount: int = Field(gt=0)  # Amount must be greater than 0
    currency: Currency

    @field_validator('from_user', 'to_user')
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('User identifier cannot be empty')
        return value


class PaymentService(BaseService):
    instance: Optional["PaymentService"] = None
    producer: AIOProducer

    def __init__(self):
        self.producer = AIOProducer({"bootstrap.servers": "localhost:9092"})

    @classmethod
    async def get_instance(cls):
        if not cls.instance:
            cls.instance = PaymentService()
        return cls.instance

    async def process_payment(
        self,
        from_user: str,
        to_user: str,
        amount: float,
        currency: Currency,
        idempotency_key: str,
    ):
        # Payment complete. Simulated. In actual, use idempotency key to prevent double payment.
        # Use base idempotency key, form a new one. In actual implementation, I expect to store the idempotency key in a database
        # for a safe amount of time, e.g. 10 minutes, to prevent double payment
        # I rather not share the same idempotency key for different services as it eliminates the option of using the same table for storing keys
        payment_idempotency_key = f"payment_{idempotency_key}"
        print(f"Processed payment of {amount}{currency.value}")

        # Form the JSON object for SMSService to send SMS
        sms_idempotency_key = f"sms_{idempotency_key}"
        sms_request_body = {
            "from": from_user,
            "to": to_user,
            "amount": amount,
            "currency": currency.value,
            "idempotency_key": sms_idempotency_key,
        }

        # produce() returns a Future; first await the coroutine to get the Future,
        # then await the Future to get the delivered Message.
        delivery_future = await self.producer.produce(
            "sms_request", value=json.dumps(sms_request_body)
        )
        delivered_msg = await delivery_future

        return Response()

    async def cleanup(self):
        await self.producer.flush(timeout=5.0)
        await self.producer.close()

    # TODO: Would have loved to move route handler functions to another file route_handlers.py,
    # but running into a circular import issue. Think of a more scalable solution
    async def payment_route(self, request: Request):
        body: dict = await request.json()
        from_user: str = body["from_user"]
        to_user: str = body["to_user"]
        amount: float = body["amount"]
        currency: str = body["currency"]
        currency_enum_value = Currency(currency)

        # TODO: Input error handling before prod

        # Send payment
        # Idempotency key to prevent duplicate Payment, SMS
        base_idempotency_key = f"{from_user}_{uuid4()}"
        payment_service = await PaymentService.get_instance()
        await payment_service.process_payment(
            from_user=from_user,
            to_user=to_user,
            amount=amount,
            currency=currency_enum_value,
            idempotency_key=base_idempotency_key,
        )

        return Response()

    def register_fastapi_routes(self, app: FastAPI):
        app.post("/payment")(self.payment_route)
