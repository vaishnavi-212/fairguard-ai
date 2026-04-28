# FairGuard AI – Multi-Agent Fairness Copilot

> Bias detection, legal compliance auditing, and AI-assisted governance 
> for automated hiring systems — in one no-code copilot.

---

## Problem

Hidden bias in automated hiring systems causes unfair outcomes for 
millions of job seekers. Most organizations lack the tools or expertise 
to detect, measure, or remediate algorithmic discrimination before 
it causes legal and reputational damage.

---

## Solution

FairGuard AI is a fairness copilot that lets any HR team or organization 
upload their hiring data and instantly receive a full compliance audit — 
no data science expertise required.

---

## How It Works

Upload CSV → Statistical Fairness Analysis → Bias Firewall Decision → 
Gemini AI Audit Report → Firebase Audit History

---

## Core Features

### Fairness Engine
Computes 4 industry-standard fairness metrics:
- **Demographic Parity** — with Chi-square significance testing & Cramér's V
- **Equalized Odds** — TPR/FPR gap analysis across protected groups
- **Disparate Impact** — EEOC 4/5ths Rule compliance check
- **Calibration** — Brier score imbalance detection across groups
- **Intersectional Analysis** — compound discrimination across multiple attributes

### Bias Firewall
A policy enforcement engine that gates deployment based on legal thresholds:
- `PASS` — all fairness checks met
- `PASS WITH WARNINGS` — minor violations, conditional deployment
- `DEPLOYMENT BLOCKED` — critical violations, legally non-compliant

Thresholds are not arbitrary — they encode the EEOC 4/5ths Rule 
(Title VII, Civil Rights Act) and AI fairness literature standards.

### Gemini AI Advisor
Google Gemini 1.5 Flash generates:
- Executive summary of audit findings
- Legal compliance checklist (EEOC, Title VII, GDPR Art. 22, EU AI Act)
- Prioritized remediation roadmap
- Context-aware Q&A on your specific audit results

### Audit History (Firebase)
Every audit is persisted to Cloud Firestore — enabling trend analysis, 
score tracking, and governance documentation over time.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Fairness Engine | Python, NumPy, SciPy, Pandas |
| AI Advisor | Google Gemini 1.5 Flash |
| Audit Storage | Firebase Cloud Firestore |
| Visualizations | Plotly |
| Config | python-dotenv |

---

## SDG Alignment

- **SDG 8** — Decent Work and Economic Growth
- **SDG 10** — Reduced Inequalities
- **SDG 16** — Peace, Justice and Strong Institutions

---

## Legal Standards Implemented

- EEOC 4/5ths (80%) Rule
- Title VII of the Civil Rights Act
- GDPR Article 22 (automated decision-making)
- EU AI Act — High-Risk AI System requirements

---

## USP

Most bias tools only diagnose. FairGuard **audits, explains, enforces 
and documents** — combining statistical analysis, legal compliance 
checking, AI-powered recommendations, and persistent audit trails 
in a single no-code copilot built for HR teams, not data scientists.