"""
FairGuard AI - Gemini Advisor
Google Gemini 1.5 Flash integration for intelligent fairness recommendations.
Falls back to template-based recommendations when API key is unavailable.
"""

import os
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.fairness_engine import FairnessReport


class GeminiAdvisor:
    """
    Wraps Google Gemini 1.5 Flash to provide context-aware fairness
    recommendations. Degrades gracefully without an API key.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.is_configured = False
        self._model = None

        if self.api_key:
            self._init_gemini()

    def _init_gemini(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel("gemini-1.5-flash")
            self.is_configured = True
        except Exception:
            self.is_configured = False

    def generate_fairness_recommendations(
        self,
        report: "FairnessReport",
        user_question: Optional[str] = None,
    ) -> dict:
        if self.is_configured and self._model:
            return self._call_gemini(report, user_question)
        return self._template_response(report, user_question)

    # ------------------------------------------------------------------
    # Gemini call
    # ------------------------------------------------------------------
    def _call_gemini(self, report, user_question) -> dict:
        try:
            context = self._build_context(report)

            if user_question:
                prompt = f"""You are FairGuard AI, an expert in algorithmic fairness, employment law, and AI ethics.

{context}

User question: {user_question}

Answer specifically and concisely. Reference the actual metrics above."""
            else:
                prompt = f"""You are FairGuard AI, an expert in algorithmic fairness, employment law, and AI ethics.

{context}

Provide a structured fairness audit report with these exact sections:
## Executive Summary
(2-3 sentences on overall fairness status)

## Critical Issues
(List the most urgent fairness violations found in the data)

## Immediate Actions Required
(Prioritized, time-bound remediation steps)

## Legal Compliance Checklist
(EEOC 4/5ths rule, Title VII, GDPR Article 22, EU AI Act status)

## Long-Term Recommendations
(Strategic fairness improvements)

Be specific, cite the actual metric values, and be direct about legal risks."""

            response = self._model.generate_content(prompt)
            return {
                "response": response.text,
                "source": "Google Gemini 1.5 Flash",
            }
        except Exception as e:
            return {
                "response": f"Gemini error: {str(e)}. Falling back to template.",
                "source": "Error fallback",
            }

    def _build_context(self, report) -> str:
        dm = report.detailed_metrics
        dp = dm.get("demographic_parity", {})
        di = dm.get("disparate_impact", {})
        eo = dm.get("equalized_odds", {})
        cal = dm.get("calibration", {})

        return f"""
FAIRGUARD AI AUDIT REPORT
==========================
Protected Attribute: {report.protected_attribute}
Outcome Column: {report.outcome_column}
Total Records: {report.total_records}
Number of Groups: {report.n_groups}

FAIRNESS SCORES (0-100, higher = fairer):
- Overall Fairness Score: {report.overall_fairness_score:.1f}%
- Demographic Parity: {report.demographic_parity:.1f}% (satisfied: {dp.get('is_satisfied', 'N/A')})
- Equalized Odds: {report.equalized_odds:.1f}% (satisfied: {eo.get('is_satisfied', 'N/A')})
- Disparate Impact: {report.disparate_impact:.1f}% (EEOC compliant: {di.get('is_compliant', 'N/A')})
- Calibration: {report.calibration_score:.1f}%

RISK LEVEL: {report.risk_level}
BIAS FIREWALL: {report.bias_firewall_status}

KEY METRICS:
- Demographic Parity Ratio: {dp.get('parity_ratio', 'N/A')}
- Selection Rates by Group: {dp.get('selection_rates', {})}
- Disparate Impact Ratio: {di.get('di_ratio', 'N/A')}
- Legal Status: {di.get('legal_status', 'N/A')}
- Equalized Odds Gap: {eo.get('avg_gap', 'N/A')}
- Cramér's V Effect Size: {dp.get('cramers_v', 'N/A')}
- Chi-square p-value: {dp.get('p_value', 'N/A')}

SYSTEM RECOMMENDATIONS:
{chr(10).join(report.recommendations)}
"""

    # ------------------------------------------------------------------
    # Template fallback
    # ------------------------------------------------------------------
    def _template_response(self, report, user_question) -> dict:
        score = report.overall_fairness_score
        risk = report.risk_level
        dm = report.detailed_metrics
        dp = dm.get("demographic_parity", {})
        di = dm.get("disparate_impact", {})

        if user_question:
            response = self._answer_question(user_question, report)
        else:
            if score >= 85:
                status_text = "✅ Your hiring system demonstrates strong fairness characteristics."
                urgency = "Continue monitoring post-deployment."
            elif score >= 70:
                status_text = "⚠️ Moderate fairness concerns detected. Action recommended before deployment."
                urgency = "Address flagged metrics within 30 days."
            else:
                status_text = "🚨 Significant bias detected. Deployment should be blocked pending remediation."
                urgency = "Immediate action required. Do not deploy."

            response = f"""## Executive Summary
{status_text} Overall fairness score: **{score:.1f}%** ({risk}).

