FIX_AGENT_SYSTEM = """You are a fix agent for a web app/game generator. You receive build errors and must fix them with minimal changes.

RULES:
1. Only fix the specific errors reported
2. Write COMPLETE file contents (not patches)
3. Make minimal changes to fix the issues
4. All code must be self-contained - no external imports

You have the same tools available:
- write_file(file_path, content): Write complete file contents
- delete_file(file_path): Delete a file"""


def build_fix_prompt(errors: list[str], current_files: list[dict]) -> str:
    files_content = ""
    for f in current_files:
        files_content += f"\n--- {f['file_path']} ---\n{f['content']}\n"

    error_list = "\n".join(f"- {e}" for e in errors)

    return f"""Build errors to fix:
{error_list}

Current file contents:
{files_content}

Fix ONLY the reported errors with minimal changes."""
