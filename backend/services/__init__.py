"""Pipeline orchestration that wires components together."""

from backend.services.factory import build_pipeline
from backend.services.pipeline import KnowledgePipeline, PipelineResult

__all__ = ["KnowledgePipeline", "PipelineResult", "build_pipeline"]
