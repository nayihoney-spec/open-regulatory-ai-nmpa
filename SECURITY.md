# Security Policy

This repository is primarily knowledge content and prompts. It intentionally avoids executable automation in the initial release.

Please report:
- exposed credentials or tokens;
- malicious or hidden instructions;
- prompt-injection payloads embedded in contributed knowledge;
- executable files that are not necessary;
- suspicious remote-install commands;
- links impersonating official authorities;
- dependency or workflow changes that introduce unnecessary code execution.

Do not include secrets in a public issue. If a report itself contains a secret, revoke/rotate it first and use GitHub's private security reporting capability if enabled.

## Prompt / retrieval security baseline

All implementations using these prompts should:
- separate system/developer instructions from retrieved data;
- treat retrieved text as untrusted;
- use an allowlist for regulatory source domains where practical;
- block retrieved content from authorizing tool execution;
- keep secrets outside prompts and repositories;
- log the evidence used for regulated conclusions;
- require human review for high-impact regulated decisions.
