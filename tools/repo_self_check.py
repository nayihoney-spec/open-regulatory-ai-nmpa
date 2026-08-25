# SPDX-License-Identifier: Apache-2.0
"""
Static repository safety checker.
No network access. No external dependencies. It does not execute repository content.
"""
from pathlib import Path
from urllib.parse import urlparse
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
TEXT_EXT = {".md", ".txt", ".yaml", ".yml", ".json", ".py"}
SKIP = {Path("tools/repo_self_check.py")}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
]
DANGEROUS_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/(?:\s|$)"),
    re.compile(r"curl\b[^\n|]*\|\s*(?:ba)?sh\b"),
    re.compile(r"wget\b[^\n|]*\|\s*(?:ba)?sh\b"),
    re.compile(r"os\.system\s*\("),
    re.compile(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True"),
]

OFFICIAL_DOMAINS = {
    "nmpa.gov.cn", "www.nmpa.gov.cn", "english.nmpa.gov.cn",
    "cde.org.cn", "www.cde.org.cn", "cfdi.org.cn", "www.cfdi.org.cn",
    "fda.gov", "www.fda.gov", "ecfr.gov", "www.ecfr.gov",
    "federalregister.gov", "www.federalregister.gov",
    "ema.europa.eu", "www.ema.europa.eu",
    "health.ec.europa.eu", "eur-lex.europa.eu",
    "ich.org", "www.ich.org",
    "creativecommons.org", "www.apache.org", "github.com",
}

def iter_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if ".git" in rel.parts or rel in SKIP:
            continue
        if p.suffix.lower() in TEXT_EXT:
            yield p, rel

errors, warnings = [], []
for p, rel in iter_files():
    raw = p.read_bytes()
    if b"\x00" in raw:
        errors.append(f"{rel}: NUL byte detected")
        continue
    text = raw.decode("utf-8", errors="strict")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: possible secret/private key pattern")
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: dangerous execution pattern")

    if rel.name in {"sources.yaml", "sources.yml"}:
        for url in re.findall(r"https://[^\s'\"\])>]+", text):
            host = urlparse(url).hostname
            if host and host not in OFFICIAL_DOMAINS:
                warnings.append(f"{rel}: non-allowlisted domain {host}")

required = ["README.md", "DISCLAIMER.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE.md", "SELF_CHECK.md"]
for item in required:
    if not (ROOT / item).exists():
        errors.append(f"missing required file: {item}")

prompt_files = list((ROOT / "prompts").glob("*.md")) if (ROOT / "prompts").exists() else []
for p in prompt_files:
    t = p.read_text(encoding="utf-8").lower()
    must = ["untrusted", "do not invent", "effective", "official"]
    missing = [m for m in must if m not in t]
    if missing:
        errors.append(f"{p.relative_to(ROOT)}: missing safety concepts {missing}")

print(f"Checked: {ROOT}")
print(f"Errors: {len(errors)}")
for x in errors:
    print("ERROR:", x)
print(f"Warnings: {len(warnings)}")
for x in warnings:
    print("WARN:", x)
sys.exit(1 if errors else 0)
