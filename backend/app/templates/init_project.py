DEFAULT_FILES = [
    {
        "file_path": "index.html",
        "file_type": "text/html",
        "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Project</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <h1>Project Ready</h1>
        <p>Start chatting to build your app!</p>
    </div>
    <script src="script.js"></script>
</body>
</html>""",
    },
    {
        "file_path": "style.css",
        "file_type": "text/css",
        "content": """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #0a0a0a;
    color: #e0e0e0;
}

#app {
    text-align: center;
    padding: 2rem;
}

h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    color: #4fc3f7;
}

p {
    color: #999;
}""",
    },
    {
        "file_path": "script.js",
        "file_type": "application/javascript",
        "content": """// Your app logic goes here
console.log('Project initialized!');
""",
    },
    {
        "file_path": "game.js",
        "file_type": "application/javascript",
        "content": """// Game logic goes here
// This file is for game-specific code
""",
    },
]
