"""
Payment Service
SMS Service
"""

import asyncio
import logging
from services.sms.service import SMSService
from services.payment.service import PaymentService
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services
    services = await asyncio.gather(
        PaymentService.get_instance(), SMSService.get_instance()
    )

    # Register routes
    for service in services:
        service.register_fastapi_routes(app)

    yield

    # Teardown

    # Cleanup services
    await asyncio.gather(*[service.cleanup() for service in services])


app = FastAPI(lifespan=lifespan)
