# SPDX-License-Identifier: Apache-2.0
"""Static repository and skill safety checker.

Uses only the Python standard library, performs no network access, and never
executes repository content.
"""
from pathlib import Path
from urllib.parse import urlparse
import re
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
SELF = Path("tools/repo_self_check.py")
TEXT_EXT = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".toml", ".ini", ".cfg", ".csv"}
DEPENDENCY_MANIFESTS = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "requirements.txt", "pyproject.toml", "poetry.lock", "Pipfile",
    "Pipfile.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
}

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
]
DANGEROUS_PATTERNS = [
    ("root-recursive deletion", re.compile(r"\brm\s+-rf\s+/(?:\s|$)")),
    ("curl pipe to shell", re.compile(r"\bcurl\b[^\n|]*\|\s*(?:ba)?sh\b")),
    ("wget pipe to shell", re.compile(r"\bwget\b[^\n|]*\|\s*(?:ba)?sh\b")),
    ("os.system", re.compile(r"\bos\.system\s*\(")),
    ("subprocess shell=True", re.compile(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True", re.S)),
    ("dynamic eval", re.compile(r"(?<![A-Za-z_])eval\s*\(")),
    ("dynamic exec", re.compile(r"(?<![A-Za-z_])exec\s*\(")),
]
BIDI_CONTROL = re.compile(r"[\u202A-\u202E\u2066-\u2069]")

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
REQUIRED = [
    "README.md", "DISCLAIMER.md", "CONTRIBUTING.md", "SECURITY.md",
    "LICENSE.md", "SELF_CHECK.md", "SKILL.md", "agents/openai.yaml",
]
ALLOWED_WORKFLOWS = {"repo-self-check.yml"}

errors, warnings = [], []
text_files = {}

for path in ROOT.rglob("*"):
    rel = path.relative_to(ROOT)
    if ".git" in rel.parts:
        continue
    if path.is_symlink():
        errors.append(f"{rel}: symbolic links are not allowed")
        continue
    if not path.is_file():
        continue
    if path.name in DEPENDENCY_MANIFESTS:
        errors.append(f"{rel}: unexpected dependency manifest")
    if path.suffix.lower() not in TEXT_EXT:
        continue
    try:
        raw = path.read_bytes()
        if b"\x00" in raw:
            errors.append(f"{rel}: NUL byte detected")
            continue
        text = raw.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"{rel}: unreadable UTF-8 text: {exc}")
        continue
    text_files[rel] = text
    if rel == SELF:
        continue
    if BIDI_CONTROL.search(text):
        errors.append(f"{rel}: bidirectional control character detected")
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: possible {label}")
    for label, pattern in DANGEROUS_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: dangerous execution pattern ({label})")

for item in REQUIRED:
    if not (ROOT / item).is_file():
        errors.append(f"missing required file: {item}")

skill_path = ROOT / "SKILL.md"
skill_name = ""
if skill_path.is_file():
    skill_text = skill_path.read_text(encoding="utf-8")
    if not skill_text.startswith("---\n"):
        errors.append("SKILL.md: missing opening YAML frontmatter delimiter")
    else:
        parts = skill_text.split("---", 2)
        if len(parts) != 3:
            errors.append("SKILL.md: missing closing YAML frontmatter delimiter")
        else:
            frontmatter, body = parts[1], parts[2]
            fields = {}
            for line in frontmatter.splitlines():
                if not line.strip():
                    continue
                if line[:1].isspace() or ":" not in line:
                    errors.append(f"SKILL.md: unsupported frontmatter line: {line!r}")
                    continue
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip().strip('"').strip("'")
            extra = sorted(set(fields) - {"name", "description"})
            if extra:
                errors.append(f"SKILL.md: unsupported frontmatter fields: {extra}")
            skill_name = fields.get("name", "")
            description = fields.get("description", "")
            if not re.fullmatch(r"[a-z0-9-]{1,63}", skill_name):
                errors.append("SKILL.md: name must use 1-63 lowercase letters, digits, or hyphens")
            if len(description) < 40:
                errors.append("SKILL.md: description is too short for reliable routing")
            if "TODO" in skill_text:
                errors.append("SKILL.md: unresolved TODO placeholder")
            if len(body.splitlines()) > 500:
                errors.append("SKILL.md: body exceeds 500 lines")
            for concept in ("untrusted", "official", "current", "human review"):
                if concept not in body.lower():
                    errors.append(f"SKILL.md: missing safety concept {concept!r}")
            for ref in re.findall(r"`([A-Za-z0-9_./-]+\.(?:md|yaml|yml))`", body):
                if not (ROOT / ref).is_file():
                    errors.append(f"SKILL.md: referenced file does not exist: {ref}")

agent_path = ROOT / "agents/openai.yaml"
if agent_path.is_file():
    agent_text = agent_path.read_text(encoding="utf-8")
    for key in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s*{key}:\s*[\"'].+[\"']\s*$", agent_text, re.M):
            errors.append(f"agents/openai.yaml: {key} must be present and quoted")
    if skill_name and ("$" + skill_name) not in agent_text:
        errors.append("agents/openai.yaml: default_prompt must mention the skill explicitly")
    if not re.search(r"^\s*allow_implicit_invocation:\s*true\s*$", agent_text, re.M):
        errors.append("agents/openai.yaml: implicit invocation must be explicitly enabled")

prompt_dir = ROOT / "prompts"
if prompt_dir.is_dir():
    for path in prompt_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        missing = [term for term in ("untrusted", "do not invent", "effective", "official") if term not in text]
        if missing:
            errors.append(f"{path.relative_to(ROOT)}: missing safety concepts {missing}")

for rel, text in text_files.items():
    if rel.name not in {"sources.yaml", "sources.yml"}:
        continue
    for url in re.findall(r"https://[^\s'\"\])>]+", text):
        host = urlparse(url.rstrip(".,;")).hostname
        if host and host.lower() not in OFFICIAL_DOMAINS:
            warnings.append(f"{rel}: non-allowlisted source domain {host}")

workflow_dir = ROOT / ".github/workflows"
if workflow_dir.is_dir():
    for path in workflow_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".yml", ".yaml"}:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if path.name not in ALLOWED_WORKFLOWS:
            errors.append(f"{rel}: unexpected workflow")
        if "pull_request_target" in text:
            errors.append(f"{rel}: pull_request_target is not allowed")
        if re.search(r"^\s*(?:contents|actions|checks|deployments|id-token|packages|pull-requests|security-events|statuses):\s*write\s*$", text, re.M):
            errors.append(f"{rel}: write permission is not allowed")
        for used in re.findall(r"^\s*-?\s*uses:\s*([^\s#]+)", text, re.M):
            if "@" not in used or not re.fullmatch(r"[^@]+@[0-9a-fA-F]{40}", used):
                errors.append(f"{rel}: action is not pinned to a full commit SHA: {used}")

print(f"Checked: {ROOT}")
print(f"Errors: {len(errors)}")
for item in errors:
    print("ERROR:", item)
print(f"Warnings: {len(warnings)}")
for item in warnings:
    print("WARN:", item)
sys.exit(1 if errors else 0)

