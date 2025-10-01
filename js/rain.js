const canvas = document.getElementById("rain");
const ctx = canvas.getContext("2d");

function resize() {
  canvas.width = canvas.parentElement.offsetWidth;
  canvas.height = canvas.parentElement.offsetHeight;
}
resize();
window.addEventListener("resize", resize);

// Crear gotas de lluvia
const drops = [];
for (let i = 0; i < 60; i++) {
  drops.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    length: 10 + Math.random() * 20,
    speed: 2 + Math.random() * 3
  });
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "rgba(255, 215, 0, 0.7)"; // dorado
  ctx.lineWidth = 2;
  ctx.lineCap = "round";

  for (let d of drops) {
    ctx.beginPath();
    ctx.moveTo(d.x, d.y);
    ctx.lineTo(d.x, d.y + d.length);
    ctx.stroke();

    d.y += d.speed;
    if (d.y > canvas.height) {
      d.y = -d.length;
      d.x = Math.random() * canvas.width;
    }
  }

  requestAnimationFrame(draw);
}

draw();
