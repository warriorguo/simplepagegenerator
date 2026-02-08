import re

from app.schemas.pipeline import BuildResult


FORBIDDEN_PATTERNS = [
    r'\bimport\s+',
    r'\brequire\s*\(',
    r'\bfetch\s*\(',
    r'<script\s+src=["\']https?://',
    r'<link\s+.*href=["\']https?://',
]


def validate_html(content: str) -> list[str]:
    errors = []
    if "<!DOCTYPE html>" not in content and "<html" not in content:
        errors.append("Missing <!DOCTYPE html> or <html> tag")
    if "<head" not in content:
        errors.append("Missing <head> section")
    if "<body" not in content:
        errors.append("Missing <body> section")
    return errors


def check_forbidden_patterns(content: str, file_path: str) -> list[str]:
    warnings = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, content):
            warnings.append(f"Warning: potentially risky pattern in {file_path}: {pattern}")
    return warnings


def check_file_references(html_content: str, available_files: set[str]) -> list[str]:
    errors = []
    # Check src and href attributes for local file references
    refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html_content)
    for ref in refs:
        if ref.startswith(("http://", "https://", "data:", "#", "mailto:")):
            continue
        # Strip leading ./
        clean = ref.lstrip("./")
        if clean and clean not in available_files:
            errors.append(f"Referenced file not found: {ref}")
    return errors


def validate_build(files: list[dict]) -> BuildResult:
    errors = []
    warnings = []
    available = {f["file_path"] for f in files}

    html_found = False
    for f in files:
        if f["file_path"] == "index.html":
            html_found = True
            errors.extend(validate_html(f["content"]))
            errors.extend(check_file_references(f["content"], available))

        warnings.extend(check_forbidden_patterns(f["content"], f["file_path"]))

    if not html_found:
        errors.append("Missing index.html")

    return BuildResult(success=len(errors) == 0, errors=errors, warnings=warnings)
