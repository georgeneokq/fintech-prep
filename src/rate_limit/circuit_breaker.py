import time
import logging
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"  # Everything is fine
    OPEN = "OPEN"  # Failure detected, stopping all requests
    HALF_OPEN = "HALF_OPEN"  # Testing if the service recovered


class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = None

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN and self.last_failure_time:
                # Check if it's time to try a recovery (Half-Open)
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit moving to HALF_OPEN state...")
                else:
                    logger.warning(
                        f"Circuit is OPEN. Fast-failing request to {func.__name__}"
                    )
                    raise Exception(
                        f"Circuit Breaker: {func.__name__} is currently unavailable."
                    )

            try:
                result = await func(*args, **kwargs)
                self._handle_success()
                return result
            except Exception as e:
                self._handle_failure(e)
                raise e

        return wrapper

    def _handle_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Service recovered! Closing circuit.")
        self.state = CircuitState.CLOSED
        self.failures = 0

    def _handle_failure(self, e):
        self.failures += 1
        self.last_failure_time = time.time()
        logger.error(f"Failure {self.failures}/{self.failure_threshold}: {e}")

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.critical("Threshold reached. Circuit OPENED.")


# Reusable circuit breaker instances for different services
payment_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
sms_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=10)
