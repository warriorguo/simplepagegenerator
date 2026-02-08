TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write complete contents to a file. Always provide the FULL file content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The file path (e.g., 'index.html', 'style.css', 'script.js')",
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete file content to write",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The file path to delete",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
]
