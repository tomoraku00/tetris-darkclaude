// ===== Tetris Game in Pure JavaScript =====

const COLS = 10;
const ROWS = 20;
const BLOCK = 24;
const COLORS = {
    I: '#00f0f0',
    O: '#f0f000',
    T: '#a000f0',
    S: '#00f000',
    Z: '#f00000',
    J: '#0000f0',
    L: '#f0a000'
};

const SHAPES = {
    I: [[0,0],[1,0],[2,0],[3,0]],
    O: [[0,0],[1,0],[0,1],[1,1]],
    T: [[0,0],[1,0],[2,0],[1,1]],
    S: [[1,0],[2,0],[0,1],[1,1]],
    Z: [[0,0],[1,0],[1,1],[2,1]],
    J: [[0,0],[0,1],[1,1],[2,1]],
    L: [[2,0],[0,1],[1,1],[2,1]]
};

const PIECE_NAMES = ['I','O','T','S','Z','J','L'];

let canvas, ctx, nextCanvas, nextCtx;
let board, currentPiece, nextPiece;
let score, level, lines, gameRunning, paused, gameOver;
let dropInterval, lastDrop, animationId;
let lockDelay = 0;
const LOCK_DELAY = 500;

function init() {
    canvas = document.getElementById('gameCanvas');
    ctx = canvas.getContext('2d');
    nextCanvas = document.getElementById('nextCanvas');
    nextCtx = nextCanvas.getContext('2d');
    
    score = 0;
    level = 1;
    lines = 0;
    gameRunning = true;
    paused = false;
    gameOver = false;
    dropInterval = 1000;
    lastDrop = 0;
    lockDelay = 0;
    
    board = Array.from({length: ROWS}, () => Array(COLS).fill(null));
    
    nextPiece = createRandomPiece();
    spawnPiece();
    
    document.getElementById('score').textContent = '0';
    document.getElementById('level').textContent = '1';
    document.getElementById('lines').textContent = '0';
    document.getElementById('gameOver').style.display = 'none';
    
    lastDrop = performance.now();
    if (animationId) cancelAnimationFrame(animationId);
    gameLoop(performance.now());
}

function createRandomPiece() {
    const name = PIECE_NAMES[Math.floor(Math.random() * PIECE_NAMES.length)];
    return {
        name,
        blocks: SHAPES[name].map(b => [...b]),
        x: Math.floor(COLS / 2) - 1,
        y: 0,
        rotation: 0
    };
}

function spawnPiece() {
    currentPiece = nextPiece;
    nextPiece = createRandomPiece();
    drawNext();
    
    // Center the piece
    const minX = Math.min(...currentPiece.blocks.map(b => b[0]));
    const maxX = Math.max(...currentPiece.blocks.map(b => b[0]));
    currentPiece.x = Math.floor((COLS - (maxX - minX + 1)) / 2) - minX;
    currentPiece.y = 0;
    
    // Check if spawn position is valid
    if (!isValidPosition(currentPiece.blocks, currentPiece.x, currentPiece.y)) {
        endGame();
    }
}

function isValidPosition(blocks, offX, offY) {
    for (const [bx, by] of blocks) {
        const nx = bx + offX;
        const ny = by + offY;
        if (nx < 0 || nx >= COLS || ny >= ROWS) return false;
        if (ny >= 0 && board[ny][nx]) return false;
    }
    return true;
}

function rotatePiece() {
    const blocks = currentPiece.blocks;
    // Find center of bounding box for rotation
    const minX = Math.min(...blocks.map(b => b[0]));
    const maxX = Math.max(...blocks.map(b => b[0]));
    const minY = Math.min(...blocks.map(b => b[1]));
    const maxY = Math.max(...blocks.map(b => b[1]));
    const cx = minX + (maxX - minX) / 2;
    const cy = minY + (maxY - minY) / 2;
    
    const newBlocks = blocks.map(([x, y]) => [
        Math.round(cy - y + cx),
        Math.round(x - cx + cy)
    ]);
    
    // Wall kick offsets to try
    const kicks = [0, -1, 1, -2, 2];
    for (const kick of kicks) {
        if (isValidPosition(newBlocks, currentPiece.x + kick, currentPiece.y)) {
            currentPiece.blocks = newBlocks;
            currentPiece.x += kick;
            return;
        }
        // Also try upward kick
        if (isValidPosition(newBlocks, currentPiece.x + kick, currentPiece.y - 1)) {
            currentPiece.blocks = newBlocks;
            currentPiece.x += kick;
            currentPiece.y -= 1;
            return;
        }
    }
}

