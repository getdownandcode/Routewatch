# CostWatch Reproducibility Audit Report

**Audit Status**: PASSED (Deterministic)
**Total Executions**: 3

| Run | Output File | SHA-256 Hash | Status |
|:---:|:---|:---|:---:|
| Run 1 | `outputs/output.csv` | `4891fea1148dd7f8ae67a8e56adb628bb1e370f0d194a6c73c686ed0306efc20` | ✓ Identical |
| Run 2 | `outputs/output.csv` | `4891fea1148dd7f8ae67a8e56adb628bb1e370f0d194a6c73c686ed0306efc20` | ✓ Identical |
| Run 3 | `outputs/output.csv` | `4891fea1148dd7f8ae67a8e56adb628bb1e370f0d194a6c73c686ed0306efc20` | ✓ Identical |

### Guarantee:
- Same input generates byte-identical outputs across all runs.
- Explicit sort orders by `week_of` and `route` eliminate non-deterministic dictionary/set iteration.
- Temperature 0 and cached deterministic gates eliminate stochastic drift.