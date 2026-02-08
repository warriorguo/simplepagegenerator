SANDBOX_CSP = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:;"

SANDBOX_ATTRS = "allow-scripts"

MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".txt": "text/plain",
}


def get_mime_type(file_path: str) -> str:
    for ext, mime in MIME_TYPES.items():
        if file_path.endswith(ext):
            return mime
    return "text/plain"