## Critical Issues
- **Demographic Parity**: {"✅ Satisfied" if dp.get('is_satisfied') else f"❌ Violated — ratio {dp.get('parity_ratio', 0):.2f} (threshold: 0.80)"}
- **Disparate Impact**: {"✅ Compliant" if di.get('is_compliant') else f"❌ {di.get('legal_status', 'Non-compliant')}"}
- **Equalized Odds**: {"✅ Within threshold" if dm.get('equalized_odds', {}).get('is_satisfied') else "❌ Gap exceeds 10% threshold"}
- **Calibration**: {"✅ Balanced" if dm.get('calibration', {}).get('is_calibrated') else "⚠️ Imbalanced across groups"}

## Immediate Actions Required
1. **Audit training data** for historical bias in labeling (within 1 week)
2. **Apply re-weighting** to underrepresented groups (within 2 weeks)
3. **Remove proxy variables** correlated with protected attributes (within 2 weeks)
4. **Legal review** of current selection process (within 1 month)

## Legal Compliance Checklist
- EEOC 4/5ths Rule: {"✅ Compliant" if di.get('is_compliant') else "❌ Non-compliant — Title VII risk"}
- Title VII (Civil Rights Act): {"✅ Low risk" if score >= 80 else "⚠️ Elevated risk — disparate impact claims possible"}
- GDPR Article 22: {"✅ Likely compliant" if score >= 75 else "⚠️ Review automated decision-making disclosures"}
- EU AI Act (High-Risk AI): ⚠️ Hiring systems are classified as high-risk — mandatory bias assessment required

## Long-Term Recommendations
1. Implement continuous fairness monitoring post-deployment
2. Establish quarterly bias audits with third-party review
3. Create diverse hiring committee to oversee algorithmic decisions
4. Document all fairness interventions for regulatory compliance
5. Consider fairness-aware model retraining every 6 months

---
*{urgency}*
*Note: Add your Google API key in the sidebar for Gemini-powered personalized recommendations.*"""

        return {
            "response": response,
            "source": "FairGuard Template Engine (add Google API key for Gemini)",
        }

    def _answer_question(self, question: str, report) -> str:
        q = question.lower()
        score = report.overall_fairness_score
        dm = report.detailed_metrics
        di = dm.get("disparate_impact", {})

        if any(w in q for w in ["legal", "lawsuit", "risk", "sue", "eeoc", "title vii"]):
            compliant = di.get("is_compliant", True)
            return f"""## Legal Risk Assessment

**Current Status**: {"Low legal risk" if compliant else "⚠️ Elevated legal risk"}

**EEOC Exposure**: {"Minimal — disparate impact ratio is within the 4/5ths threshold." if compliant else f"Significant — disparate impact ratio of {di.get('di_ratio', 0):.2f} violates the EEOC 4/5ths rule. Average settlement: $125K–$500K per case."}

**Title VII (Civil Rights Act)**: Hiring algorithms producing disparate outcomes for protected classes are actionable under Title VII even without discriminatory intent (disparate impact doctrine, *Griggs v. Duke Power*).

**GDPR Article 22**: Automated decision-making affecting individuals must be explainable and challengeable. Ensure you have human oversight mechanisms in place.

**Recommended Actions**:
1. Engage employment law counsel immediately if score < 70
2. Document all fairness testing performed
3. Implement human-in-the-loop review for borderline decisions
4. Prepare adverse impact analysis report for OFCCP compliance"""

        if any(w in q for w in ["fix", "mitigat", "remediat", "improve", "how"]):
            return f"""## Remediation Strategies (Prioritized)

**Immediate (Week 1–2)**:
- Audit training data labels for historical bias
- Remove or transform features that proxy protected attributes (zip code, graduation year)
- Apply class reweighting to balance underrepresented groups

**Short-term (Month 1)**:
- Re-train model with fairness constraints (e.g., Fairlearn, AIF360)
- Apply post-processing: threshold adjustment per group to equalize outcomes
- Implement adversarial debiasing if using neural networks

**Long-term (Quarter 1)**:
- Establish a fairness review board with diverse representation
- Integrate FairGuard into CI/CD pipeline — block deployments that fail Bias Firewall
- Conduct third-party algorithmic audit annually

**Current score**: {score:.1f}% → Target: 85%+"""

        return f"""## Response to Your Question

Based on the FairGuard audit (overall score: **{score:.1f}%**, risk: **{report.risk_level}**):

Your question touches on an important aspect of algorithmic fairness. The audit data shows:
- Demographic Parity: {report.demographic_parity:.1f}%
- Disparate Impact: {report.disparate_impact:.1f}% ({di.get('legal_status', 'See details')})
- Equalized Odds: {report.equalized_odds:.1f}%

For a more detailed answer specific to your question, please add your Google Gemini API key in the sidebar. The AI advisor can provide context-aware responses based on your exact audit data.

*Add Google API key → Sidebar → API Configuration*"""
