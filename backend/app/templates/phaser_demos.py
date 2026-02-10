"""
Phaser 3 Game Demo Templates Catalog
Each template is a complete, runnable HTML5 game using Phaser 3 from CDN
No external assets required - all graphics drawn with Phaser primitives
"""

PHASER_DEMO_CATALOG = [
    {
        "template_id": "platformer_basic",
        "title": "Classic Platformer",
        "core_loop": "Jump between platforms, avoid falling, collect coins",
        "controls": "Arrow keys to move, Space to jump / Touch sides to move",
        "mechanics": ["jumping", "gravity", "platforms", "collectibles", "score"],
        "complexity": "medium",
        "mobile_fit": "good",
        "tags": ["action", "platformer", "classic", "arcade"],
        "files": [
            {
                "file_path": "index.html",
                "file_type": "text/html",
                "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Classic Platformer</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #1a1a2e;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }
        canvas {
            display: block;
            margin: auto;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <script>
        const config = {
            type: Phaser.AUTO,
            width: 800,
            height: 600,
            backgroundColor: '#87CEEB',
            physics: {
                default: 'arcade',
                arcade: {
                    gravity: { y: 800 },
                    debug: false
                }
            },
            scene: {
                create: create,
                update: update
            },
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }
        };

        const game = new Phaser.Game(config);
        let player, platforms, coins, cursors, score = 0, scoreText, gameOver = false;
        let touchLeft, touchRight, touchJump;

        function create() {
            // Create platforms group
            platforms = this.physics.add.staticGroup();

            // Ground
            const ground = this.add.rectangle(400, 580, 800, 40, 0x2d572c);
            platforms.add(ground);

            // Platforms
            const platformData = [
                { x: 200, y: 450, w: 200, h: 20 },
                { x: 600, y: 400, w: 200, h: 20 },
                { x: 100, y: 300, w: 150, h: 20 },
                { x: 700, y: 250, w: 150, h: 20 },
                { x: 400, y: 200, w: 200, h: 20 }
            ];

            platformData.forEach(p => {
                const platform = this.add.rectangle(p.x, p.y, p.w, p.h, 0x8B4513);
                platforms.add(platform);
            });

            platforms.refresh();

            // Create player
            player = this.add.rectangle(100, 450, 30, 40, 0xFF6B6B);
            this.physics.add.existing(player);
            player.body.setBounce(0.1);
            player.body.setCollideWorldBounds(true);

            // Create coins
            coins = this.physics.add.group();
            const coinPositions = [
                { x: 200, y: 400 }, { x: 600, y: 350 }, { x: 100, y: 250 },
                { x: 700, y: 200 }, { x: 400, y: 150 }, { x: 50, y: 500 },
                { x: 750, y: 500 }, { x: 400, y: 500 }
            ];

            coinPositions.forEach(pos => {
                const coin = this.add.circle(pos.x, pos.y, 12, 0xFFD700);
                coins.add(coin);
                coin.body.setAllowGravity(false);
                coin.body.setBounce(0);

                // Add sparkle animation
                this.tweens.add({
                    targets: coin,
                    scaleX: 1.2,
                    scaleY: 1.2,
                    duration: 500,
                    yoyo: true,
                    repeat: -1
                });
            });

            // Collisions
            this.physics.add.collider(player, platforms);
            this.physics.add.overlap(player, coins, collectCoin, null, this);

            // Input
            cursors = this.input.keyboard.createCursorKeys();

            // Touch controls
            const controlsY = 550;
            touchLeft = this.add.rectangle(60, controlsY, 80, 60, 0x4ECDC4, 0.5);
            touchLeft.setInteractive();
            touchLeft.setScrollFactor(0);

            touchRight = this.add.rectangle(180, controlsY, 80, 60, 0x4ECDC4, 0.5);
            touchRight.setInteractive();
            touchRight.setScrollFactor(0);

            touchJump = this.add.rectangle(720, controlsY, 100, 60, 0xFF6B6B, 0.5);
            touchJump.setInteractive();
            touchJump.setScrollFactor(0);

            this.add.text(60, controlsY, '◀', { fontSize: '32px', color: '#fff' }).setOrigin(0.5);
            this.add.text(180, controlsY, '▶', { fontSize: '32px', color: '#fff' }).setOrigin(0.5);
            this.add.text(720, controlsY, 'JUMP', { fontSize: '20px', color: '#fff' }).setOrigin(0.5);

            // Score
            scoreText = this.add.text(16, 16, 'Score: 0', {
                fontSize: '28px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 4
            });

            // Instructions
            this.add.text(400, 50, 'Collect all coins!', {
                fontSize: '24px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 3
            }).setOrigin(0.5);
        }

        function update() {
            if (gameOver) return;

            // Movement
            const speed = 200;

            if (cursors.left.isDown || (touchLeft.input?.activePointer?.isDown &&
                this.input.activePointer.x < 120)) {
                player.body.setVelocityX(-speed);
            } else if (cursors.right.isDown || (touchRight.input?.activePointer?.isDown &&
                       this.input.activePointer.x > 120 && this.input.activePointer.x < 230)) {
                player.body.setVelocityX(speed);
            } else {
                player.body.setVelocityX(0);
            }

            // Jump
            if ((cursors.space.isDown || cursors.up.isDown ||
                (this.input.activePointer.isDown && this.input.activePointer.x > 670)) &&
                player.body.touching.down) {
                player.body.setVelocityY(-400);
            }

            // Check if fell off
            if (player.y > 650) {
                gameOver = true;
                this.add.text(400, 300, 'Game Over!\\nScore: ' + score, {
                    fontSize: '48px',
                    fill: '#fff',
                    stroke: '#000',
                    strokeThickness: 6,
                    align: 'center'
                }).setOrigin(0.5);
            }
        }

        function collectCoin(player, coin) {
            coin.destroy();
            score += 10;
            scoreText.setText('Score: ' + score);

            // Check win condition
            if (coins.countActive(true) === 0) {
                gameOver = true;
                this.add.text(400, 300, 'You Win!\\nFinal Score: ' + score, {
                    fontSize: '48px',
                    fill: '#FFD700',
                    stroke: '#000',
                    strokeThickness: 6,
                    align: 'center'
                }).setOrigin(0.5);
            }
        }
    </script>
</body>
</html>"""
            }
        ]
    },
    {
        "template_id": "shooter_topdown",
        "title": "Top-Down Shooter",
        "core_loop": "Move and shoot enemies, survive waves",
        "controls": "Arrow keys to move, Space to shoot / Touch to move + auto-shoot",
        "mechanics": ["shooting", "enemies", "waves", "health", "score"],
        "complexity": "medium",
        "mobile_fit": "good",
        "tags": ["action", "shooter", "arcade", "wave-based"],
        "files": [
            {
                "file_path": "index.html",
                "file_type": "text/html",
                "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Top-Down Shooter</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #0a0a0a;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        canvas {
            display: block;
            margin: auto;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <script>
        const config = {
            type: Phaser.AUTO,
            width: 800,
            height: 600,
            backgroundColor: '#1a1a2e',
            physics: {
                default: 'arcade',
                arcade: {
                    debug: false
                }
            },
            scene: {
                create: create,
                update: update
            },
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }
        };

        const game = new Phaser.Game(config);
        let player, enemies, bullets, cursors, scoreText, healthText;
        let score = 0, health = 100, gameOver = false;
        let lastFired = 0, fireRate = 200, enemySpawnTimer = 0;
        let wave = 1, enemiesThisWave = 5, enemiesSpawned = 0, enemiesKilled = 0;

        function create() {
            // Player
            player = this.add.container(400, 500);
            const playerBody = this.add.triangle(0, 0, 0, -15, -12, 15, 12, 15, 0x00D9FF);
            player.add(playerBody);
            this.physics.add.existing(player);
            player.body.setCollideWorldBounds(true);
            player.body.setSize(24, 30);

            // Groups
            enemies = this.physics.add.group();
            bullets = this.physics.add.group();

            // Input
            cursors = this.input.keyboard.createCursorKeys();
            this.input.keyboard.on('keydown-SPACE', () => shootBullet.call(this));

            // Touch input
            this.input.on('pointerdown', (pointer) => {
                if (gameOver) return;
                // Move towards touch
                const angle = Phaser.Math.Angle.Between(player.x, player.y, pointer.x, pointer.y);
                this.physics.velocityFromRotation(angle, 300, player.body.velocity);
            });

            // Collisions
            this.physics.add.overlap(bullets, enemies, hitEnemy, null, this);
            this.physics.add.overlap(player, enemies, hitPlayer, null, this);

            // UI
            scoreText = this.add.text(16, 16, 'Score: 0', {
                fontSize: '24px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 3
            });

            healthText = this.add.text(16, 50, 'Health: 100', {
                fontSize: '24px',
                fill: '#0f0',
                stroke: '#000',
                strokeThickness: 3
            });

            this.waveText = this.add.text(400, 30, 'Wave 1', {
                fontSize: '28px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5);

            // Auto-shoot timer for mobile
            this.time.addEvent({
                delay: 250,
                callback: () => {
                    if (!gameOver && this.input.activePointer.isDown) {
                        shootBullet.call(this);
                    }
                },
                loop: true
            });
        }

        function update(time) {
            if (gameOver) return;

            // Player movement with keyboard
            const speed = 300;
            if (cursors.left.isDown) {
                player.body.setVelocityX(-speed);
            } else if (cursors.right.isDown) {
                player.body.setVelocityX(speed);
            } else if (!this.input.activePointer.isDown) {
                player.body.setVelocityX(0);
            }

            if (cursors.up.isDown) {
                player.body.setVelocityY(-speed);
            } else if (cursors.down.isDown) {
                player.body.setVelocityY(speed);
            } else if (!this.input.activePointer.isDown) {
                player.body.setVelocityY(0);
            }

            // Spawn enemies
            if (enemiesSpawned < enemiesThisWave) {
                enemySpawnTimer += 16;
                if (enemySpawnTimer > 1000) {
                    spawnEnemy.call(this);
                    enemiesSpawned++;
                    enemySpawnTimer = 0;
                }
            }

            // Move enemies toward player
            enemies.children.entries.forEach(enemy => {
                this.physics.moveToObject(enemy, player, 100);
            });

            // Clean up off-screen bullets
            bullets.children.entries.forEach(bullet => {
                if (bullet.y < -10) bullet.destroy();
            });

            // Check wave completion
            if (enemiesSpawned >= enemiesThisWave && enemies.countActive(true) === 0 && !gameOver) {
                startNextWave.call(this);
            }
        }

        function shootBullet() {
            if (gameOver) return;

            const bullet = this.add.circle(player.x, player.y - 20, 4, 0xFFFF00);
            bullets.add(bullet);
            bullet.body.setVelocityY(-500);
            bullet.body.setAllowGravity(false);
        }

        function spawnEnemy() {
            const x = Phaser.Math.Between(50, 750);
            const enemy = this.add.rectangle(x, -20, 30, 30, 0xFF0055);
            enemies.add(enemy);
            enemy.body.setAllowGravity(false);

            // Pulse animation
            this.tweens.add({
                targets: enemy,
                scaleX: 1.2,
                scaleY: 1.2,
                duration: 400,
                yoyo: true,
                repeat: -1
            });
        }

        function hitEnemy(bullet, enemy) {
            bullet.destroy();
            enemy.destroy();
            score += 10;
            scoreText.setText('Score: ' + score);
            enemiesKilled++;
        }

        function hitPlayer(player, enemy) {
            enemy.destroy();
            health -= 10;
            healthText.setText('Health: ' + health);

            if (health <= 50) {
                healthText.setColor('#ff0');
            }
            if (health <= 25) {
                healthText.setColor('#f00');
            }

            // Flash player
            this.tweens.add({
                targets: player,
                alpha: 0.5,
                duration: 100,
                yoyo: true,
                repeat: 2
            });

            if (health <= 0) {
                gameOver = true;
                player.destroy();
                this.add.text(400, 300, 'GAME OVER\\nFinal Score: ' + score, {
                    fontSize: '48px',
                    fill: '#f00',
                    stroke: '#000',
                    strokeThickness: 6,
                    align: 'center'
                }).setOrigin(0.5);
            }
        }

        function startNextWave() {
            wave++;
            enemiesThisWave = 5 + (wave * 2);
            enemiesSpawned = 0;
            enemiesKilled = 0;

            this.waveText.setText('Wave ' + wave);

            // Flash wave text
            this.tweens.add({
                targets: this.waveText,
                scaleX: 1.5,
                scaleY: 1.5,
                duration: 300,
                yoyo: true
            });

            // Heal player a bit
            health = Math.min(100, health + 20);
            healthText.setText('Health: ' + health);
            if (health > 50) healthText.setColor('#0f0');
        }
    </script>
</body>
</html>"""
            }
        ]
    },
    {
        "template_id": "puzzle_match",
        "title": "Color Match Puzzle",
        "core_loop": "Match 3+ adjacent blocks of same color to score",
        "controls": "Click/tap blocks to select and match",
        "mechanics": ["matching", "grid", "score", "cascading", "combo"],
        "complexity": "medium",
        "mobile_fit": "excellent",
        "tags": ["puzzle", "match-3", "casual", "strategy"],
        "files": [
            {
                "file_path": "index.html",
                "file_type": "text/html",
                "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Color Match Puzzle</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        canvas {
            display: block;
            margin: auto;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <script>
        const config = {
            type: Phaser.AUTO,
            width: 600,
            height: 800,
            backgroundColor: '#2c3e50',
            scene: {
                create: create,
                update: update
            },
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }
        };

        const game = new Phaser.Game(config);
        const GRID_SIZE = 8;
        const BLOCK_SIZE = 60;
        const COLORS = [0xFF6B6B, 0x4ECDC4, 0xFFE66D, 0x95E1D3, 0xF38181, 0xAA96DA];
        let grid = [];
        let selectedBlocks = [];
        let score = 0, moves = 30, scoreText, movesText;
        let gameOver = false;

        function create() {
            // Title
            this.add.text(300, 40, 'Color Match', {
                fontSize: '40px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5);

            // Instructions
            this.add.text(300, 90, 'Click same-colored adjacent blocks!', {
                fontSize: '18px',
                fill: '#fff'
            }).setOrigin(0.5);

            // UI
            scoreText = this.add.text(50, 130, 'Score: 0', {
                fontSize: '24px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 3
            });

            movesText = this.add.text(450, 130, 'Moves: 30', {
                fontSize: '24px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 3
            });

            // Create grid
            const startX = 60;
            const startY = 180;

            for (let row = 0; row < GRID_SIZE; row++) {
                grid[row] = [];
                for (let col = 0; col < GRID_SIZE; col++) {
                    const x = startX + col * (BLOCK_SIZE + 5);
                    const y = startY + row * (BLOCK_SIZE + 5);
                    const color = Phaser.Utils.Array.GetRandom(COLORS);

                    const block = this.add.rectangle(x, y, BLOCK_SIZE, BLOCK_SIZE, color);
                    block.setStroke(0xffffff, 2);
                    block.setInteractive();
                    block.row = row;
                    block.col = col;
                    block.color = color;
                    block.selected = false;

                    block.on('pointerdown', () => selectBlock.call(this, block));

                    grid[row][col] = block;
                }
            }

            // Submit button
            const submitBtn = this.add.rectangle(300, 720, 200, 60, 0x27ae60);
            submitBtn.setStroke(0xffffff, 3);
            submitBtn.setInteractive();

            const submitText = this.add.text(300, 720, 'MATCH!', {
                fontSize: '28px',
                fill: '#fff',
                fontStyle: 'bold'
            }).setOrigin(0.5);

            submitBtn.on('pointerdown', () => matchBlocks.call(this));

            submitBtn.on('pointerover', () => {
                submitBtn.setFillStyle(0x2ecc71);
            });

            submitBtn.on('pointerout', () => {
                submitBtn.setFillStyle(0x27ae60);
            });
        }

        function update() {
            // Game loop
        }

        function selectBlock(block) {
            if (gameOver) return;

            if (block.selected) {
                // Deselect
                block.selected = false;
                block.setStroke(0xffffff, 2);
                selectedBlocks = selectedBlocks.filter(b => b !== block);

                // Remove all blocks after this one
                const index = selectedBlocks.indexOf(block);
                if (index !== -1) {
                    for (let i = selectedBlocks.length - 1; i > index; i--) {
                        selectedBlocks[i].selected = false;
                        selectedBlocks[i].setStroke(0xffffff, 2);
                    }
                    selectedBlocks = selectedBlocks.slice(0, index + 1);
                }
            } else {
                // Check if can select
                if (selectedBlocks.length === 0) {
                    // First block
                    block.selected = true;
                    block.setStroke(0xFFFF00, 4);
                    selectedBlocks.push(block);
                } else {
                    // Must be adjacent and same color
                    const lastBlock = selectedBlocks[selectedBlocks.length - 1];
                    const isAdjacent =
                        (Math.abs(block.row - lastBlock.row) === 1 && block.col === lastBlock.col) ||
                        (Math.abs(block.col - lastBlock.col) === 1 && block.row === lastBlock.row);

                    if (isAdjacent && block.color === lastBlock.color && !selectedBlocks.includes(block)) {
                        block.selected = true;
                        block.setStroke(0xFFFF00, 4);
                        selectedBlocks.push(block);
                    }
                }
            }
        }

        function matchBlocks() {
            if (gameOver) return;
            if (selectedBlocks.length < 3) {
                // Need at least 3
                clearSelection.call(this);
                return;
            }

            moves--;
            movesText.setText('Moves: ' + moves);

            // Calculate score
            const points = selectedBlocks.length * 10 * selectedBlocks.length;
            score += points;
            scoreText.setText('Score: ' + score);

            // Show points
            const avgX = selectedBlocks.reduce((sum, b) => sum + b.x, 0) / selectedBlocks.length;
            const avgY = selectedBlocks.reduce((sum, b) => sum + b.y, 0) / selectedBlocks.length;

            const pointsText = this.add.text(avgX, avgY, '+' + points, {
                fontSize: '32px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5);

            this.tweens.add({
                targets: pointsText,
                y: avgY - 50,
                alpha: 0,
                duration: 1000,
                onComplete: () => pointsText.destroy()
            });

            // Animate removal
            selectedBlocks.forEach(block => {
                this.tweens.add({
                    targets: block,
                    scaleX: 0,
                    scaleY: 0,
                    alpha: 0,
                    duration: 300,
                    onComplete: () => {
                        block.destroy();
                    }
                });
            });

            // Refill after delay
            this.time.delayedCall(400, () => {
                refillGrid.call(this);
            });

            selectedBlocks = [];

            // Check game over
            if (moves <= 0) {
                gameOver = true;
                this.time.delayedCall(500, () => {
                    this.add.rectangle(300, 400, 500, 300, 0x000000, 0.8);
                    this.add.text(300, 350, 'GAME OVER!', {
                        fontSize: '48px',
                        fill: '#fff',
                        stroke: '#000',
                        strokeThickness: 6
                    }).setOrigin(0.5);
                    this.add.text(300, 420, 'Final Score: ' + score, {
                        fontSize: '36px',
                        fill: '#FFD700',
                        stroke: '#000',
                        strokeThickness: 4
                    }).setOrigin(0.5);
                });
            }
        }

        function clearSelection() {
            selectedBlocks.forEach(block => {
                if (block.active) {
                    block.selected = false;
                    block.setStroke(0xffffff, 2);
                }
            });
            selectedBlocks = [];
        }

        function refillGrid() {
            const startY = 180;

            for (let col = 0; col < GRID_SIZE; col++) {
                // Find empty spots
                let emptyCount = 0;
                for (let row = GRID_SIZE - 1; row >= 0; row--) {
                    if (!grid[row][col].active) {
                        emptyCount++;
                    }
                }

                // Create new blocks
                for (let i = 0; i < emptyCount; i++) {
                    const row = i;
                    const x = 60 + col * (BLOCK_SIZE + 5);
                    const y = startY - (emptyCount - i) * (BLOCK_SIZE + 5);
                    const color = Phaser.Utils.Array.GetRandom(COLORS);

                    const block = this.add.rectangle(x, y, BLOCK_SIZE, BLOCK_SIZE, color);
                    block.setStroke(0xffffff, 2);
                    block.setInteractive();
                    block.row = row;
                    block.col = col;
                    block.color = color;
                    block.selected = false;

                    block.on('pointerdown', () => selectBlock.call(this, block));

                    grid[row][col] = block;

                    // Animate drop
                    const targetY = startY + row * (BLOCK_SIZE + 5);
                    this.tweens.add({
                        targets: block,
                        y: targetY,
                        duration: 400,
                        ease: 'Bounce.easeOut'
                    });
                }

                // Shift down existing blocks
                let writeRow = GRID_SIZE - 1;
                for (let row = GRID_SIZE - 1; row >= 0; row--) {
                    if (grid[row][col].active && grid[row][col] !== grid[writeRow][col]) {
                        const block = grid[row][col];
                        grid[writeRow][col] = block;
                        block.row = writeRow;

                        const targetY = startY + writeRow * (BLOCK_SIZE + 5);
                        this.tweens.add({
                            targets: block,
                            y: targetY,
                            duration: 300,
                            ease: 'Cubic.easeOut'
                        });

                        writeRow--;
                    }
                }
            }
        }
    </script>
</body>
</html>"""
            }
        ]
    },
    {
        "template_id": "runner_endless",
        "title": "Endless Runner",
        "core_loop": "Auto-run and jump over obstacles, survive as long as possible",
        "controls": "Space or Click/Tap to jump",
        "mechanics": ["auto-scrolling", "jumping", "obstacles", "score", "speed-increase"],
        "complexity": "simple",
        "mobile_fit": "excellent",
        "tags": ["action", "runner", "endless", "arcade", "single-button"],
        "files": [
            {
                "file_path": "index.html",
                "file_type": "text/html",
                "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Endless Runner</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(to bottom, #87CEEB 0%, #98D8C8 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        canvas {
            display: block;
            margin: auto;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <script>
        const config = {
            type: Phaser.AUTO,
            width: 800,
            height: 400,
            backgroundColor: '#87CEEB',
            physics: {
                default: 'arcade',
                arcade: {
                    gravity: { y: 1200 },
                    debug: false
                }
            },
            scene: {
                create: create,
                update: update
            },
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }
        };

        const game = new Phaser.Game(config);
        let player, obstacles, ground, scoreText, highScoreText;
        let score = 0, highScore = 0, gameOver = false;
        let gameSpeed = 300, obstacleTimer = 0, obstacleDelay = 1500;
        let isJumping = false;

        function create() {
            // Ground
            ground = this.add.rectangle(400, 370, 800, 60, 0x2d572c);
            this.physics.add.existing(ground, true);

            // Player
            player = this.add.rectangle(100, 300, 40, 50, 0xFF6B6B);
            this.physics.add.existing(player);
            player.body.setCollideWorldBounds(true);
            this.physics.add.collider(player, ground);

            // Obstacles group
            obstacles = this.physics.add.group();

            // Collision
            this.physics.add.overlap(player, obstacles, hitObstacle, null, this);

            // Input
            this.input.keyboard.on('keydown-SPACE', () => jump());
            this.input.on('pointerdown', () => jump());

            // UI
            scoreText = this.add.text(16, 16, 'Score: 0', {
                fontSize: '28px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 4
            });

            highScoreText = this.add.text(400, 16, 'Best: 0', {
                fontSize: '24px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 3
            }).setOrigin(0.5, 0);

            // Instructions
            const instructions = this.add.text(400, 200, 'TAP or PRESS SPACE to JUMP!', {
                fontSize: '32px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 5
            }).setOrigin(0.5);

            this.tweens.add({
                targets: instructions,
                alpha: 0,
                duration: 3000,
                delay: 1000
            });

            // Add clouds for atmosphere
            for (let i = 0; i < 5; i++) {
                const cloud = this.add.ellipse(
                    Phaser.Math.Between(0, 800),
                    Phaser.Math.Between(50, 150),
                    Phaser.Math.Between(60, 100),
                    40,
                    0xffffff,
                    0.7
                );

                this.tweens.add({
                    targets: cloud,
                    x: cloud.x + 1000,
                    duration: Phaser.Math.Between(20000, 40000),
                    repeat: -1
                });
            }
        }

        function update(time, delta) {
            if (gameOver) return;

            // Increment score
            score += delta * 0.01;
            scoreText.setText('Score: ' + Math.floor(score));

            // Increase difficulty
            gameSpeed = 300 + (score * 0.5);
            obstacleDelay = Math.max(800, 1500 - score);

            // Spawn obstacles
            obstacleTimer += delta;
            if (obstacleTimer > obstacleDelay) {
                spawnObstacle.call(this);
                obstacleTimer = 0;
            }

            // Move obstacles
            obstacles.children.entries.forEach(obstacle => {
                obstacle.x -= gameSpeed * (delta / 1000);

                if (obstacle.x < -50) {
                    obstacle.destroy();
                }
            });

            // Check if player landed
            if (player.body.touching.down) {
                isJumping = false;
            }
        }

        function jump() {
            if (gameOver) return;

            if (player.body.touching.down && !isJumping) {
                player.body.setVelocityY(-550);
                isJumping = true;
            }
        }

        function spawnObstacle() {
            const type = Phaser.Math.Between(0, 2);
            let obstacle;

            if (type === 0) {
                // Single block
                obstacle = this.add.rectangle(850, 330, 30, 40, 0x8B4513);
            } else if (type === 1) {
                // Tall block
                obstacle = this.add.rectangle(850, 310, 30, 60, 0x654321);
            } else {
                // Wide block
                obstacle = this.add.rectangle(850, 335, 50, 30, 0xA0522D);
            }

            this.physics.add.existing(obstacle);
            obstacle.body.setAllowGravity(false);
            obstacle.body.setImmovable(true);
            obstacles.add(obstacle);
        }

        function hitObstacle(player, obstacle) {
            gameOver = true;

            // Stop player
            player.body.setVelocity(0, 0);
            player.setTint(0xff0000);

            // Update high score
            const finalScore = Math.floor(score);
            if (finalScore > highScore) {
                highScore = finalScore;
                highScoreText.setText('Best: ' + highScore);
            }

            // Game over screen
            const gameOverBg = this.add.rectangle(400, 200, 600, 250, 0x000000, 0.8);

            const gameOverText = this.add.text(400, 150, 'GAME OVER!', {
                fontSize: '56px',
                fill: '#ff0000',
                stroke: '#000',
                strokeThickness: 6
            }).setOrigin(0.5);

            const finalScoreText = this.add.text(400, 220, 'Score: ' + finalScore, {
                fontSize: '36px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5);

            const restartText = this.add.text(400, 280, 'Tap to Restart', {
                fontSize: '28px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 3
            }).setOrigin(0.5);

            // Blink restart text
            this.tweens.add({
                targets: restartText,
                alpha: 0.3,
                duration: 500,
                yoyo: true,
                repeat: -1
            });

            // Restart on click
            this.input.once('pointerdown', () => {
                this.scene.restart();
                resetGame();
            });

            this.input.keyboard.once('keydown-SPACE', () => {
                this.scene.restart();
                resetGame();
            });
        }

        function resetGame() {
            score = 0;
            gameOver = false;
            gameSpeed = 300;
            obstacleTimer = 0;
            isJumping = false;
        }
    </script>
</body>
</html>"""
            }
        ]
    },
    {
        "template_id": "clicker_idle",
        "title": "Idle Clicker",
        "core_loop": "Click to earn points, buy upgrades for passive income",
        "controls": "Click/Tap to earn, purchase upgrades",
        "mechanics": ["clicking", "currency", "upgrades", "idle-income", "economy"],
        "complexity": "simple",
        "mobile_fit": "excellent",
        "tags": ["idle", "clicker", "incremental", "casual", "strategy"],
        "files": [
            {
                "file_path": "index.html",
                "file_type": "text/html",
                "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Idle Clicker</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        canvas {
            display: block;
            margin: auto;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <script>
        const config = {
            type: Phaser.AUTO,
            width: 600,
            height: 800,
            backgroundColor: '#2c3e50',
            scene: {
                create: create,
                update: update
            },
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }
        };

        const game = new Phaser.Game(config);
        let coins = 0, coinsPerClick = 1, coinsPerSecond = 0;
        let coinText, cpsText, clickButton;
        let upgrades = [];
        let lastUpdate = 0;

        const UPGRADES = [
            { id: 'auto1', name: 'Auto Miner', baseCost: 10, cps: 1, owned: 0, costMult: 1.15 },
            { id: 'auto2', name: 'Factory', baseCost: 100, cps: 5, owned: 0, costMult: 1.15 },
            { id: 'auto3', name: 'Robot', baseCost: 500, cps: 25, owned: 0, costMult: 1.15 },
            { id: 'click1', name: 'Better Pick', baseCost: 25, clickBonus: 1, owned: 0, costMult: 1.2 },
            { id: 'click2', name: 'Power Drill', baseCost: 200, clickBonus: 5, owned: 0, costMult: 1.2 },
        ];

        function create() {
            // Title
            this.add.text(300, 30, 'COIN CLICKER', {
                fontSize: '42px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 5
            }).setOrigin(0.5);

            // Coin display
            coinText = this.add.text(300, 90, '0', {
                fontSize: '48px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5);

            this.add.text(300, 130, 'coins', {
                fontSize: '24px',
                fill: '#fff'
            }).setOrigin(0.5);

            // CPS display
            cpsText = this.add.text(300, 165, 'Per second: 0', {
                fontSize: '20px',
                fill: '#4ECDC4'
            }).setOrigin(0.5);

            // Click button
            clickButton = this.add.circle(300, 300, 80, 0xFFD700);
            clickButton.setStroke(0xFFA500, 6);
            clickButton.setInteractive();

            this.add.text(300, 300, 'CLICK', {
                fontSize: '32px',
                fill: '#000',
                fontStyle: 'bold'
            }).setOrigin(0.5);

            clickButton.on('pointerdown', () => {
                coins += coinsPerClick;
                updateDisplay();

                // Animate click
                this.tweens.add({
                    targets: clickButton,
                    scaleX: 0.9,
                    scaleY: 0.9,
                    duration: 100,
                    yoyo: true
                });

                // Show +coins text
                const plusText = this.add.text(300, 250, '+' + coinsPerClick, {
                    fontSize: '28px',
                    fill: '#FFD700',
                    stroke: '#000',
                    strokeThickness: 3
                }).setOrigin(0.5);

                this.tweens.add({
                    targets: plusText,
                    y: 200,
                    alpha: 0,
                    duration: 800,
                    onComplete: () => plusText.destroy()
                });
            });

            // Upgrades section
            this.add.text(300, 420, 'UPGRADES', {
                fontSize: '28px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 3
            }).setOrigin(0.5);

            // Create upgrade buttons
            let yPos = 470;
            UPGRADES.forEach((upgrade, index) => {
                createUpgradeButton.call(this, upgrade, yPos);
                yPos += 65;
            });
        }

        function update(time) {
            // Passive income
            if (lastUpdate === 0) {
                lastUpdate = time;
            }

            const delta = time - lastUpdate;
            if (delta >= 1000) {
                coins += coinsPerSecond;
                updateDisplay();
                lastUpdate = time;
            }
        }

        function createUpgradeButton(upgrade, yPos) {
            const bg = this.add.rectangle(300, yPos, 560, 55, 0x34495e);
            bg.setStroke(0x7f8c8d, 2);
            bg.setInteractive();

            const nameText = this.add.text(30, yPos, upgrade.name, {
                fontSize: '20px',
                fill: '#fff',
                fontStyle: 'bold'
            }).setOrigin(0, 0.5);

            const infoText = this.add.text(30, yPos + 20,
                upgrade.cps ? `+${upgrade.cps}/sec` : `+${upgrade.clickBonus}/click`, {
                fontSize: '14px',
                fill: '#95a5a6'
            }).setOrigin(0, 0.5);

            const costText = this.add.text(550, yPos, getCost(upgrade) + ' coins', {
                fontSize: '18px',
                fill: '#FFD700'
            }).setOrigin(1, 0.5);

            const ownedText = this.add.text(30, yPos - 20, 'Owned: 0', {
                fontSize: '14px',
                fill: '#4ECDC4'
            }).setOrigin(0, 0.5);

            bg.on('pointerdown', () => {
                const cost = getCost(upgrade);
                if (coins >= cost) {
                    coins -= cost;
                    upgrade.owned++;

                    if (upgrade.cps) {
                        coinsPerSecond += upgrade.cps;
                    } else if (upgrade.clickBonus) {
                        coinsPerClick += upgrade.clickBonus;
                    }

                    updateDisplay();
                    costText.setText(getCost(upgrade) + ' coins');
                    ownedText.setText('Owned: ' + upgrade.owned);

                    // Flash effect
                    this.tweens.add({
                        targets: bg,
                        alpha: 0.5,
                        duration: 100,
                        yoyo: true
                    });
                } else {
                    // Shake effect when can't afford
                    this.tweens.add({
                        targets: [bg, nameText, infoText, costText, ownedText],
                        x: '+=5',
                        duration: 50,
                        yoyo: true,
                        repeat: 2
                    });
                }
            });

            bg.on('pointerover', () => {
                bg.setFillStyle(0x3d566e);
            });

            bg.on('pointerout', () => {
                bg.setFillStyle(0x34495e);
            });

            upgrade.ui = { bg, nameText, infoText, costText, ownedText };
        }

        function getCost(upgrade) {
            return Math.floor(upgrade.baseCost * Math.pow(upgrade.costMult, upgrade.owned));
        }

        function updateDisplay() {
            coinText.setText(formatNumber(coins));
            cpsText.setText('Per second: ' + formatNumber(coinsPerSecond));
        }

        function formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(2) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return Math.floor(num).toString();
        }
    </script>
</body>
</html>"""
            }
        ]
    },
    {
        "template_id": "defense_tower",
        "title": "Tower Defense",
        "core_loop": "Place towers to stop enemies from reaching the end",
        "controls": "Click/Tap to place towers along the path",
        "mechanics": ["tower-placement", "waves", "enemies", "path", "strategy"],
        "complexity": "medium",
        "mobile_fit": "good",
        "tags": ["strategy", "tower-defense", "wave-based", "tactical"],
        "files": [
            {
                "file_path": "index.html",
                "file_type": "text/html",
                "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Tower Defense</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.60.0/dist/phaser.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #1a1a1a;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        canvas {
            display: block;
            margin: auto;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <script>
        const config = {
            type: Phaser.AUTO,
            width: 800,
            height: 600,
            backgroundColor: '#2d5016',
            physics: {
                default: 'arcade',
                arcade: { debug: false }
            },
            scene: {
                create: create,
                update: update
            },
            scale: {
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }
        };

        const game = new Phaser.Game(config);

        // Game state
        let towers = [], enemies = [], bullets = [];
        let money = 150, lives = 20, wave = 1;
        let moneyText, livesText, waveText;
        let enemySpawnTimer = 0, enemiesThisWave = 5, enemiesSpawned = 0;
        let waveActive = false, gameOver = false;

        // Path waypoints
        const path = [
            { x: 0, y: 150 },
            { x: 300, y: 150 },
            { x: 300, y: 400 },
            { x: 600, y: 400 },
            { x: 600, y: 100 },
            { x: 850, y: 100 }
        ];

        function create() {
            // Draw path
            const graphics = this.add.graphics();
            graphics.lineStyle(50, 0x8B7355, 1);
            graphics.beginPath();
            graphics.moveTo(path[0].x, path[0].y);
            for (let i = 1; i < path.length; i++) {
                graphics.lineTo(path[i].x, path[i].y);
            }
            graphics.strokePath();

            // UI
            moneyText = this.add.text(16, 16, 'Money: $150', {
                fontSize: '24px',
                fill: '#FFD700',
                stroke: '#000',
                strokeThickness: 3
            });

            livesText = this.add.text(16, 50, 'Lives: 20', {
                fontSize: '24px',
                fill: '#FF6B6B',
                stroke: '#000',
                strokeThickness: 3
            });

            waveText = this.add.text(400, 16, 'Wave 1', {
                fontSize: '28px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5, 0);

            // Tower placement button
            const towerBtn = this.add.rectangle(700, 30, 180, 50, 0x4ECDC4);
            towerBtn.setStroke(0xffffff, 3);
            towerBtn.setInteractive();

            this.add.text(700, 30, 'Place Tower ($50)', {
                fontSize: '18px',
                fill: '#000',
                fontStyle: 'bold'
            }).setOrigin(0.5);

            towerBtn.on('pointerdown', () => {
                if (money >= 50) {
                    placementMode = true;
                }
            });

            // Start wave button
            const startBtn = this.add.rectangle(700, 90, 180, 50, 0x27ae60);
            startBtn.setStroke(0xffffff, 3);
            startBtn.setInteractive();

            this.add.text(700, 90, 'Start Wave', {
                fontSize: '20px',
                fill: '#fff',
                fontStyle: 'bold'
            }).setOrigin(0.5);

            startBtn.on('pointerdown', () => {
                if (!waveActive && !gameOver) {
                    startWave.call(this);
                }
            });

            // Tower placement
            let placementMode = false;
            this.input.on('pointerdown', (pointer) => {
                if (placementMode && pointer.x < 650 && money >= 50) {
                    placeTower.call(this, pointer.x, pointer.y);
                    money -= 50;
                    moneyText.setText('Money: $' + money);
                    placementMode = false;
                }
            });

            // Instructions
            this.add.text(400, 550, 'Place towers, then start the wave!', {
                fontSize: '20px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 3
            }).setOrigin(0.5);
        }

        function update(time, delta) {
            if (gameOver) return;

            // Spawn enemies
            if (waveActive && enemiesSpawned < enemiesThisWave) {
                enemySpawnTimer += delta;
                if (enemySpawnTimer > 1000) {
                    spawnEnemy.call(this);
                    enemiesSpawned++;
                    enemySpawnTimer = 0;
                }
            }

            // Move enemies along path
            enemies.forEach(enemy => {
                if (!enemy.active) return;

                const target = path[enemy.pathIndex];
                const distance = Phaser.Math.Distance.Between(enemy.x, enemy.y, target.x, target.y);

                if (distance < 5) {
                    enemy.pathIndex++;
                    if (enemy.pathIndex >= path.length) {
                        // Enemy reached end
                        enemy.destroy();
                        lives--;
                        livesText.setText('Lives: ' + lives);

                        if (lives <= 0) {
                            endGame.call(this, false);
                        }
                    }
                } else {
                    this.physics.moveToObject(enemy, target, 80 + (wave * 5));
                }
            });

            // Tower shooting
            towers.forEach(tower => {
                tower.cooldown -= delta;

                if (tower.cooldown <= 0) {
                    // Find closest enemy in range
                    let closestEnemy = null;
                    let closestDist = tower.range;

                    enemies.forEach(enemy => {
                        if (!enemy.active) return;
                        const dist = Phaser.Math.Distance.Between(tower.x, tower.y, enemy.x, enemy.y);
                        if (dist < closestDist) {
                            closestDist = dist;
                            closestEnemy = enemy;
                        }
                    });

                    if (closestEnemy) {
                        shootBullet.call(this, tower, closestEnemy);
                        tower.cooldown = 500;
                    }
                }
            });

            // Move bullets
            bullets.forEach(bullet => {
                if (!bullet.active || !bullet.target.active) {
                    bullet.destroy();
                    return;
                }

                this.physics.moveToObject(bullet, bullet.target, 400);

                const dist = Phaser.Math.Distance.Between(bullet.x, bullet.y, bullet.target.x, bullet.target.y);
                if (dist < 10) {
                    // Hit enemy
                    bullet.target.health -= bullet.damage;

                    if (bullet.target.health <= 0) {
                        bullet.target.destroy();
                        money += 15;
                        moneyText.setText('Money: $' + money);
                    }

                    bullet.destroy();
                }
            });

            // Clean up destroyed objects
            enemies = enemies.filter(e => e.active);
            bullets = bullets.filter(b => b.active);

            // Check wave completion
            if (waveActive && enemiesSpawned >= enemiesThisWave && enemies.length === 0) {
                waveActive = false;
                wave++;
                enemiesThisWave = 5 + (wave * 3);
                enemiesSpawned = 0;

                waveText.setText('Wave ' + wave + ' Ready!');

                // Bonus money
                money += 50;
                moneyText.setText('Money: $' + money);
            }
        }

        function placeTower(x, y) {
            const tower = this.add.rectangle(x, y, 30, 30, 0x4ECDC4);
            tower.setStroke(0x2c3e50, 3);

            // Range indicator
            const rangeCircle = this.add.circle(x, y, 100, 0x4ECDC4, 0.1);
            rangeCircle.setStroke(0x4ECDC4, 1);

            tower.range = 100;
            tower.cooldown = 0;
            tower.damage = 25;

            towers.push(tower);
        }

        function spawnEnemy() {
            const enemy = this.add.rectangle(path[0].x, path[0].y, 25, 25, 0xFF0055);
            this.physics.add.existing(enemy);
            enemy.body.setAllowGravity(false);

            enemy.pathIndex = 1;
            enemy.health = 50 + (wave * 10);
            enemy.maxHealth = enemy.health;

            // Health bar
            const healthBg = this.add.rectangle(enemy.x, enemy.y - 20, 30, 4, 0x000000);
            const healthBar = this.add.rectangle(enemy.x, enemy.y - 20, 30, 4, 0x00ff00);

            enemy.healthBar = healthBar;
            enemy.healthBg = healthBg;

            // Update health bar
            const originalUpdate = enemy.preUpdate;
            enemy.preUpdate = function() {
                if (originalUpdate) originalUpdate.call(this);
                if (this.healthBar && this.healthBar.active) {
                    this.healthBar.x = this.x;
                    this.healthBar.y = this.y - 20;
                    this.healthBg.x = this.x;
                    this.healthBg.y = this.y - 20;

                    const healthPercent = this.health / this.maxHealth;
                    this.healthBar.width = 30 * healthPercent;

                    if (healthPercent < 0.3) {
                        this.healthBar.setFillStyle(0xff0000);
                    } else if (healthPercent < 0.6) {
                        this.healthBar.setFillStyle(0xffff00);
                    }
                }
            };

            enemies.push(enemy);
        }

        function shootBullet(tower, target) {
            const bullet = this.add.circle(tower.x, tower.y, 5, 0xFFFF00);
            this.physics.add.existing(bullet);
            bullet.body.setAllowGravity(false);

            bullet.target = target;
            bullet.damage = tower.damage;

            bullets.push(bullet);
        }

        function startWave() {
            waveActive = true;
            enemySpawnTimer = 0;
            waveText.setText('Wave ' + wave);
        }

        function endGame(won) {
            gameOver = true;

            const bg = this.add.rectangle(400, 300, 600, 300, 0x000000, 0.9);

            const title = this.add.text(400, 250, won ? 'VICTORY!' : 'GAME OVER', {
                fontSize: '56px',
                fill: won ? '#FFD700' : '#FF0055',
                stroke: '#000',
                strokeThickness: 6
            }).setOrigin(0.5);

            this.add.text(400, 330, 'Wave Reached: ' + wave, {
                fontSize: '32px',
                fill: '#fff',
                stroke: '#000',
                strokeThickness: 4
            }).setOrigin(0.5);
        }
    </script>
</body>
</html>"""
            }
        ]
    }
]
