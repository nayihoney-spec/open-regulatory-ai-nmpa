# Release Self-Check

Release: `v0.2.0`

This release is Skill-enabled and includes a safety-first static validation baseline.

## Automated validation

The repository contains one GitHub Actions workflow: `.github/workflows/repo-self-check.yml`. It uses read-only permissions, pins `actions/checkout` to a full commit SHA, installs no dependencies, compiles the local checker, and runs:

```bash
python3 tools/repo_self_check.py .
```

The checker uses only the Python standard library, performs no network access, and never executes repository content.

## Checks performed

- [x] Required Skill files and UI metadata are present.
- [x] Skill name, description, reference paths, safety concepts, and implicit-invocation setting are validated.
- [x] No plaintext API keys, tokens, passwords, private keys, or credentials are intentionally included.
- [x] No customer, patient, or employee confidential data is intentionally included.
- [x] No shell installer, pipe-to-shell command, destructive root command, hidden executable payload, dynamic eval/exec, or unsafe subprocess pattern is intentionally included.
- [x] Symbolic links, unexpected dependency manifests, bidirectional control characters, unexpected workflows, workflow write permissions, `pull_request_target`, and unpinned actions are blocked.
- [x] Regulatory source registries use recognized official authority domains.
- [x] Prompts treat retrieved material as untrusted data and prohibit fabricated citations or regulatory claims.
- [x] Prompts require official evidence and current-status checks.
- [x] Binding requirements are separated from guidance, Q&A, inspection observations, enforcement correspondence, drafts, and historical material.
- [x] Human review is required for regulated or high-impact decisions.
- [x] No proprietary Aves AI Hub runtime, customer configuration, credential, commercial workflow, or private knowledge base is included.

## Known limitations

- This is an initial taxonomy and retrieval module, not a complete regulatory database.
- Regulatory sites, legal instruments, guidance, and authority structures change over time and must be revalidated.
- Static checks reduce common repository and workflow risks but do not replace human code review, regulatory review, or platform security controls.
- NMPA notices, announcements, technical guidelines, standards, and formal regulations must be distinguished by document type, current status, and legal effect.
