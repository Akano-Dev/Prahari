// Mirrors scamshield_ai.schemas — the shared explainable contract.
export interface EvidenceSpan { text: string; utterance_index: number; start?: number | null; end?: number | null; }
export interface Signal { id: string; label: string; description: string; weight: number; behaviour: string; evidence: EvidenceSpan[]; }
export interface Entity { type: string; value: string; normalized?: string | null; utterance_index: number; }
export interface BehaviourAnalysis {
  urgency: number; fear: number; authority_impersonation: number; money_request: number;
  credential_request: number; secrecy: number; threat: number; emotional_manipulation: number;
  video_call_pressure: number; confidence: number;
}
export interface ScamTypeScore { category: string; label: string; score: number; }
export interface OfficerClaim {
  claimed: boolean; name?: string | null; department?: string | null; designation?: string | null;
  location?: string | null; consistency: string; notes: string[];
}
export interface TimelineEvent { index: number; kind: string; label: string; detail?: string | null; risk_after?: number | null; }
export interface RiskAssessment {
  call_id: string; risk_score: number; band: string; is_scam: boolean; confidence: number;
  languages: string[]; top_scam_type?: ScamTypeScore | null; scam_types: ScamTypeScore[];
  behaviour: BehaviourAnalysis; signals: Signal[]; entities: Entity[]; officer_claim?: OfficerClaim | null;
  reasoning: string; recommendation: string; timeline: TimelineEvent[]; n_utterances: number;
}
export interface Incident { id: string; call_id: string; risk_score: number; scam_type?: string | null; caller_number: string; created_at: string; }
export interface Stats { total_calls: number; total_incidents: number; scam_calls: number; avg_peak_risk: number; by_scam_type: Record<string, number>; }
export interface User { id: string; email: string; display_name: string; avatar?: string | null; created_at?: string | null; }
