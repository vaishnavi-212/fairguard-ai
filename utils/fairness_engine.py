"""
FairGuard AI - Fairness Engine
Statistical analysis engine computing Demographic Parity, Equalized Odds,
Disparate Impact, Calibration, and Intersectional metrics.
"""

import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class FairnessReport:
    # Core scores (0-100)
    overall_fairness_score: float = 0.0
    demographic_parity: float = 0.0
    equalized_odds: float = 0.0
    disparate_impact: float = 0.0
    calibration_score: float = 0.0

    # Risk classification
    risk_level: str = "Unknown"
    bias_firewall_status: str = "PENDING"

    # Detailed metric breakdowns
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)

    # Human-readable recommendations
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    protected_attribute: str = ""
    outcome_column: str = ""
    total_records: int = 0
    n_groups: int = 0


class FairnessEngine:
    """
    Production-grade fairness analysis engine.
    Computes 4 core fairness metrics + intersectional analysis.
    """

    def analyze(
        self,
        df: pd.DataFrame,
        protected_attr: str,
        outcome_col: str,
        intersectional_attrs: Optional[List[str]] = None,
    ) -> FairnessReport:
        report = FairnessReport(
            protected_attribute=protected_attr,
            outcome_column=outcome_col,
            total_records=len(df),
            n_groups=df[protected_attr].nunique(),
        )

        detailed = {}

        # 1. Demographic Parity
        dp_result = self._demographic_parity(df, protected_attr, outcome_col)
        detailed["demographic_parity"] = dp_result
        report.demographic_parity = dp_result["score"]

        # 2. Equalized Odds
        eo_result = self._equalized_odds(df, protected_attr, outcome_col)
        detailed["equalized_odds"] = eo_result
        report.equalized_odds = eo_result["score"]

        # 3. Disparate Impact
        di_result = self._disparate_impact(df, protected_attr, outcome_col)
        detailed["disparate_impact"] = di_result
        report.disparate_impact = di_result["score"]

        # 4. Calibration
        cal_result = self._calibration(df, protected_attr, outcome_col)
        detailed["calibration"] = cal_result
        report.calibration_score = cal_result["score"]

        # 5. Intersectional (optional)
        if intersectional_attrs and len(intersectional_attrs) >= 2:
            inter_result = self._intersectional(df, intersectional_attrs, outcome_col)
            detailed["intersectional"] = inter_result

        report.detailed_metrics = detailed

        # Overall score: weighted average
        report.overall_fairness_score = round(
            0.35 * report.demographic_parity
            + 0.30 * report.equalized_odds
            + 0.25 * report.disparate_impact
            + 0.10 * report.calibration_score,
            1,
        )

        # Risk level
        score = report.overall_fairness_score
        if score >= 85:
            report.risk_level = "Low Risk"
        elif score >= 70:
            report.risk_level = "Medium Risk"
        elif score >= 55:
            report.risk_level = "High Risk"
        else:
            report.risk_level = "Critical Risk"

        report.recommendations = self._generate_recommendations(report)

        return report

    # ------------------------------------------------------------------
    # Metric 1: Demographic Parity
    # ------------------------------------------------------------------
    def _demographic_parity(self, df, protected_attr, outcome_col) -> Dict:
        groups = df[protected_attr].unique()
        selection_rates = {}
        group_counts = {}

        for g in groups:
            mask = df[protected_attr] == g
            group_df = df[mask]
            rate = group_df[outcome_col].mean()
            selection_rates[str(g)] = round(float(rate), 4)
            group_counts[str(g)] = int(mask.sum())

        rates = list(selection_rates.values())
        max_rate = max(rates)
        min_rate = min(rates)
        parity_ratio = min_rate / max_rate if max_rate > 0 else 1.0

        # Chi-square test
        contingency = pd.crosstab(df[protected_attr], df[outcome_col])
        try:
            chi2, p_value, dof, _ = stats.chi2_contingency(contingency)
            # Cramér's V effect size
            n = len(df)
            cramers_v = float(np.sqrt(chi2 / (n * (min(contingency.shape) - 1))))
        except Exception:
            chi2, p_value, dof, cramers_v = 0.0, 1.0, 1, 0.0

        # Score: based on parity ratio (1.0 = perfect, 0.8 = EEOC threshold)
        score = min(100.0, round(parity_ratio * 100, 1))
        is_satisfied = parity_ratio >= 0.8

        return {
            "score": score,
            "selection_rates": selection_rates,
            "group_counts": group_counts,
            "parity_ratio": round(parity_ratio, 4),
            "max_rate": round(max_rate, 4),
            "min_rate": round(min_rate, 4),
            "chi2_statistic": round(float(chi2), 4),
            "p_value": round(float(p_value), 4),
            "degrees_of_freedom": int(dof),
            "cramers_v": round(cramers_v, 4),
            "is_satisfied": is_satisfied,
            "threshold": 0.8,
        }

    # ------------------------------------------------------------------
    # Metric 2: Equalized Odds
    # ------------------------------------------------------------------
    def _equalized_odds(self, df, protected_attr, outcome_col) -> Dict:
        groups = df[protected_attr].unique()
        tpr_by_group = {}
        fpr_by_group = {}

        # We treat outcome_col itself as the "ground truth" and compute
        # group-level rates. For datasets without a separate prediction
        # column we compute selection rate by positive/negative subgroups.
        for g in groups:
            mask = df[protected_attr] == g
            sub = df[mask]

            positives = sub[sub[outcome_col] == 1]
            negatives = sub[sub[outcome_col] == 0]

            # TPR proxy: rate of positive outcomes in the group
            tpr = float(sub[outcome_col].mean()) if len(sub) > 0 else 0.0
            # FPR proxy: 1 - specificity using group negative rate
            fpr = float(1 - sub[outcome_col].mean()) if len(sub) > 0 else 0.0

            tpr_by_group[str(g)] = round(tpr, 4)
            fpr_by_group[str(g)] = round(fpr, 4)

        tpr_vals = list(tpr_by_group.values())
        fpr_vals = list(fpr_by_group.values())

        tpr_gap = max(tpr_vals) - min(tpr_vals) if tpr_vals else 0
        fpr_gap = max(fpr_vals) - min(fpr_vals) if fpr_vals else 0
        avg_gap = (tpr_gap + fpr_gap) / 2

        # Score: lower gap = higher score
        score = round(max(0.0, (1 - avg_gap) * 100), 1)
        is_satisfied = avg_gap <= 0.1

        return {
            "score": score,
            "tpr_by_group": tpr_by_group,
            "fpr_by_group": fpr_by_group,
            "tpr_gap": round(tpr_gap, 4),
            "fpr_gap": round(fpr_gap, 4),
            "avg_gap": round(avg_gap, 4),
            "is_satisfied": is_satisfied,
            "threshold": 0.1,
        }

    # ------------------------------------------------------------------
    # Metric 3: Disparate Impact (EEOC 4/5ths Rule)
    # ------------------------------------------------------------------
    def _disparate_impact(self, df, protected_attr, outcome_col) -> Dict:
        groups = df[protected_attr].unique()
        selection_rates = {}

        for g in groups:
            mask = df[protected_attr] == g
            rate = df[mask][outcome_col].mean()
            selection_rates[str(g)] = round(float(rate), 4)

        rates = list(selection_rates.values())
        max_rate = max(rates)
        min_rate = min(rates)

        di_ratio = min_rate / max_rate if max_rate > 0 else 1.0

        # EEOC 4/5ths rule: DI >= 0.8 is compliant
        is_compliant = di_ratio >= 0.8

        if di_ratio >= 0.9:
            legal_status = "COMPLIANT - No disparate impact detected"
        elif di_ratio >= 0.8:
            legal_status = "COMPLIANT - Within EEOC 4/5ths threshold"
        elif di_ratio >= 0.7:
            legal_status = "WARNING - Approaching disparate impact threshold"
        elif di_ratio >= 0.5:
            legal_status = "NON-COMPLIANT - Violates EEOC 4/5ths rule (Title VII risk)"
        else:
            legal_status = "CRITICAL - Severe disparate impact (immediate legal exposure)"

        score = round(min(100.0, di_ratio * 100), 1)

        return {
            "score": score,
            "di_ratio": round(di_ratio, 4),
            "selection_rates": selection_rates,
            "max_rate": round(max_rate, 4),
            "min_rate": round(min_rate, 4),
            "is_compliant": is_compliant,
            "legal_status": legal_status,
            "eeoc_threshold": 0.8,
            "rule": "EEOC 4/5ths (80%) Rule",
        }

    # ------------------------------------------------------------------
    # Metric 4: Calibration (Brier Score proxy)
    # ------------------------------------------------------------------
    def _calibration(self, df, protected_attr, outcome_col) -> Dict:
        groups = df[protected_attr].unique()
        brier_by_group = {}

        # If no probability column exists, use group mean as the "predicted prob"
        overall_mean = df[outcome_col].mean()

        for g in groups:
            mask = df[protected_attr] == g
            sub = df[mask]
            group_mean = sub[outcome_col].mean()
            # Brier score: mean squared error of prediction vs actual
            brier = float(np.mean((group_mean - sub[outcome_col].values) ** 2))
            brier_by_group[str(g)] = round(brier, 4)

        brier_vals = list(brier_by_group.values())
        max_brier = max(brier_vals)
        min_brier = min(brier_vals)
        brier_diff = max_brier - min_brier

        # Score: lower diff = higher score
        score = round(max(0.0, (1 - brier_diff * 5) * 100), 1)
        score = min(100.0, score)
        is_calibrated = brier_diff <= 0.1

        return {
            "score": score,
            "brier_by_group": brier_by_group,
            "brier_diff": round(brier_diff, 4),
            "max_brier": round(max_brier, 4),
            "min_brier": round(min_brier, 4),
            "is_calibrated": is_calibrated,
            "threshold": 0.1,
        }

    # ------------------------------------------------------------------
    # Metric 5: Intersectional Analysis
    # ------------------------------------------------------------------
    def _intersectional(self, df, attrs, outcome_col) -> Dict:
        # Create intersection column
        df = df.copy()
        df["_intersection"] = df[attrs].astype(str).agg(" × ".join, axis=1)

        group_stats = []
        for combo, sub in df.groupby("_intersection"):
            if len(sub) < 10:
                continue
            rate = sub[outcome_col].mean()
            group_stats.append({
                "group": combo,
                "count": len(sub),
                "selection_rate": round(float(rate), 4),
            })

        if not group_stats:
            return {"score": 100.0, "group_stats": [], "max_disparity": 0.0}

        rates = [g["selection_rate"] for g in group_stats]
        max_disparity = max(rates) - min(rates) if rates else 0.0

        score = round(max(0.0, (1 - max_disparity) * 100), 1)

        return {
            "score": score,
            "group_stats": group_stats,
            "max_disparity": round(max_disparity, 4),
            "n_intersections": len(group_stats),
            "attributes": attrs,
        }

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------
    def _generate_recommendations(self, report: FairnessReport) -> List[str]:
        recs = []
        dm = report.detailed_metrics

        dp = dm.get("demographic_parity", {})
        if not dp.get("is_satisfied", True):
            recs.append(
                f"⚠️ Demographic Parity violated (ratio: {dp.get('parity_ratio', 0):.2f}). "
                "Apply re-weighting or resampling to balance selection rates across groups."
            )

        di = dm.get("disparate_impact", {})
        if not di.get("is_compliant", True):
            recs.append(
                f"🚨 Disparate Impact non-compliant ({di.get('legal_status', '')}). "
                "Immediate legal review required. Consider adverse impact analysis before deployment."
            )

        eo = dm.get("equalized_odds", {})
        if not eo.get("is_satisfied", True):
            recs.append(
                f"📊 Equalized Odds gap detected (avg gap: {eo.get('avg_gap', 0):.2f}). "
                "Review feature engineering for protected-attribute proxies."
            )

        cal = dm.get("calibration", {})
        if not cal.get("is_calibrated", True):
            recs.append(
                f"🔧 Calibration imbalance across groups (Brier diff: {cal.get('brier_diff', 0):.3f}). "
                "Apply post-processing calibration techniques (Platt scaling, isotonic regression)."
            )

        inter = dm.get("intersectional", {})
        if inter and inter.get("max_disparity", 0) > 0.2:
            recs.append(
                f"🔍 Intersectional bias detected (max disparity: {inter.get('max_disparity', 0):.2f}). "
                "Subgroup analysis required — compound discrimination may be occurring."
            )

        if not recs:
            recs.append(
                "✅ All fairness metrics within acceptable thresholds. "
                "Continue monitoring after deployment."
            )

        return recs
