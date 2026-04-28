"""
FairGuard AI - Firebase Integration
Stores audit history in Cloud Firestore for persistent, cross-session storage.
Degrades gracefully when Firebase is not configured.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class FirebaseManager:
    """
    Manages Firestore audit storage.
    Falls back silently if Firebase is not configured.
    """

    def __init__(self):
        self.is_configured = False
        self.db = None
        self._init_firebase()

    def _init_firebase(self):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            # Check if already initialized
            if not firebase_admin._apps:
                # Try environment variable (Streamlit secrets)
                firebase_config = os.getenv("FIREBASE_CONFIG")
                if firebase_config:
                    import json
                    cred_dict = json.loads(firebase_config)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                else:
                    # Try local service account file
                    cred_path = os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "firebase_credentials.json"
                    )
                    cred_path = os.path.abspath(cred_path)

                    if os.path.exists(cred_path):
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred)
                    else:
                        return
                

            self.db = firestore.client()
            self.is_configured = True

            print("Firebase configured:", self.is_configured)

        except Exception as e:
            print("Firebase init error:", e)
            self.is_configured = False
    def save_audit(self, report, firewall_result=None) -> Optional[str]:
        """Save a fairness audit to Firestore. Returns document ID or None."""
        if not self.is_configured:
            return None

        try:
            from firebase_admin import firestore as fs

            audit_data = {
                "timestamp": datetime.utcnow(),
                "protected_attribute": report.protected_attribute,
                "outcome_column": report.outcome_column,
                "total_records": report.total_records,
                "n_groups": report.n_groups,
                "scores": {
                    "overall": round(report.overall_fairness_score, 2),
                    "demographic_parity": round(report.demographic_parity, 2),
                    "equalized_odds": round(report.equalized_odds, 2),
                    "disparate_impact": round(report.disparate_impact, 2),
                    "calibration": round(report.calibration_score, 2),
                },
                "risk_level": report.risk_level,
                "bias_firewall_status": report.bias_firewall_status,
                "recommendations": report.recommendations,
            }

            if firewall_result:
                audit_data["firewall"] = {
                    "decision": firewall_result.decision.value,
                    "decision_label": firewall_result.decision_label,
                }

            # Add to Firestore
            doc_ref = self.db.collection("fairguard_audits").add(audit_data)
            return doc_ref[1].id

        except Exception as e:
            print(f"Firebase save error: {e}")
            return None

    def get_audit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent audits from Firestore."""
        if not self.is_configured:
            return []

        try:
            docs = (
                self.db.collection("fairguard_audits")
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            history = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                # Convert Firestore timestamp
                if "timestamp" in data and hasattr(data["timestamp"], "isoformat"):
                    data["timestamp"] = data["timestamp"].isoformat()
                history.append(data)

            return history

        except Exception as e:
            print(f"Firebase fetch error: {e}")
            return []

    def get_trend_data(self) -> Dict[str, Any]:
        """Get fairness score trends over time."""
        history = self.get_audit_history(limit=20)
        if not history:
            return {}

        scores = [h.get("scores", {}).get("overall", 0) for h in history]
        timestamps = [h.get("timestamp", "") for h in history]
        firewall_statuses = [h.get("bias_firewall_status", "") for h in history]

        return {
            "scores": scores,
            "timestamps": timestamps,
            "firewall_statuses": firewall_statuses,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "total_audits": len(history),
            "pass_rate": round(
                sum(1 for s in firewall_statuses if s == "PASS") / len(firewall_statuses) * 100, 1
            ) if firewall_statuses else 0,
        }
