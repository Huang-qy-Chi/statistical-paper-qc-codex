# Coverage and evidence ledger

Create UTF-8 JSON. Start scoped checks as pending, use stable IDs and bounded checks (one reconciliation, identity, step or reference group).

```json
{
  "schema_version": 1,
  "manuscript_id": "EXAMPLE-001",
  "scope": "A and B, main Tables 1 and 2",
  "inputs": [{"role": "main", "path": "ABSOLUTE/main.pdf", "sha256": "COPY_FROM_MANIFEST"}],
  "limitations": [],
  "items": [{
    "id": "B-T1-total", "module": "B", "object": "Table 1 total",
    "status": "pending", "claim": "The total equals the sum of its rows",
    "location": {"role": "main", "pdf_page": 3, "printed_page": "2"},
    "equation_level": false, "evidence": [], "reason": "Awaiting recomputation"
  }]
}
```

Replace example paths/hash/scope. Inputs require unique roles and a 64-digit hex SHA-256. Locations use a supplied role and one-based PDF page; printed_page may be null. For broad absence checks locate the relevant section and state complete search ranges in evidence.

Statuses:
- pending: unfinished, reason required.
- inconclusive: examined but unresolved, reason required; retain available evidence.
- not_applicable: does not apply, reason required.
- verified: bounded claim supported, evidence required.
- finding: substantiated issue, evidence plus kind (Error/Gap/Defect), severity (Critical/Major/Minor), finding and suggested_fix required.

Evidence objects have method and detail; optional artifact is an existing absolute path, visually_inspected is boolean. Methods: page_image, recomputation, search, comparison, derivation, external_source. Store evidence in the audit workspace. For numerical findings save executable code and output and reference both. For absence claims record terms, documents, ranges and manual follow-up. Equation-level findings require page_image evidence with an existing PNG and visually_inspected=true after actually viewing it.

Only finding items count toward issue severity. Unresolved hypotheses remain inconclusive. Derive counts using the helper; report resolved (verified + finding), inconclusive, pending and not_applicable separately. Validation checks evidence declarations and artifact existence, not their contents or the truth of the conclusion.
