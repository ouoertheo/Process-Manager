from pydantic import BaseModel, Field, PlainSerializer
from typing import Annotated
from pathlib import Path
from typing import Literal
from collections import deque


class ProcessDefinition(BaseModel):
    path: Annotated[Path, PlainSerializer(lambda p: str(p))]
    command: list[str]


class ProcessDefinitionList(BaseModel):
    definitions: dict[str, ProcessDefinition]


class Process(BaseModel):
    name: str
    definition: ProcessDefinition
    pid: int = Field(default=None, exclude=True)
    logs: Annotated[
        deque[str],
        Field(default_factory=lambda: deque(maxlen=1000)),
        PlainSerializer(lambda l: list(l)),
    ]
    status: Literal["running", "stopped"] = "stopped"
    new_log_count: int = 0