function movePiece(dx, dy) {
    const newX = currentPiece.x + dx;
    const newY = currentPiece.y + dy;
    if (isValidPosition(currentPiece.blocks, newX, newY)) {
        currentPiece.x = newX;
        currentPiece.y = newY;
        if (dy === 0) lockDelay = 0; // Reset lock delay on horizontal move
        return true;
    }
    return false;
}

function hardDrop() {
    while (movePiece(0, 1)) {}
    lockPiece();
}

function lockPiece() {
    for (const [bx, by] of currentPiece.blocks) {
        const nx = bx + currentPiece.x;
        const ny = by + currentPiece.y;
        if (ny >= 0 && ny < ROWS && nx >= 0 && nx < COLS) {
            board[ny][nx] = currentPiece.name;
        }
    }
    
    // Clear completed lines
    let cleared = 0;
    for (let y = ROWS - 1; y >= 0; y--) {
        if (board[y].every(cell => cell !== null)) {
            board.splice(y, 1);
            board.unshift(Array(COLS).fill(null));
            cleared++;
            y++; // Recheck this row
        }
    }
    
    if (cleared > 0) {
        const points = [0, 100, 300, 500, 800];
        score += (points[cleared] || 800) * level;
        lines += cleared;
        level = Math.floor(lines / 10) + 1;
        dropInterval = Math.max(100, 1000 - (level - 1) * 80);
        
        document.getElementById('score').textContent = score;
        document.getElementById('level').textContent = level;
        document.getElementById('lines').textContent = lines;
    }
    
    spawnPiece();
}

function endGame() {
    gameRunning = false;
    gameOver = true;
    if (animationId) cancelAnimationFrame(animationId);
    document.getElementById('finalScore').textContent = score;
    document.getElementById('gameOver').style.display = 'block';
}

function drawBlock(context, x, y, color, size) {
    context.fillStyle = color;
    context.fillRect(x * size, y * size, size, size);
    
    // Highlight
    context.fillStyle = 'rgba(255,255,255,0.3)';
    context.fillRect(x * size, y * size, size, 2);
    context.fillRect(x * size, y * size, 2, size);
    
    // Shadow
    context.fillStyle = 'rgba(0,0,0,0.3)';
    context.fillRect(x * size + size - 2, y * size, 2, size);
    context.fillRect(x * size, y * size + size - 2, size, 2);
    
    // Grid line
    context.strokeStyle = 'rgba(0,0,0,0.5)';
    context.lineWidth = 1;
    context.strokeRect(x * size, y * size, size, size);
}

function drawGhost() {
    if (!currentPiece) return;
    
    let ghostY = currentPiece.y;
    while (isValidPosition(currentPiece.blocks, currentPiece.x, ghostY + 1)) {
        ghostY++;
    }
    
    if (ghostY !== currentPiece.y) {
        ctx.globalAlpha = 0.2;
        for (const [bx, by] of currentPiece.blocks) {
            const nx = bx + currentPiece.x;
            const ny = by + ghostY;
            if (ny >= 0) {
                drawBlock(ctx, nx, ny, COLORS[currentPiece.name], BLOCK);
            }
        }
        ctx.globalAlpha = 1.0;
    }
}

function draw() {
    // Clear board
    ctx.fillStyle = '#0a0a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid lines
    ctx.strokeStyle = 'rgba(74,74,255,0.1)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= COLS; x++) {
        ctx.beginPath();
        ctx.moveTo(x * BLOCK, 0);
        ctx.lineTo(x * BLOCK, ROWS * BLOCK);
        ctx.stroke();
    }
    for (let y = 0; y <= ROWS; y++) {
        ctx.beginPath();
        ctx.moveTo(0, y * BLOCK);
        ctx.lineTo(COLS * BLOCK, y * BLOCK);
        ctx.stroke();
    }
    
    // Draw locked blocks
    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLS; x++) {
            if (board[y][x]) {
                drawBlock(ctx, x, y, COLORS[board[y][x]], BLOCK);
            }
        }
    }
    
    // Draw ghost piece
    drawGhost();
    
    // Draw current piece
    if (currentPiece) {
        for (const [bx, by] of currentPiece.blocks) {
            const nx = bx + currentPiece.x;
            const ny = by + currentPiece.y;
            if (ny >= 0 && ny < ROWS && nx >= 0 && nx < COLS) {
                drawBlock(ctx, nx, ny, COLORS[currentPiece.name], BLOCK);
            }
        }
    }
    
    // Draw pause overlay
    if (paused) {
        ctx.fillStyle = 'rgba(10,10,46,0.8)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#fff';
        ctx.font = '24px Courier New';
        ctx.textAlign = 'center';
        ctx.fillText('PAUSED', canvas.width / 2, canvas.height / 2);
    }
}

