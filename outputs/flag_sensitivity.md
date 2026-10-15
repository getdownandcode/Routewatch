# Candidate Flag Threshold Sensitivity Analysis

| Own History Threshold | Similar Routes Threshold | Min History Weeks | Flagged Candidate Count | Candidate Route-Weeks |
|:---:|:---:|:---:|:---:|:---|
| +8% | +10% | 4 | **9** | Delhi-Jaipur (2024-11-11), Delhi-Jaipur (2024-11-18), Ahmedabad-Mumbai (2025-01-20), Chennai-Bangalore (2025-02-24), Chennai-Bangalore (2025-03-03), Chennai-Bangalore (2025-03-10), Chennai-Bangalore (2025-03-17), Mumbai-Pune (2025-09-15), Mumbai-Pune (2025-11-17) |
| +10% | +10% | 4 | **7** | Delhi-Jaipur (2024-11-11), Delhi-Jaipur (2024-11-18), Ahmedabad-Mumbai (2025-01-20), Chennai-Bangalore (2025-02-24), Chennai-Bangalore (2025-03-03), Chennai-Bangalore (2025-03-10), Chennai-Bangalore (2025-03-17) |
| +15% | +10% | 4 | **6** | Delhi-Jaipur (2024-11-11), Delhi-Jaipur (2024-11-18), Ahmedabad-Mumbai (2025-01-20), Chennai-Bangalore (2025-02-24), Chennai-Bangalore (2025-03-03), Chennai-Bangalore (2025-03-10) |

### Observations & Defense of Default Threshold (+8% own / +10% peer):
- Weekly own-history standard deviation across steady routes is ~4.0%, making +8% roughly a 2-sigma deviation.
- Peer comparison on Short routes (Mumbai-Pune vs Delhi-Jaipur) has only 1 peer, making individual peer noise higher; the dual-gate requirement prevents false positives from single-route noise.
- At 8/10, exactly 9 genuine anomaly spikes are captured (including floods, festival surcharges, and rate shifts). Higher thresholds miss genuine moderate increases like Mumbai-Pune (+9.2%).