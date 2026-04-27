from dataclasses import dataclass, field
from enum import Enum
from typing import List


class FirewallDecision(Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    BLOCK = "BLOCK"


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str


@dataclass
class FirewallResult:
    decision: FirewallDecision
    decision_label: str
    can_deploy: bool

    checks_passed: int
    checks_failed: int
    total_checks: int

    failed_checks: list = field(default_factory=list)
    deployment_conditions: List[str] = field(default_factory=list)


class BiasFirewall:

    def evaluate(self, report):

        checks = []

        # Demographic parity
        dp = report.detailed_metrics.get("demographic_parity", {})
        checks.append(
            CheckResult(
                "Demographic Parity",
                dp.get("parity_ratio",1) >= 0.8,
                f"Parity ratio = {dp.get('parity_ratio',1)}"
            )
        )

        # Disparate impact
        di = report.detailed_metrics.get("disparate_impact",{})
        checks.append(
            CheckResult(
                "Disparate Impact",
                di.get("is_compliant",True),
                di.get("legal_status","Compliant")
            )
        )

        # Equalized odds
        eo=report.detailed_metrics.get("equalized_odds",{})
        checks.append(
            CheckResult(
                "Equalized Odds",
                eo.get("avg_gap",0)<=0.1,
                f"Gap={eo.get('avg_gap',0)}"
            )
        )

        passed=sum(c.passed for c in checks)
        failed=len(checks)-passed

        failed_checks=[
            {
                "name":c.name,
                "message":c.message
            }
            for c in checks if not c.passed
        ]

        if failed==0:
            decision=FirewallDecision.PASS
            label="PASS"
            can_deploy=True

        elif failed==1:
            decision=FirewallDecision.PASS_WITH_WARNINGS
            label="PASS WITH WARNINGS"
            can_deploy=True

        else:
            decision=FirewallDecision.BLOCK
            label="DEPLOYMENT BLOCKED"
            can_deploy=False


        conditions=[]

        if failed:
            conditions.append(
             "Remediate failed fairness checks before production deployment"
            )

        return FirewallResult(
            decision=decision,
            decision_label=label,
            can_deploy=can_deploy,
            checks_passed=passed,
            checks_failed=failed,
            total_checks=len(checks),
            failed_checks=failed_checks,
            deployment_conditions=conditions
        )