function drawNext() {
    nextCtx.fillStyle = '#1a1a3e';
    nextCtx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
    
    if (!nextPiece) return;
    
    // Center the piece in the preview
    const minX = Math.min(...nextPiece.blocks.map(b => b[0]));
    const maxX = Math.max(...nextPiece.blocks.map(b => b[0]));
    const minY = Math.min(...nextPiece.blocks.map(b => b[1]));
    const maxY = Math.max(...nextPiece.blocks.map(b => b[1]));
    
    const pieceW = maxX - minX + 1;
    const pieceH = maxY - minY + 1;
    const offX = Math.floor((4 - pieceW) / 2);
    const offY = Math.floor((4 - pieceH) / 2);
    
    for (const [bx, by] of nextPiece.blocks) {
        drawBlock(nextCtx, bx - minX + offX, by - minY + offY, COLORS[nextPiece.name], 16);
    }
}

function gameLoop(timestamp) {
    if (!gameRunning || gameOver) return;
    
    if (!paused) {
        if (timestamp - lastDrop > dropInterval) {
            if (!movePiece(0, 1)) {
                lockDelay += timestamp - lastDrop;
                if (lockDelay >= LOCK_DELAY) {
                    lockPiece();
                    lockDelay = 0;
                }
            } else {
                lockDelay = 0;
            }
            lastDrop = timestamp;
        }
        
        draw();
    }
    
    animationId = requestAnimationFrame(gameLoop);
}

// Input handling
const keys = {};
let dasTimer = {};
const DAS_DELAY = 170; // Delay before auto-repeat (ms)
const DAS_RATE = 50;   // Auto-repeat interval (ms)

document.addEventListener('keydown', (e) => {
    if (!gameRunning || gameOver) return;
    
    if (e.key === 'p' || e.key === 'P') {
        paused = !paused;
        return;
    }
    
    if (paused) return;
    
    e.preventDefault();
    
    if (keys[e.code]) return; // Prevent key repeat
    keys[e.code] = true;
    
    switch(e.code) {
        case 'ArrowLeft':
            movePiece(-1, 0);
            dasTimer['left'] = { time: performance.now(), active: false };
            break;
        case 'ArrowRight':
            movePiece(1, 0);
            dasTimer['right'] = { time: performance.now(), active: false };
            break;
        case 'ArrowDown':
            if (movePiece(0, 1)) score += 1;
            dasTimer['down'] = { time: performance.now(), active: false };
            document.getElementById('score').textContent = score;
            break;
        case 'ArrowUp':
            rotatePiece();
            break;
        case 'Space':
            hardDrop();
            break;
    }
});

document.addEventListener('keyup', (e) => {
    keys[e.code] = false;
    delete dasTimer[e.code];
});

// DAS (Delayed Auto Shift) handling
setInterval(() => {
    if (!gameRunning || gameOver || paused) return;
    
    const now = performance.now();
    
    if (keys['ArrowLeft'] && dasTimer['left']) {
        const elapsed = now - dasTimer['left'].time;
        if (elapsed >= DAS_DELAY) {
            if (!dasTimer['left'].active) {
                dasTimer['left'].active = true;
                dasTimer['left'].lastRepeat = now;
            } else if (now - dasTimer['left'].lastRepeat >= DAS_RATE) {
                movePiece(-1, 0);
                dasTimer['left'].lastRepeat = now;
            }
        }
    }
    
    if (keys['ArrowRight'] && dasTimer['right']) {
        const elapsed = now - dasTimer['right'].time;
        if (elapsed >= DAS_DELAY) {
            if (!dasTimer['right'].active) {
                dasTimer['right'].active = true;
                dasTimer['right'].lastRepeat = now;
            } else if (now - dasTimer['right'].lastRepeat >= DAS_RATE) {
                movePiece(1, 0);
                dasTimer['right'].lastRepeat = now;
            }
        }
    }
    
    if (keys['ArrowDown'] && dasTimer['down']) {
        const elapsed = now - dasTimer['down'].time;
        if (elapsed >= DAS_DELAY) {
            if (!dasTimer['down'].active) {
                dasTimer['down'].active = true;
                dasTimer['down'].lastRepeat = now;
            } else if (now - dasTimer['down'].lastRepeat >= DAS_RATE) {
                if (movePiece(0, 1)) score += 1;
                document.getElementById('score').textContent = score;
                dasTimer['down'].lastRepeat = now;
            }
        }
    }
}, 16);

// Restart button
document.getElementById('restartBtn').addEventListener('click', init);

// Start the game
init();
