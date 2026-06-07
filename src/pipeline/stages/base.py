from abc import ABC, abstractmethod
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

class BaseStage(ABC):
    name: str

    async def execute(self, inputs: Any) -> Any:
        logger.info("stage_started", stage=self.name)
        try:
            results = await self.run(inputs)
            logger.info("stage_completed", stage=self.name)
            return results
        except Exception as e:
            logger.error("stage_failed", stage=self.name, error=str(e))
            raise

    @abstractmethod
    async def run(self, inputs: Any) -> Any:
        pass

    async def on_error(self, item: Any, error: Exception) -> None:
        logger.error("item_processing_failed", stage=self.name, item=str(item), error=str(error))
