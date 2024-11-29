const d = new Date();

for(let snowflakes=0; snowflakes < d.getDate(); snowflakes++){
    SpawnSnowflake();
}

const santa = document.createElement('div');
santa.classList.add("santa");
const gif = document.createElement("img")
gif.src=themes_static_url+"snow/santa-sled.gif";
santa.appendChild(gif);
document.body.querySelector(".snow-container").appendChild(santa);

SetBodyChristmasStyle();
InjectChristmasCSS();

function SpawnSnowflake () {
    const snowflake = document.createElement('div');
    snowflake.classList.add("snowflake");
    document.body.querySelector(".snow-container").appendChild(snowflake);
}

function SetBodyChristmasStyle() {
    const bodyStyle = document.body.style;
    bodyStyle.color = "white";
    bodyStyle.backgroundImage = "url(\"" + themes_static_url + "snow/background.png\")";
    bodyStyle.backgroundRepeat = "repeat-x";
    bodyStyle.backgroundSize = "auto 100%";
    bodyStyle.padding = "0";
    bodyStyle.margin = "0";
    bodyStyle.width = "100vw";
    bodyStyle.height = "100vh";
    bodyStyle.position = "relative"
}

function InjectChristmasCSS(){
    let el = document.createElement('style');
    el.type = 'text/css';
    el.innerText = "a, a:hover, a:active, a:visited { color: white; }";
    document.head.appendChild(el);
}