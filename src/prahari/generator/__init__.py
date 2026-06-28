"""Synthetic labelled-example generator (defensive: training augmentation + test fixtures).

See :mod:`prahari.generator.templates` for the mission note. The synthetic
data exists only to train and test the defensive classifier.
"""
from prahari.generator.templates import generate

__all__ = ["generate"]
