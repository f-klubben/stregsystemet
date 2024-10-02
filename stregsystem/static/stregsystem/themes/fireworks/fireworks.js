// Make the text readable
document.body.style.color = "white";

const starsPerPixel = 0.01;

const rocketConfig = {
  timeBetweenRockets: 1.2, // Seconds between rockets
  timeRandomness: 2,
  speed: 200, // Pixels per second.
  size: [ 50, 100 ] // Size in pixels
};

// Crank this bitch up to make it more better (laggy)
const numSimultaneousExplosions = 8;

const minColor = 0.1;
const maxColor = 0.8;

const flashTime = 250;

// How many sparkles to spawn per explosion.
const numSparkles = 160;

// The amount of pixels from the sides of the screen that the rocket will never explode at.
const minSpaceFromSides = 150;

const maxDifferenceBetweenStartXandEndX = 250;

const body = document.body;
const canvasContainer = document.getElementById("canvas-container");
const rocketImg = document.getElementById("rocket");


const starCanvas = createCanvas("star", -100, updateStars);
starCanvas.canvas.style.backgroundColor = "black";
const rocketCanvas = createCanvas("rocket", -1);

const canvases = [starCanvas, rocketCanvas];
const explosionCanvases = [];

for (let i = 0; i < numSimultaneousExplosions; i++) {
  const canvas = createCanvas("explosion" + i, -50, function(canvas) {canvas.ctx.globalCompositeOperation = "lighter"});
  canvas.used = false;
  canvases.push(canvas);
  explosionCanvases.push(canvas);
}

window.addEventListener("resize", updateCanvasSizes);
updateCanvasSizes();


let explosionLastTime = null;
let explosions = [];


function updateExplosions(now) {
  if (explosionLastTime === null) {
    explosionLastTime = now;
  }
  const deltaTime = (now - explosionLastTime) / 1000;
  explosionLastTime = now;

  const explosionsToRemove = [];

  for (let j = explosions.length - 1; j >= 0; j--) {
    const explosion = explosions[j];

    const canvas = explosion.canvas.canvas;
    const ctx = explosion.canvas.ctx;

    const f = explosion.timeLeft / 5;
    const directionFactor = deltaTime * 80 * smoothStep(f);
    const gravityFactor = explosion.gravityFactor * deltaTime;

    // Update sparkles
    for (let i = 0; i < explosion.sparkles.length; i++) {
      const sparkle = explosion.sparkles[i];

      const oldPositionX = sparkle.position[0];
      const oldPositionY = sparkle.position[1];

      const newPositionX = sparkle.position[0] + sparkle.direction[0] * directionFactor;
      const newPositionY = sparkle.position[1] + sparkle.direction[1] * directionFactor + gravityFactor;

      sparkle.position[0] = newPositionX;
      sparkle.position[1] = newPositionY;

      const color = rgbaToString(sparkle.color[0] * f, sparkle.color[1] * f, sparkle.color[2] * f);
      drawLine(ctx, oldPositionX, oldPositionY, newPositionX, newPositionY, color, f * 3);



      // Draw flashes
      const flashTime2 = flashTime + sparkle.flashSpeedOffset;
      const fadeFactor = explosion.timeLeft <= 1 ? explosion.timeLeft : 1;

      let flashFactor = ((now + sparkle.flashOffset) % flashTime2) / flashTime2;
      if (flashFactor < 0.5) {
        flashFactor = 1 - flashFactor;
      }
      
      flashFactor *= fadeFactor;


      const flashesColor = rgbaToString(sparkle.flashColor[0] * flashFactor, sparkle.flashColor[1] * flashFactor, sparkle.flashColor[2] * flashFactor);
      //const flashesColor = sparkle.flashColor;

      const rCtx = rocketCanvas.ctx;

      rCtx.fillStyle = flashesColor;
      rCtx.fillRect(newPositionX - 1, newPositionY - 1, 2, 2);
    }

    explosion.gravityFactor += 9.82 * deltaTime * 1;
    explosion.timeLeft -= deltaTime;

    if (explosion.timeLeft <= 0) {
      explosionsToRemove.push(explosion);
    }
    else if (explosion.timeLeft <= 2) {
      const fadeOut = explosion.timeLeft / 2;
      canvas.style.opacity = fadeOut;
      canvas.style.filter = "blur(" + ((1 / fadeOut) - 1) + "px)";
    }

  }

  for (let explosionToDelete of explosionsToRemove) {
    const index = explosions.indexOf(explosionToDelete);
    explosions.splice(index,1);
    explosionToDelete.canvas.ctx.clearRect(0, 0, explosionToDelete.canvas.canvas.width, explosionToDelete.canvas.canvas.height);
    explosionToDelete.canvas.used = false;
    explosionToDelete.canvas.canvas.style.opacity = 1;
    //explosionToDelete.canvas.canvas.style.blur = 0;
    explosionToDelete.canvas.canvas.style.filter = "blur(0)";
  }
}

let nextRocketTime = 0;
let rockets = [];

