"""Compatibility facade; business rules live in model."""
from model.manager import PIMManager
from model.factory import PIRFactory

__all__ = ["PIMManager", "PIRFactory"]
