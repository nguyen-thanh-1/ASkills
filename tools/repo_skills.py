#!/usr/bin/env python3
"""Build and validate the unified skill catalog.

The tool treats skills/ as the only distributable source of truth. Raw upstream
repositories are provenance inputs, never runtime dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATALOG = ROOT / "catalog"
COLLECTIONS = ROOT / "collections"
VALID_RISKS = {"none", "safe", "critical", "offensive", "unknown"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def parse_skill(path: Path) -> tuple[dict, str, str]:
    text = path.read_text(encoding="utf-8-sig")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter")
    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return metadata, text[match.end() :], text


def scalar(value: object) -> str:
    # JSON string scalars are valid YAML and avoid PyYAML's standalone `...`
    # document terminator for top-level scalar dumps.
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return yaml.safe_dump(value, allow_unicode=True, default_flow_style=True).strip().splitlines()[0]


def official_import_metadata() -> dict[str, dict]:
    config = load_yaml(ROOT / "config" / "official-imports.yaml")
    defaults = config.get("defaults", {})
    imported_on = str(config.get("imported_on", date.today().isoformat()))
    resolved: dict[str, dict] = {}
    for source_id, source in config.get("sources", {}).items():
        for skill_name, overrides in source.get("skills", {}).items():
            path = SKILLS / skill_name / "SKILL.md"
            if not path.is_file():
                raise FileNotFoundError(f"Configured official import is missing: {path}")
            resolved[skill_name] = {
                "category": overrides["category"],
                "risk": overrides["risk"],
                "source": source["source"],
                "source_repo": source["source_repo"],
                "source_type": defaults.get("source_type", "official"),
                "date_added": imported_on,
                "license": defaults.get("license", "See bundled license"),
                "imported_from": source_id,
            }
    return resolved


def sync_import_metadata() -> list[str]:
    # Official files stay byte-close to upstream and compatible with strict
    # Agent Skills validators. Repository-only metadata lives in config and is
    # merged into the generated catalog instead of rewriting SKILL.md.
    official_import_metadata()
    return []


def baseline_categories() -> dict[str, str]:
    path = ROOT / "sources" / "agentic-awesome-skills" / "skills_index.json"
    if not path.is_file():
        return {}
    items = json.loads(path.read_text(encoding="utf-8"))
    return {str(item.get("id")): str(item.get("category")) for item in items if item.get("id")}


def taxonomy_maps() -> tuple[dict, dict[str, str]]:
    taxonomy = load_yaml(ROOT / "config" / "taxonomy.yaml")
    alias_to_domain: dict[str, str] = {}
    for domain, info in taxonomy["domains"].items():
        alias_to_domain[domain] = domain
        for alias in info.get("aliases", []):
            alias_to_domain[str(alias)] = domain
    return taxonomy, alias_to_domain


def infer_domain(raw_category: str, metadata: dict, alias_to_domain: dict[str, str]) -> str:
    if raw_category in alias_to_domain:
        return alias_to_domain[raw_category]
    text = " ".join(
        str(metadata.get(key, "")) for key in ("name", "description", "tags")
    ).lower()
    rules = [
        ("security", ("security", "pentest", "vulnerability", "forensic", "malware", "threat")),
        ("cloud-devops", ("deploy", "kubernetes", "terraform", "cloud", "sre", "observability")),
        ("data-analytics", ("database", "postgres", "sql", "analytics", "data science", "spreadsheet")),
        ("marketing-sales", ("marketing", "seo", "sales", "campaign", "conversion", "brand")),
        ("design-creative", ("design", "figma", "visual", "illustration", "ui ", "ux ")),
        ("documents-office", ("document", "pdf", "docx", "pptx", "presentation", "office")),
        ("content-media", ("writing", "content", "video", "audio", "podcast", "speech")),
        ("ai-agents", ("agent", "llm", "model", "machine learning", "prompt")),
        ("automation-integrations", ("automation", "integration", "mcp", "api connector", "browser")),
        ("software-development", ("code", "developer", "frontend", "backend", "testing", "debug")),
    ]
    for domain, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return domain
    return "other"


def local_link_issues(skill_file: Path, text: str) -> list[str]:
    issues: list[str] = []
    visible_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    visible_text = re.sub(r"`[^`\n]+`", "", visible_text)
    for raw_target in LINK_RE.findall(visible_text):
        target = raw_target.strip().split()[0].strip("<>\"")
        if not target or target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        if target.upper() in {"URL", "URI", "PATH", "LINK"}:
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        resolved = (skill_file.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            issues.append(f"link escapes repository: {raw_target}")
            continue
        if not resolved.exists():
            issues.append(f"missing local link: {raw_target}")
    return issues


def inspect_skills(check_links: bool = True) -> tuple[list[dict], list[str], list[str]]:
    baseline = baseline_categories()
    official = official_import_metadata()
    taxonomy, alias_to_domain = taxonomy_maps()
    records: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, str] = {}
    for skill_file in sorted(SKILLS.rglob("SKILL.md")):
        relative = skill_file.relative_to(ROOT).as_posix()
        try:
            metadata, body, full_text = parse_skill(skill_file)
        except Exception as exc:  # noqa: BLE001 - validation should report every malformed skill
            errors.append(f"{relative}: {exc}")
            continue
        name = str(metadata.get("name", "")).strip()
        description = str(metadata.get("description", "")).strip()
        folder_name = skill_file.parent.name
        if not name:
            errors.append(f"{relative}: missing name")
            continue
        if not description:
            errors.append(f"{relative}: missing description")
        if not NAME_RE.fullmatch(name):
            errors.append(f"{relative}: invalid kebab-case name {name!r}")
        if name != folder_name:
            errors.append(f"{relative}: name {name!r} does not match folder {folder_name!r}")
        if name in seen:
            errors.append(f"{relative}: duplicate name {name!r}; first seen at {seen[name]}")
        else:
            seen[name] = relative
        nested = metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {}
        imported = official.get(name, {})
        risk = str(metadata.get("risk") or nested.get("risk") or imported.get("risk") or "unknown")
        if risk not in VALID_RISKS:
            errors.append(f"{relative}: invalid risk {risk!r}")
        if "risk" not in metadata and "risk" not in nested and "risk" not in imported:
            warnings.append(f"{relative}: missing risk metadata")
        source_value = metadata.get("source") or nested.get("source") or imported.get("source")
        if not source_value:
            warnings.append(f"{relative}: missing source metadata")
        has_trigger = re.search(
            r"^##\s+(When to Use|Use this skill when|When to use)",
            body,
            re.MULTILINE | re.IGNORECASE,
        ) or re.search(r"\buse (?:this skill )?when(?:ever)?\b", description, re.IGNORECASE)
        if not has_trigger:
            warnings.append(f"{relative}: missing an explicit When to Use section")
        if not re.search(r"^##\s+Limitations", body, re.MULTILINE | re.IGNORECASE):
            warnings.append(f"{relative}: missing a Limitations section")
        if check_links:
            warnings.extend(f"{relative}: {issue}" for issue in local_link_issues(skill_file, full_text))
        raw_category = str(
            metadata.get("category")
            or nested.get("category")
            or imported.get("category")
            or baseline.get(name)
            or "uncategorized"
        )
        domain = infer_domain(raw_category, metadata, alias_to_domain)
        files = [path for path in skill_file.parent.rglob("*") if path.is_file()]
        source_value = source_value or "unknown"
        source_type = metadata.get("source_type") or nested.get("source_type") or imported.get("source_type")
        if not source_type and source_value in {"official", "community", "self", "personal"}:
            source_type = source_value
        records.append(
            {
                "id": name,
                "name": name,
                "description": description,
                "path": skill_file.parent.relative_to(ROOT).as_posix(),
                "domain": domain,
                "category": raw_category,
                "risk": risk,
                "source": source_value,
                "source_repo": metadata.get("source_repo") or nested.get("source_repo") or imported.get("source_repo"),
                "source_type": source_type,
                "license": metadata.get("license") or nested.get("license") or imported.get("license"),
                "date_added": str(metadata.get("date_added") or nested.get("date_added") or imported.get("date_added") or "") or None,
                "files": len(files),
                "bytes": sum(path.stat().st_size for path in files),
                "has_scripts": (skill_file.parent / "scripts").is_dir(),
                "has_references": (skill_file.parent / "references").is_dir(),
            }
        )
    domain_ids = set(taxonomy["domains"])
    for record in records:
        if record["domain"] not in domain_ids:
            errors.append(f"{record['path']}: unknown normalized domain {record['domain']}")
    return records, errors, warnings


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_catalog() -> tuple[int, list[str], list[str]]:
    records, errors, warnings = inspect_skills(check_links=False)
    if errors:
        return len(records), errors, warnings
    taxonomy, _ = taxonomy_maps()
    records.sort(key=lambda item: (item["domain"], item["name"]))
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_domain[record["domain"]].append(record)
    summary = {
        "generated_on": date.today().isoformat(),
        "skill_count": len(records),
        "domain_count": len(taxonomy["domains"]),
        "risk_counts": dict(sorted(Counter(item["risk"] for item in records).items())),
        "source_type_counts": dict(
            sorted(Counter(str(item["source_type"] or "unspecified") for item in records).items())
        ),
        "domain_counts": {domain: len(by_domain.get(domain, [])) for domain in taxonomy["domains"]},
    }
    write_json(CATALOG / "skills.json", records)
    write_json(CATALOG / "summary.json", summary)
    COLLECTIONS.mkdir(parents=True, exist_ok=True)
    index_lines = ["# Skill collections", "", "Logical collections keep one canonical skill copy while making the library easy to browse.", ""]
    catalog_lines = ["# All Skills Catalog", "", f"Generated catalog of **{len(records):,}** canonical skills.", ""]
    for domain, info in taxonomy["domains"].items():
        items = by_domain.get(domain, [])
        title = info["title"]
        index_lines.append(f"- [{title}]({domain}.md) — {len(items):,} skills")
        lines = [f"# {title}", "", info["description"], "", f"Skills: **{len(items):,}**", ""]
        catalog_lines.extend([f"## {title}", "", info["description"], ""])
        for item in items:
            lines.append(f"- [`{item['name']}`](../{item['path']}/) — {item['description']}")
            catalog_lines.append(f"- [`{item['name']}`]({item['path']}/) — {item['description']}")
        lines.append("")
        catalog_lines.append("")
        (COLLECTIONS / f"{domain}.md").write_text("\n".join(lines), encoding="utf-8")
    (COLLECTIONS / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    (ROOT / "CATALOG.md").write_text("\n".join(catalog_lines), encoding="utf-8")
    return len(records), errors, warnings


def validate() -> tuple[int, list[str], list[str]]:
    records, errors, warnings = inspect_skills(check_links=True)
    documentation = list(ROOT.glob("*.md"))
    for directory in (ROOT / "docs", ROOT / "collections", ROOT / "spec"):
        if directory.is_dir():
            documentation.extend(directory.rglob("*.md"))
    for doc in sorted(set(documentation)):
        text = doc.read_text(encoding="utf-8-sig")
        relative = doc.relative_to(ROOT).as_posix()
        errors.extend(f"{relative}: {issue}" for issue in local_link_issues(doc, text))
    report = {
        "generated_on": date.today().isoformat(),
        "skill_count": len(records),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }
    write_json(CATALOG / "validation-report.json", report)
    return len(records), errors, warnings


def print_result(label: str, count: int, errors: list[str], warnings: list[str]) -> None:
    print(f"{label}: {count} skills, {len(errors)} errors, {len(warnings)} warnings")
    for item in errors[:50]:
        print(f"ERROR: {item}")
    if len(errors) > 50:
        print(f"ERROR: ... {len(errors) - 50} more (see catalog/validation-report.json)")
    for item in warnings[:20]:
        print(f"WARN: {item}")
    if len(warnings) > 20:
        print(f"WARN: ... {len(warnings) - 20} more (see catalog/validation-report.json)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sync-imports", "build", "validate", "all"))
    args = parser.parse_args()
    if args.command in {"sync-imports", "all"}:
        changed = sync_import_metadata()
        print(f"Official import metadata synchronized: {len(changed)} files changed")
    if args.command in {"build", "all"}:
        count, errors, warnings = build_catalog()
        print_result("Catalog build", count, errors, warnings)
        if errors:
            return 1
    if args.command in {"validate", "all"}:
        count, errors, warnings = validate()
        print_result("Validation", count, errors, warnings)
        if errors:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
