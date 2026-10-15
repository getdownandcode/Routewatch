# CostWatch System Evaluation & Fabrication Audit Report

**Test Cases Evaluated**: 28
**Verdict Accuracy**: 100.0% (28/28)
**Note ID Accuracy**: 100.0% (28/28)
**Fabrication Audit Integrity**: 100.0% (28/28)
**Hallucinated / Fabricated Justifications**: **0**

## Detailed Evaluation Matrix

| Case | Route | Week | Expected | Predicted | Note Exp | Note Pred | Status | Fabrication Audit | Description |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| C01 | Ahmedabad-Mumbai | 2025-01-20 | No (justified) | No (justified) | `N002` | `N002` | ✓ PASS | ✓ PASS | Festival surcharge week on corridor |
| C02 | Chennai-Bangalore | 2025-02-24 | No (justified) | No (justified) | `N001` | `N001` | ✓ PASS | ✓ PASS | Severe highway flood disruption start |
| C03 | Chennai-Bangalore | 2025-03-03 | No (justified) | No (justified) | `N001` | `N001` | ✓ PASS | ✓ PASS | Flood disruption continuation |
| C04 | Chennai-Bangalore | 2025-03-10 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Post-flood week: N001 ended on March 8 |
| C05 | Chennai-Bangalore | 2025-03-17 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N009 reports highway returned to normal |
| C06 | Delhi-Jaipur | 2024-11-11 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Candidate with no matching note in date range |
| C07 | Delhi-Jaipur | 2024-11-18 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Candidate with no matching note in date range |
| C08 | Mumbai-Pune | 2025-09-15 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N006 mentions stable demand with no disruptions |
| C09 | Mumbai-Pune | 2025-11-17 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N010 costs absorbed without rate change |
| C10 | Delhi-Jaipur | 2024-03-11 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N004 new toll plaza on routes outside dataset |
| C11 | Mumbai-Delhi | 2024-07-29 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N005 maintenance caused minor delays without cost effect |
| C12 | Delhi-Jaipur | 2024-05-20 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N007 road resurfacing reduced costs |
| C13 | Kolkata-Bhubaneswar | 2025-06-09 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N008 normal freight movement with no disruption |
| C14 | Mumbai-Delhi | 2025-04-28 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Week before N003 diesel price rise started |
| C15 | Delhi-Jaipur | 2025-01-20 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Wrong route trap: N002 applied to Delhi-Jaipur |
| C16 | Mumbai-Delhi | 2025-02-24 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Wrong route trap: N001 flood applied to Mumbai-Delhi |
| C17 | Kolkata-Bhubaneswar | 2025-01-20 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Wrong route trap: N002 applied to Kolkata-Bhubaneswar |
| C18 | Delhi-Chennai | 2025-02-24 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Wrong route trap: N001 flood applied to Delhi-Chennai |
| C19 | Mumbai-Pune | 2024-05-20 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Wrong route trap: N007 resurfacing applied to Mumbai-Pune |
| C20 | Ahmedabad-Mumbai | 2024-07-29 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Wrong route trap: N005 maintenance applied to Ahmedabad-Mumbai |
| C21 | Mumbai-Pune | 2024-01-08 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard week with normal costs |
| C22 | Delhi-Jaipur | 2024-06-10 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard summer week with normal costs |
| C23 | Chennai-Bangalore | 2024-09-16 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard monsoon week with normal costs |
| C24 | Kolkata-Bhubaneswar | 2024-11-04 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard autumn week with normal costs |
| C25 | Ahmedabad-Mumbai | 2024-12-16 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard winter week with normal costs |
| C26 | Mumbai-Delhi | 2025-01-06 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard post-holiday week with normal costs |
| C27 | Delhi-Chennai | 2025-06-16 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Standard mid-year week with normal costs |
| C28 | Delhi-Jaipur | 2025-09-22 | Yes | Yes | `` | `` | ✓ PASS | ✓ PASS | Trap: N006 stable demand applied to Delhi-Jaipur |

## Guardrail Verification Summary
1. **No Hallucination**: 100% of justified verdicts are backed by a real note verified against route, dates, and effect.
2. **Trap Notes Rejection**: All non-justifying notes (N004-N010) are successfully prevented from justifying any route.
3. **Zero False Justifications**: Every unexplained row leaves `matched_note_id` blank.