import pytest
from pipeline.stages.base import BaseStage


class DummyStage(BaseStage):
    name = "dummy"

    async def run(self, inputs):
        return inputs

    async def on_error(self, item, error):
        await super().on_error(item, error)


@pytest.mark.asyncio
async def test_base_stage_execute_success() -> None:
    stage = DummyStage()
    result = await stage.execute([1, 2, 3])
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_base_stage_on_error() -> None:
    stage = DummyStage()
    await stage.on_error("test_item", Exception("test_error"))


class FailingStage(BaseStage):
    name = "failing"

    async def run(self, inputs):
        raise RuntimeError("run failed")


@pytest.mark.asyncio
async def test_base_stage_execute_failure() -> None:
    stage = FailingStage()
    with pytest.raises(RuntimeError, match="run failed"):
        await stage.execute([1, 2, 3])