function updateRocket(now) {
  const canvas = rocketCanvas.canvas;
  const ctx = rocketCanvas.ctx;

  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);

  if (rocketCanvas.lastTime == null) {
    rocketCanvas.lastTime = now;
  }

  const deltaTime = (now - rocketCanvas.lastTime) / 1000;
  rocketCanvas.lastTime = now;

  if (now >= nextRocketTime) {
    nextRocketTime = now + rocketConfig.timeBetweenRockets * 1000 + Math.random() * rocketConfig.timeRandomness * 1000;


    const endX = Math.random() * (width - (minSpaceFromSides*2)) + minSpaceFromSides;
    const endY = Math.random() * (height - (minSpaceFromSides*2)) + minSpaceFromSides;

    const startX = (Math.random() * (maxDifferenceBetweenStartXandEndX * 2)- maxDifferenceBetweenStartXandEndX) + endX;
    const startY = height;

    const xDist = endX - startX;
    const yDist = endY - startY;

    const angle = Math.atan2(yDist, xDist);

    const direction = [Math.cos(angle), Math.sin(angle)];

    rockets.push({ position: [startX, startY], targetY: endY, angle: angle, direction: direction, speed: rocketConfig.speed});
  }

  // Update position and remove
  for (let i = rockets.length - 1; i >= 0; i--) {
    const rocket = rockets[i];
    rocket.position[0] += rocket.direction[0] * deltaTime * rocket.speed;
    rocket.position[1] += rocket.direction[1] * deltaTime * rocket.speed;


    if (rocket.position[1] < rocket.targetY) {
      spawnExplosion(rocket.position);
      rockets.splice(i,1);
    }
  }

  for (let rocket of rockets) {
    drawImage(ctx, rocketImg, rocket.position[0] - (rocketConfig.size[0] / 2), rocket.position[1] - (rocketConfig.size[1] / 2), rocketConfig.size[0], rocketConfig.size[1], rocket.angle + Math.PI / 2);
  }
}

function runAnimations(now) {
  updateRocket(now);
  updateExplosions(now);

  window.requestAnimationFrame(runAnimations);
}

window.requestAnimationFrame(runAnimations);

function spawnExplosion(position) {
  for (let canvas of explosionCanvases) {
    if (canvas.used === false) {
      const explosion = {
        canvas: canvas,
        timeLeft: 5,
        sparkles: [],
        gravityFactor: 0
      };


      const sparkleColor = generateColor();
      const sparkleColor2 = generateColor();

      const useSparkleColorForFlash = Math.random() > 0.5;

      for (let i = 0; i < numSparkles; i++) {
        const angle = Math.random()*Math.PI*2;
        const radius = Math.random();
        const x = Math.cos(angle)*radius;
        const y = Math.sin(angle)*radius;
        const color = i % 2 == 0 ? sparkleColor : sparkleColor2;
        const flashColor = useSparkleColorForFlash ? color : [1, 0.5, 0];
        explosion.sparkles.push({ color: color, position: [position[0], position[1]], direction: [x, y], flashColor: flashColor, flashOffset: Math.random() * flashTime, flashSpeedOffset: Math.random() * 50});
      }

      canvas.used = true;
      explosions.push(explosion);

      return;
    }
  }

  // Explosion gets skipped when it cant find the canvas.
  // However, it should be considered an error.
  console.error("COULD NOT FIND UNUSED CANVAS Increase numSimultaneousExplosions or increase rocketConfig.timeBetweenRockets");
}

function updateStars() {
  const canvas = starCanvas.canvas;
  const ctx = starCanvas.ctx;

  const width = canvas.width;
  const height = canvas.height;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "white";

  const stars = width * height * starsPerPixel;

  for (let i = 0; i < stars; i++) {
    const x = Math.random() * width;
    const y = Math.random() * height;
    const size = Math.random();
    ctx.fillRect(x, y, size, size);
  }
}


function createCanvas(name, zIndex, resizeFunc) {
  const canvas = document.createElement("canvas");
  canvas.id = name + "-canvas";
  canvas.style.zIndex = zIndex;
  const ctx = canvas.getContext("2d");

  canvasContainer.appendChild(canvas);

  return { canvas: canvas, ctx: ctx, resizeFunc: resizeFunc };
}

function updateCanvasSizes() {
  for (let canvas of canvases) {
    const c = canvas.canvas;
    c.width = body.clientWidth;
    c.height = body.clientHeight;

    if (canvas.resizeFunc !== undefined) {
      canvas.resizeFunc(canvas);
    }
  }
}

function drawLine(ctx, x0, y0, x1, y1, color, thickness) {
  const halfThickness = thickness / 2;
  const angle = Math.atan2(y1 - y0, x1 - x0);
  
  const angle0 = angle + Math.PI / 2;
  const angle1 = angle - Math.PI / 2;
  
  const halfwayX = (x1 + x0) / 2;
  const halfwayY = (y1 + y0) / 2;
  
  const gX0 = Math.cos(angle0) * halfThickness + halfwayX;
  const gY0 = Math.sin(angle0) * halfThickness + halfwayY;
  
  const gX1 = Math.cos(angle1) * halfThickness + halfwayX;
  const gY1 = Math.sin(angle1) * halfThickness + halfwayY;
  
  
  const gradient = ctx.createLinearGradient(gX0, gY0, gX1, gY1);
  gradient.addColorStop(0, "black");
  gradient.addColorStop(0.5, color);
  gradient.addColorStop(1, "black");

  ctx.strokeStyle = gradient;
  ctx.lineWidth = thickness;
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y1);
  ctx.stroke();
}

function smoothStep(x) {
  return x * x * (3 - 2 * x);
}

function rgbaToString(r, g, b, a) {

  return`rgba(${r * 255}, ${g * 255}, ${b * 255}, ${(a === undefined ? 1.0 : a) * 255})`;
}

function hslaToString(h, s, l, a) {
  return `hsla(${h * 359}, ${s * 100}%, ${l * 100}%, ${a})`;
}

function generateColor() {
  function g() {
    return Math.random() * (maxColor - minColor) + minColor;
  }
  return [g(), g(), g()];
}

function drawImage(ctx, image, x, y, w, h, degrees){
  ctx.save();
  ctx.translate(x+w/2, y+h/2);
  ctx.rotate(degrees);
  ctx.translate(-x-w/2, -y-h/2);
  ctx.drawImage(image, x, y, w, h);
  ctx.restore();
}
