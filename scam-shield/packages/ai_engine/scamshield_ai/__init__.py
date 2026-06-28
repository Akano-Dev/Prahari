"""ScamShield AI — hybrid, explainable scam-detection engine (defensive).

Public API::

    from scamshield_ai import AnalysisPipeline
    pipe = AnalysisPipeline()                 # no models/keys needed
    state = pipe.new_state("call-123")
    assessment = pipe.analyze_utterance("This is CBI, you are under digital arrest", state)
    print(assessment.risk_score, assessment.band)
"""
from .pipeline import DECISION_THRESHOLD, AnalysisPipeline, default_stages
from .schemas import (
    BehaviourAnalysis,
    Entity,
    OfficerClaim,
    RiskAssessment,
    RiskBand,
    ScamTypeScore,
    Signal,
    band_for_score,
)

__version__ = "0.1.0"

__all__ = [
    "AnalysisPipeline", "default_stages", "DECISION_THRESHOLD",
    "RiskAssessment", "RiskBand", "Signal", "Entity", "BehaviourAnalysis",
    "ScamTypeScore", "OfficerClaim", "band_for_score", "__version__",
]
