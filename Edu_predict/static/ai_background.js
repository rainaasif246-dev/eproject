(function () {
    if (document.getElementById('ai-network-bg')) {
        return;
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    var canvas = document.createElement('canvas');
    canvas.id = 'ai-network-bg';
    canvas.setAttribute('aria-hidden', 'true');
    document.body.prepend(canvas);

    var context = canvas.getContext('2d');
    var width = 0;
    var height = 0;
    var nodes = [];
    var frame = 0;

    function resize() {
        var ratio = Math.min(window.devicePixelRatio || 1, 1.5);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width * ratio;
        canvas.height = height * ratio;
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
        var targetCount = Math.max(16, Math.min(28, Math.round(width / 30)));
        nodes = Array.from({ length: targetCount }, function (_, index) {
            return {
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.18,
                vy: (Math.random() - 0.5) * 0.18,
                size: 1 + (index % 3) * 0.6,
                phase: Math.random() * Math.PI * 2
            };
        });
    }

    function draw() {
        frame += 1;
        context.clearRect(0, 0, width, height);
        var glow = context.createRadialGradient(width * 0.72, height * 0.35, 0, width * 0.72, height * 0.35, width * 0.55);
        glow.addColorStop(0, 'rgba(34, 211, 238, 0.08)');
        glow.addColorStop(0.45, 'rgba(99, 102, 241, 0.03)');
        glow.addColorStop(1, 'rgba(6, 18, 31, 0)');
        context.fillStyle = glow;
        context.fillRect(0, 0, width, height);

        nodes.forEach(function (node) {
            node.x += node.vx;
            node.y += node.vy;
            if (node.x < -20) node.x = width + 20;
            if (node.x > width + 20) node.x = -20;
            if (node.y < -20) node.y = height + 20;
            if (node.y > height + 20) node.y = -20;
        });

        context.lineWidth = 0.7;
        nodes.forEach(function (node, index) {
            nodes.slice(index + 1).forEach(function (other) {
                var dx = node.x - other.x;
                var dy = node.y - other.y;
                var distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 120) {
                    context.strokeStyle = 'rgba(34, 211, 238, ' + (0.12 * (1 - distance / 120)) + ')';
                    context.beginPath();
                    context.moveTo(node.x, node.y);
                    context.lineTo(other.x, other.y);
                    context.stroke();
                }
            });
        });

        nodes.forEach(function (node, index) {
            var pulse = 0.65 + Math.sin(frame * 0.02 + node.phase) * 0.18;
            context.beginPath();
            context.fillStyle = index % 4 === 0 ? 'rgba(167, 139, 250, ' + pulse + ')' : 'rgba(34, 211, 238, ' + pulse + ')';
            context.shadowBlur = 8;
            context.shadowColor = context.fillStyle;
            context.arc(node.x, node.y, node.size, 0, Math.PI * 2);
            context.fill();
        });
        context.shadowBlur = 0;
        window.requestAnimationFrame(draw);
    }

    resize();
    window.addEventListener('resize', resize);
    draw();
}());
