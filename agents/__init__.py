"""
FairGuard AI - Multi-Agent Governance System
Three specialized agents with inter-agent communication:
  - DetectionAgent: Discovers and classifies bias violations
  - ExplanationAgent: Translates findings into legal/business context
  - MitigationAgent: Generates prioritized remediation strategies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.fairness_engine import FairnessReport


@dataclass
class AgentResult:
    agent_name: str
    content: str
    confidence: float          # 0.0 – 1.0
    severity: str              # LOW / MEDIUM / HIGH / CRITICAL
    findings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Agent 1: Detection
# ──────────────────────────────────────────────────────────────────────────────

class DetectionAgent:
    """
    Scans fairness metrics for statistical violations.
    Emits structured violation codes (DP-001, DI-001, EO-001, INT-001).
    """

    VIOLATION_CODES = {
        "DP-001": "Demographic Parity Violation",
        "DI-001": "Disparate Impact — EEOC 4/5ths Rule Failure",
        "EO-001": "Equalized Odds Gap Exceeded",
        "CAL-001": "Calibration Imbalance Across Groups",
        "INT-001": "Intersectional Bias Detected",
        "SAMPLE-001": "Insufficient Sample Size Warning",
    }

    def analyze(self, report: "FairnessReport") -> AgentResult:
        violations = []
        findings = []
        dm = report.detailed_metrics

        # --- Demographic Parity ---
        dp = dm.get("demographic_parity", {})
        if not dp.get("is_satisfied", True):
            ratio = dp.get("parity_ratio", 0)
            violations.append("DP-001")
            findings.append(
                f"[DP-001] Demographic Parity violated: parity ratio = {ratio:.3f} "
                f"(threshold ≥ 0.80). Groups: {list(dp.get('selection_rates', {}).keys())}"
            )

        # --- Disparate Impact ---
        di = dm.get("disparate_impact", {})
        if not di.get("is_compliant", True):
            violations.append("DI-001")
            findings.append(
                f"[DI-001] Disparate Impact non-compliant: DI ratio = {di.get('di_ratio', 0):.3f}. "
                f"Legal status: {di.get('legal_status', 'Unknown')}"
            )

        # --- Equalized Odds ---
        eo = dm.get("equalized_odds", {})
        if not eo.get("is_satisfied", True):
            violations.append("EO-001")
            findings.append(
                f"[EO-001] Equalized Odds gap = {eo.get('avg_gap', 0):.3f} "
                f"(threshold ≤ 0.10). TPR gap: {eo.get('tpr_gap', 0):.3f}"
            )

        # --- Calibration ---
        cal = dm.get("calibration", {})
        if not cal.get("is_calibrated", True):
            violations.append("CAL-001")
            findings.append(
                f"[CAL-001] Calibration imbalance: Brier score difference = "
                f"{cal.get('brier_diff', 0):.4f} (threshold ≤ 0.10)"
            )

        # --- Intersectional ---
        inter = dm.get("intersectional", {})
        if inter and inter.get("max_disparity", 0) > 0.2:
            violations.append("INT-001")
            findings.append(
                f"[INT-001] Intersectional bias: max disparity = "
                f"{inter.get('max_disparity', 0):.3f} across "
                f"{inter.get('n_intersections', 0)} subgroups"
            )

        # --- Sample size warning ---
        if report.total_records < 500:
            violations.append("SAMPLE-001")
            findings.append(
                f"[SAMPLE-001] Small dataset ({report.total_records} records). "
                "Statistical conclusions may be unreliable. Recommend ≥ 500 records."
            )

        # Build summary
        if not violations:
            summary = (
                "✅ No significant bias violations detected across all fairness dimensions.\n"
                f"Overall fairness score: {report.overall_fairness_score:.1f}% — "
                f"Risk level: {report.risk_level}.\n"
                "System appears ready for deployment pending Bias Firewall clearance."
            )
            confidence = 0.92
            severity = "LOW"
        else:
            codes_str = ", ".join(violations)
            summary = (
                f"🚨 {len(violations)} violation(s) detected: [{codes_str}]\n\n"
                + "\n".join(f"• {f}" for f in findings)
                + f"\n\nOverall fairness score: {report.overall_fairness_score:.1f}% "
                f"({report.risk_level})"
            )
            confidence = 0.88 if len(violations) <= 2 else 0.95
            severity = "CRITICAL" if len(violations) >= 3 else "HIGH" if len(violations) == 2 else "MEDIUM"

        return AgentResult(
            agent_name="DetectionAgent",
            content=summary,
            confidence=confidence,
            severity=severity,
            findings=findings,
            metadata={"violation_codes": violations},
        )


# ──────────────────────────────────────────────────────────────────────────────
# Agent 2: Explanation
# ──────────────────────────────────────────────────────────────────────────────

class ExplanationAgent:
    """
    Receives detection findings and translates them into legal risk,
    business impact, and plain-language explanations for stakeholders.
    """

    LEGAL_FRAMEWORKS = {
        "DP-001": ["Title VII (Civil Rights Act)", "EEOC Uniform Guidelines"],
        "DI-001": ["EEOC 4/5ths Rule", "Title VII", "Griggs v. Duke Power precedent"],
        "EO-001": ["Equal Pay Act", "EEOC Guidelines"],
        "CAL-001": ["GDPR Article 22", "EU AI Act (High-Risk)"],
        "INT-001": ["Title VII", "GDPR Article 22", "EU AI Act"],
        "SAMPLE-001": ["Best practice — not a legal violation"],
    }

    def analyze(
        self, report: "FairnessReport", detection_result: AgentResult
    ) -> AgentResult:
        violation_codes = detection_result.metadata.get("violation_codes", [])
        dm = report.detailed_metrics
        dp = dm.get("demographic_parity", {})
        di = dm.get("disparate_impact", {})

        # Legal exposure
        applicable_laws = set()
        for code in violation_codes:
            applicable_laws.update(self.LEGAL_FRAMEWORKS.get(code, []))

        # Business impact estimate
        if "DI-001" in violation_codes or "DP-001" in violation_codes:
            legal_risk_pct = 65
            business_impact = "HIGH — Potential EEOC complaint, class-action lawsuit, and reputational damage."
        elif violation_codes:
            legal_risk_pct = 35
            business_impact = "MEDIUM — Regulatory scrutiny possible. Proactive remediation advised."
        else:
            legal_risk_pct = 8
            business_impact = "LOW — Continue standard monitoring practices."

        # Selection rate explanation
        rates = dp.get("selection_rates", {})
        rates_text = ""
        if rates:
            sorted_rates = sorted(rates.items(), key=lambda x: x[1], reverse=True)
            rates_text = "\nSelection rates by group:\n" + "\n".join(
                f"  • {g}: {r*100:.1f}%" for g, r in sorted_rates
            )

        # Build explanation
        if not violation_codes:
            content = (
                f"✅ Legal Risk Assessment: LOW ({legal_risk_pct}% estimated risk)\n\n"
                f"Business Impact: {business_impact}\n\n"
                "This hiring system demonstrates statistically fair outcomes across "
                f"the protected attribute '{report.protected_attribute}'. "
                f"No applicable legal frameworks are currently triggered.\n"
                f"{rates_text}\n\n"
                "Recommendation: Maintain current practices and establish quarterly re-audits."
            )
        else:
            laws_text = "\n".join(f"  ⚖️ {law}" for law in sorted(applicable_laws))
            content = (
                f"⚠️ Legal Risk Assessment: {detection_result.severity} ({legal_risk_pct}% estimated risk)\n\n"
                f"Business Impact: {business_impact}\n\n"
                f"Applicable Legal Frameworks:\n{laws_text}\n"
                f"{rates_text}\n\n"
                f"Plain-language explanation:\n"
                f"The hiring data for '{report.protected_attribute}' shows statistically "
                f"significant differences in selection rates between groups "
                f"(parity ratio: {dp.get('parity_ratio', 1.0):.2f}). "
                f"Under the EEOC's 4/5ths rule, this {'FAILS' if not di.get('is_compliant') else 'PASSES'} "
                f"the minimum compliance threshold. "
                f"{'This creates exposure to disparate impact claims under Title VII, even without discriminatory intent.' if not di.get('is_compliant') else 'However, some metrics warrant monitoring.'}\n\n"
                f"Cramér's V effect size: {dp.get('cramers_v', 0):.3f} "
                f"({'strong' if dp.get('cramers_v', 0) > 0.3 else 'moderate' if dp.get('cramers_v', 0) > 0.1 else 'weak'} association between protected attribute and outcome)"
            )

        confidence = 0.85 if violation_codes else 0.90

        return AgentResult(
            agent_name="ExplanationAgent",
            content=content,
            confidence=confidence,
            severity=detection_result.severity,
            findings=[f"Legal risk: {legal_risk_pct}%", f"Laws triggered: {len(applicable_laws)}"],
            metadata={
                "applicable_laws": list(applicable_laws),
                "legal_risk_pct": legal_risk_pct,
            },
        )


# ──────────────────────────────────────────────────────────────────────────────
# Agent 3: Mitigation
# ──────────────────────────────────────────────────────────────────────────────

class MitigationAgent:
    """
    Takes detection + explanation findings and produces prioritized,
    time-bound remediation strategies with implementation guidance.
    """

    def analyze(
        self,
        report: "FairnessReport",
        detection_result: AgentResult,
        explanation_result: AgentResult,
    ) -> AgentResult:
        violation_codes = detection_result.metadata.get("violation_codes", [])
        score = report.overall_fairness_score
        dm = report.detailed_metrics

        strategies = []

        # Pre-processing strategies
        if "DP-001" in violation_codes or "DI-001" in violation_codes:
            strategies.append(
                "PRE-PROCESSING [Week 1–2]\n"
                "  → Reweigh training samples: assign higher weights to underrepresented group outcomes\n"
                "  → Remove or transform proxy features (zip code, graduation year, school name)\n"
                "  → Augment training data for minority groups via synthetic generation (SMOTE)"
            )

        if "EO-001" in violation_codes:
            strategies.append(
                "IN-PROCESSING [Week 2–4]\n"
                "  → Apply fairness constraints during model training (Fairlearn ConstrainedClassifier)\n"
                "  → Use adversarial debiasing: add fairness loss term to optimization objective\n"
                "  → Consider separate threshold optimization per protected group"
            )

        if "CAL-001" in violation_codes:
            strategies.append(
                "POST-PROCESSING [Week 1–2]\n"
                "  → Apply Platt scaling or isotonic regression per group\n"
                "  → Equalize calibration curves across demographic groups\n"
                "  → Implement reject-option classification for borderline cases"
            )

        if "INT-001" in violation_codes:
            inter = dm.get("intersectional", {})
            strategies.append(
                f"INTERSECTIONAL REMEDIATION [Week 3–6]\n"
                f"  → {inter.get('n_intersections', 0)} subgroups analyzed — target the bottom 3 by selection rate\n"
                "  → Apply subgroup-specific fairness constraints\n"
                "  → Ensure minimum sample sizes (≥100) for each intersectional subgroup"
            )

        # Governance strategies (always recommended)
        strategies.append(
            "GOVERNANCE [Ongoing]\n"
            "  → Integrate FairGuard Bias Firewall into CI/CD pipeline\n"
            "  → Establish quarterly third-party fairness audits\n"
            "  → Create diverse oversight committee for algorithmic decisions\n"
            "  → Document all interventions for OFCCP/EEOC compliance records"
        )

        if not strategies:
            content = (
                "✅ No remediation required at this time.\n\n"
                "Recommended preventive measures:\n"
                "• Schedule quarterly re-audits as data distribution shifts\n"
                "• Monitor fairness metrics post-deployment via real-time dashboard\n"
                "• Maintain audit trail for all hiring decisions\n"
                "• Train HR teams on algorithmic bias awareness"
            )
            confidence = 0.90
        else:
            target_score = min(95, score + 20)
            content = (
                f"Remediation Plan — Target: {score:.1f}% → {target_score:.1f}% fairness score\n\n"
                + "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(strategies))
                + f"\n\nEstimated timeline to compliance: "
                + ("2–4 weeks" if score >= 70 else "4–8 weeks" if score >= 55 else "8–12 weeks")
                + "\nEstimated legal risk reduction: "
                + f"{explanation_result.metadata.get('legal_risk_pct', 50)}% → ~15% after full remediation"
            )
            confidence = 0.82

        severity = detection_result.severity

        return AgentResult(
            agent_name="MitigationAgent",
            content=content,
            confidence=confidence,
            severity=severity,
            findings=[f"{len(strategies)} strategy groups recommended"],
            metadata={"strategy_count": len(strategies)},
        )


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Coordinates the three agents and produces a unified consensus.
    Agents communicate via shared AgentResult objects.
    """

    def __init__(self):
        self.detection_agent = DetectionAgent()
        self.explanation_agent = ExplanationAgent()
        self.mitigation_agent = MitigationAgent()

    def run_analysis(self, report: "FairnessReport") -> Dict[str, Any]:
        # Sequential pipeline with inter-agent communication
        detection = self.detection_agent.analyze(report)
        explanation = self.explanation_agent.analyze(report, detection)
        mitigation = self.mitigation_agent.analyze(report, detection, explanation)

        consensus = self._build_consensus(report, detection, explanation, mitigation)

        return {
            "detection": detection,
            "explanation": explanation,
            "mitigation": mitigation,
            "consensus": consensus,
        }

    def _build_consensus(
        self,
        report: "FairnessReport",
        detection: AgentResult,
        explanation: AgentResult,
        mitigation: AgentResult,
    ) -> str:
        avg_confidence = (
            detection.confidence + explanation.confidence + mitigation.confidence
        ) / 3

        violation_codes = detection.metadata.get("violation_codes", [])
        legal_risk = explanation.metadata.get("legal_risk_pct", 0)
        strategy_count = mitigation.metadata.get("strategy_count", 0)

        if not violation_codes:
            return (
                f"🤝 Agent Consensus [Confidence: {avg_confidence:.0%}]: "
                f"All three agents agree — this system demonstrates adequate fairness "
                f"(score: {report.overall_fairness_score:.1f}%). "
                "Approved for deployment with standard monitoring."
            )

        return (
            f"🤝 Agent Consensus [Confidence: {avg_confidence:.0%}]: "
            f"{len(violation_codes)} violation(s) confirmed across Detection, Explanation, and Mitigation agents. "
            f"Estimated legal risk: {legal_risk}%. "
            f"{strategy_count} remediation strategy group(s) recommended. "
            f"Bias Firewall status: {report.bias_firewall_status}. "
            f"{'Deployment BLOCKED until remediation is complete.' if report.overall_fairness_score < 60 else 'Remediation advised before production deployment.'}"
        )
