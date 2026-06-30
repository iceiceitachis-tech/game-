from flask import Flask, render_template_string

app = Flask(__name__)

HTML_CONTENT = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { margin: 0; overflow: hidden; background: #222; }
        canvas { display: block; touch-action: none; background: #f0f0f0; }
    </style>
</head>
<body>
    <canvas id="gameCanvas"></canvas>
    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const imgUrl = "https://i.postimg.cc/T3WKvx3N/Messenger-creation-1550069093148263.jpg";
        const img = new Image();
        img.src = imgUrl;

        let targets = [spawnTarget(), spawnTarget(), spawnTarget()];
        let gameOver = false;

        function spawnTarget() {
            return {
                x: Math.random() * (canvas.width - 80),
                y: -100,
                size: 80,
                speed: 3 + Math.random() * 2
            };
        }

        function draw() {
            if (gameOver) {
                ctx.fillStyle = "black";
                ctx.font = "40px Arial";
                ctx.fillText("GAME OVER", canvas.width/2 - 110, canvas.height/2);
                return;
            }
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            targets.forEach((t, index) => {
                ctx.drawImage(img, t.x, t.y, t.size, t.size);
                t.y += t.speed;
                if (t.y > canvas.height) { gameOver = true; }
            });
            requestAnimationFrame(draw);
        }

        canvas.addEventListener("touchstart", (e) => {
            const touch = e.touches[0];
            const mx = touch.clientX;
            const my = touch.clientY;
            targets.forEach((t, index) => {
                if (mx > t.x && mx < t.x + t.size && my > t.y && my < t.y + t.size) {
                    targets[index] = spawnTarget();
                }
            });
        });
        draw();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    # เปลี่ยนพอร์ตเป็น 8080 สำหรับ Replit
    app.run(host='0.0.0.0', port=8080)
