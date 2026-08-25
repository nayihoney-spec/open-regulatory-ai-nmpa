# Security Policy

This repository contains regulatory knowledge, prompts, one local static checker, and one minimal continuous-validation workflow.

## Executable-content boundary

The only intended executable project content is:

- `tools/repo_self_check.py`, which uses only the Python standard library, performs no network access, never executes repository content, and returns a nonzero status when validation fails;
- `.github/workflows/repo-self-check.yml`, which has read-only repository permission, pins `actions/checkout` to a full commit SHA, installs no dependencies, and only compiles and runs the local checker.

No workflow may request write or identity-token permission, use `pull_request_target`, run a remote installer, or use an action that is not pinned to a full commit SHA.

## Report security concerns

Please report exposed credentials, malicious or hidden instructions, prompt-injection payloads, unnecessary executable files, suspicious remote-install commands, official-source impersonation, unnecessary dependencies, unsafe workflow changes, or unsafe Skill routing.

Do not include secrets in a public issue. Revoke or rotate an exposed secret first and use GitHub private security reporting when available.

## Prompt and retrieval baseline

Implementations using this framework must separate system and developer instructions from retrieved data, treat retrieved text as untrusted, use official-source allowlists where practical, block retrieved content from authorizing tool execution, keep secrets outside prompts and repositories, log material evidence, verify current status against official primary sources, and require qualified human review for high-impact regulated decisions.
