
spawn_man();
spawn_beaver();
animate_man();
animate_beaver();

function spawn_beaver() {
    const beaver = document.createElement('div');
    beaver.classList.add("beaver");
    const beaverpng = document.createElement("img")
    beaverpng.src = themes_static_url + "bober/beaver.gif";
    beaverpng.classList.add("beaverpng");
    beaver.appendChild(beaverpng);
    document.body.querySelector(".beaver-container").appendChild(beaver);
}

function spawn_man() {

    const manden = document.createElement('div');
    manden.classList.add("manden");
    const mandpng = document.createElement("img")
    mandpng.src = themes_static_url + "bober/man.gif";
    mandpng.classList.add("mandenpng")
    manden.appendChild(mandpng);
    document.body.querySelector(".men-container").appendChild(manden);
}

function animate_man() {
    const man = document.body.querySelector(".manden");
    const manpng = document.body.querySelector(".mandenpng");
    const beaver = document.body.querySelector(".beaver");

    const manRect = man.getBoundingClientRect();
    const beaverRect = beaver.getBoundingClientRect();

    var dx = beaverRect.left - manRect.left;
    var dy = beaverRect.top - manRect.top;

    var newX = manRect.left + Math.sign(dx) * Math.min(Math.abs(dx), 1);
    var newY = manRect.top + Math.sign(dy) * Math.min(Math.abs(dy), 1);

    var angle = Math.atan2(dy, dx);

    man.style.left = newX + "px";
    man.style.top = newY + "px";

    manpng.style.transform = `rotate(${angle}rad)`;
    requestAnimationFrame(animate_man);
}

function animate_beaver() {
    const beaver = document.body.querySelector(".beaver");

    var currentRect = beaver.getBoundingClientRect();
    var screenWidth = window.innerWidth;
    var screenHeight = window.innerHeight;
    
    var random_x = (Math.random() - 0.5) * 30;
    var random_y = (Math.random() - 0.5) * 30;

    var next_x = currentRect.left + random_x;
    var next_y = currentRect.top + random_y;

    if (next_x < 0) {
        next_x = 0;
    } else if (next_x > screenWidth - currentRect.width) {
        next_x = screenWidth - currentRect.width;
    }
    if (next_y < 0) {
        next_y = 0;
    } else if (next_y > screenHeight - currentRect.height) {
        next_y = screenHeight - currentRect.height;
    }

    beaver.style.left = next_x + "px";
    beaver.style.top = next_y + "px";

    requestAnimationFrame(animate_beaver);
}