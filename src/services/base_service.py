from abc import ABC, abstractmethod
from fastapi import FastAPI

class BaseService(ABC):
    @abstractmethod
    async def cleanup(self):
        pass

    @abstractmethod
    def register_fastapi_routes(self, app: FastAPI):
        """
        Register fastapi routes related to the current service.
        Can be empty implementation if no routes to be exposed.
        """
        pass
