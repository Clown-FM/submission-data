# Replication Package

This package supports **auditing the measurement**. Every distribution, rate,
and ladder count reported in the paper can be recomputed from it. It does not
support **re-running the evaluation**, which would need the execution
environments, model access, and compute budget that produced the corpus.

## Contents

| Path | What it is | Paper |
|---|---|---|
| `user-space/` | 840 runs: the user-space set (CVE-GENIE's corpus, deduplicated) | §3.1, §3.4 |
| `kernel/` | 78 runs: the kernel set (K-Repro's KernelCTF challenges, deduplicated) | §3.1, §3.4 |
| `remote/` | 26 runs on remote Debian VMs, the classic-mitigation measurements | §4.1 |
| `other/` | 17 additional runs outside the two main collection windows | §3.1 |
| `ladder.py` | The rules that map each run to a depth-ladder level | §3.3 |
| `specs/` | The specification files defining each impact type's acceptance predicate and end marker | §2.2 |
| `strategies/` | The exploit strategy templates injected before a run | §2.2 |

Each run directory holds that run's records, its environment definition, and —
for kernel and remote runs — the mitigation probe results.

## Reproducing the ladder

`ladder.py` needs no dependencies:

```
$ python3 ladder.py
user-space   L0= 249  L1= 279  L2= 103  not_placed= 209  total= 840   [matches paper]
kernel       L0=  14  L1=   3  L2=  57  not_placed=   4  total=  78   [matches paper]
remote       L0=  10  L1=   3  L2=   2  not_placed=  11  total=  26
other        L0=   1  L1=   0  L2=   0  not_placed=  16  total=  17
```

A run's level comes from the impact type in its `actual_type` field, not from a
separate inspection of what it achieved. The two coincide at Level 2, where
every run reached the impact it was routed to. At Levels 0 and 1 a minority did
not, so those rows record where runs were routed; `_result.json` gives the
achieved counts. The mapping is listed at the top of `ladder.py`.

## The `verified` field

Every run's `_result.json` records manual re-execution:

```json
{ "verified": true, "verified_method": "reexecuted_verify_sh", ... }
```

- **`verified: true`** — the authors re-ran the run's verification script,
  directly observed the target effect, and confirmed the impact recorded in `ok`.
- **`verified: null`** — the run was **not** re-examined. This is not a negative
  result: `null` marks runs that `ok` already records as unsuccessful. Every run
  with `ok: true` carries `verified: true`.

Verification was performed by the authors, was not blinded, covered successes
and not failures, and recorded no agreement statistic. Because the unverified
runs are all non-successes, every reported rate is a **lower bound**.

## What is not here

**The exploit payloads are withheld.** That means the scripts the agent wrote
(`exp.sh`, `verify.sh`), its full reasoning traces (`agent.log`), the narrative
write-ups it produced (`report.md`, and the per-run `README.md`), and any
standalone exploit sources. Each of these is either a runnable weapon or a
step-by-step recipe for one. What remains — the records, the specifications,
the strategy templates, and the probe results — is what a reader needs in order
to audit the measurement, and the two sets are separable.

Also not included: the full source of the ExpPilot apparatus, on which the
measurements do not depend; and the downloaded software trees and build
artifacts inside each environment.

## Note on `status.json`

Each run also carries a `status.json` holding the framework's own per-run
verdict. Its success criterion **changed during collection**: 285 of the 839
user-space records that carry one apply an end-marker check, and 554 do not.
Where the check is present the verdict diverges from `_result.json` on 61.8% of
runs; where it is absent the two agree on 96.5%. The per-run framework verdict
is therefore not homogeneous across the corpus, and the paper reports the
run-level `_result.json` criterion only. `status.json` is included for
completeness.

## Coverage

The user-space set holds 840 runs: 807 recorded as successful, all 807 manually
re-executed and confirmed; the remaining 33 recorded as unsuccessful. One of
those 33, `user-space/CVE-2025-27606/`, failed at environment setup and produced
no artifacts, so its record is the only one in this package not written at run
time; it is flagged `"reconstructed": true` and carries an explanatory note.
