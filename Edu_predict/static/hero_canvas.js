/* ═══════════════════════════════════════════════════════
   EduPredict — Animated Hero Canvas Background
   Simulates: data streams, neural nodes, floating particles
   100% offline, no external dependencies
═══════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');

  /* ── Resize ── */
  function resize() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener('resize', function () { resize(); initAll(); });

  /* ── Color palette ── */
  var CYAN    = 'rgba(34,211,238,';
  var PURPLE  = 'rgba(168,85,247,';
  var TEAL    = 'rgba(20,184,166,';
  var WHITE   = 'rgba(255,255,255,';

  /* ══════════════════════════════════
     1. FLOATING PARTICLES
  ══════════════════════════════════ */
  var particles = [];
  var PARTICLE_COUNT = 90;

  function Particle() {
    this.reset();
  }
  Particle.prototype.reset = function () {
    this.x     = Math.random() * canvas.width;
    this.y     = Math.random() * canvas.height;
    this.r     = Math.random() * 2.2 + 0.4;
    this.vx    = (Math.random() - 0.5) * 0.38;
    this.vy    = (Math.random() - 0.5) * 0.38 - 0.12;
    this.alpha = Math.random() * 0.55 + 0.15;
    var roll   = Math.random();
    this.color = roll < 0.45 ? CYAN : roll < 0.75 ? PURPLE : TEAL;
    this.twinkle = Math.random() * Math.PI * 2;
    this.twinkleSpeed = Math.random() * 0.025 + 0.008;
  };
  Particle.prototype.update = function () {
    this.x += this.vx;
    this.y += this.vy;
    this.twinkle += this.twinkleSpeed;
    var a = this.alpha * (0.7 + 0.3 * Math.sin(this.twinkle));
    if (this.x < -10 || this.x > canvas.width + 10 ||
        this.y < -10 || this.y > canvas.height + 10) {
      this.reset();
      this.y = canvas.height + 5;
    }
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fillStyle = this.color + a + ')';
    ctx.fill();
  };

  /* ══════════════════════════════════
     2. NEURAL NETWORK NODES + EDGES
  ══════════════════════════════════ */
  var nodes = [];
  var NODE_COUNT = 28;
  var CONNECTION_DIST = 160;

  function Node() {
    this.x    = Math.random() * canvas.width;
    this.y    = Math.random() * canvas.height;
    this.vx   = (Math.random() - 0.5) * 0.28;
    this.vy   = (Math.random() - 0.5) * 0.28;
    this.r    = Math.random() * 3.5 + 1.5;
    var roll  = Math.random();
    this.color = roll < 0.5 ? CYAN : roll < 0.78 ? PURPLE : TEAL;
    this.pulse = Math.random() * Math.PI * 2;
    this.pulseSpeed = Math.random() * 0.02 + 0.008;
  }
  Node.prototype.update = function () {
    this.x += this.vx;
    this.y += this.vy;
    this.pulse += this.pulseSpeed;
    if (this.x < 0 || this.x > canvas.width)  this.vx *= -1;
    if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
  };

  function drawNodes() {
    /* draw edges */
    for (var i = 0; i < nodes.length; i++) {
      for (var j = i + 1; j < nodes.length; j++) {
        var dx = nodes[i].x - nodes[j].x;
        var dy = nodes[i].y - nodes[j].y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECTION_DIST) {
          var alpha = (1 - dist / CONNECTION_DIST) * 0.18;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = CYAN + alpha + ')';
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }
    /* draw nodes */
    for (var k = 0; k < nodes.length; k++) {
      var n = nodes[k];
      var pAlpha = 0.45 + 0.25 * Math.sin(n.pulse);
      /* glow ring */
      var grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 4);
      grd.addColorStop(0,   n.color + (pAlpha * 0.8) + ')');
      grd.addColorStop(0.5, n.color + (pAlpha * 0.25) + ')');
      grd.addColorStop(1,   n.color + '0)');
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * 4, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
      /* core dot */
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = n.color + pAlpha + ')';
      ctx.fill();
    }
  }

  /* ══════════════════════════════════
     3. DATA STREAM LINES (vertical)
  ══════════════════════════════════ */
  var streams = [];
  var STREAM_COUNT = 18;

  function Stream() {
    this.reset();
  }
  Stream.prototype.reset = function () {
    this.x      = Math.random() * canvas.width;
    this.y      = -Math.random() * canvas.height;
    this.speed  = Math.random() * 1.1 + 0.4;
    this.len    = Math.random() * 120 + 40;
    this.alpha  = Math.random() * 0.18 + 0.06;
    this.width  = Math.random() * 1.2 + 0.4;
    var roll    = Math.random();
    this.color  = roll < 0.6 ? CYAN : roll < 0.85 ? TEAL : PURPLE;
  };
  Stream.prototype.update = function () {
    this.y += this.speed;
    if (this.y - this.len > canvas.height) this.reset();
    var grad = ctx.createLinearGradient(this.x, this.y - this.len, this.x, this.y);
    grad.addColorStop(0,   this.color + '0)');
    grad.addColorStop(0.6, this.color + this.alpha + ')');
    grad.addColorStop(1,   this.color + (this.alpha * 1.8) + ')');
    ctx.beginPath();
    ctx.moveTo(this.x, this.y - this.len);
    ctx.lineTo(this.x, this.y);
    ctx.strokeStyle = grad;
    ctx.lineWidth   = this.width;
    ctx.stroke();
  };

  /* ══════════════════════════════════
     4. FLOATING DATA LABELS
  ══════════════════════════════════ */
  var labels = [];
  var LABEL_TEXTS = [
    'AUC: 0.942', 'RF model', 'HDFS', 'Dropout: 2.1%',
    'Kafka stream', 'XGBoost', 'pandas', 'scikit-learn',
    'accuracy: 94%', 'batch ingest', 'cluster node',
    'spark', 'predict()', 'fit()', 'csv → HDFS',
    '244K records', 'score: 87', 'risk: low'
  ];

  function Label() {
    this.reset();
  }
  Label.prototype.reset = function () {
    this.text   = LABEL_TEXTS[Math.floor(Math.random() * LABEL_TEXTS.length)];
    this.x      = Math.random() * canvas.width;
    this.y      = canvas.height + 20;
    this.speed  = Math.random() * 0.4 + 0.15;
    this.alpha  = 0;
    this.maxA   = Math.random() * 0.28 + 0.10;
    this.fadeIn = true;
    this.size   = Math.random() * 3 + 9;
    var roll    = Math.random();
    this.color  = roll < 0.5 ? CYAN : roll < 0.78 ? TEAL : PURPLE;
  };
  Label.prototype.update = function () {
    this.y -= this.speed;
    if (this.fadeIn) {
      this.alpha = Math.min(this.alpha + 0.003, this.maxA);
      if (this.alpha >= this.maxA) this.fadeIn = false;
    } else {
      this.alpha = Math.max(this.alpha - 0.0015, 0);
    }
    if (this.alpha <= 0 && !this.fadeIn) this.reset();
    ctx.font = '500 ' + this.size + 'px "Courier New", monospace';
    ctx.fillStyle = this.color + this.alpha + ')';
    ctx.fillText(this.text, this.x, this.y);
  };

  /* ══════════════════════════════════
     INIT
  ══════════════════════════════════ */
  function initAll() {
    particles = [];
    nodes     = [];
    streams   = [];
    labels    = [];
    for (var i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());
    for (var j = 0; j < NODE_COUNT;     j++) nodes.push(new Node());
    for (var k = 0; k < STREAM_COUNT;   k++) {
      var s = new Stream();
      s.y = Math.random() * canvas.height; /* stagger start */
      streams.push(s);
    }
    for (var l = 0; l < 12; l++) {
      var lb = new Label();
      lb.y = Math.random() * canvas.height;
      labels.push(lb);
    }
  }
  initAll();

  /* ══════════════════════════════════
     ANIMATION LOOP
  ══════════════════════════════════ */
  var frame = 0;
  function animate() {
    requestAnimationFrame(animate);
    frame++;

    /* deep dark clear */
    ctx.fillStyle = 'rgba(8,14,28, 0.18)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    /* occasional horizontal scan line */
    if (frame % 180 < 60) {
      var scanY = ((frame % 180) / 60) * canvas.height;
      var scanGrad = ctx.createLinearGradient(0, scanY - 2, 0, scanY + 2);
      scanGrad.addColorStop(0,   CYAN + '0)');
      scanGrad.addColorStop(0.5, CYAN + '0.06)');
      scanGrad.addColorStop(1,   CYAN + '0)');
      ctx.fillStyle = scanGrad;
      ctx.fillRect(0, scanY - 2, canvas.width, 4);
    }

    /* layers: streams → nodes → particles → labels */
    for (var i = 0; i < streams.length;   i++) streams[i].update();
    for (var j = 0; j < nodes.length;     j++) nodes[j].update();
    drawNodes();
    for (var k = 0; k < particles.length; k++) particles[k].update();
    for (var l = 0; l < labels.length;    l++) labels[l].update();
  }
  animate();

})();
