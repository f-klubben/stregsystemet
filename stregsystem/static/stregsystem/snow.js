d = new Date();

if(d.getMonth() === 11 && d.getDate() <= 24){
    for(let snowflakes=0; snowflakes < d.getDate(); snowflakes++){
        SpawnSnowflake();
    }

    const santa = document.createElement('div');
    santa.classList.add("santa");
    const gif = document.createElement("img")
    gif.src="/static/stregsystem/santa-sled.gif";
    santa.appendChild(gif);
    document.body.querySelector(".snow-container").appendChild(santa);

    SetBodyChristmasStyle();
}

function SpawnSnowflake () {
    const snowflake = document.createElement('div');
    snowflake.classList.add("snowflake");
    document.body.querySelector(".snow-container").appendChild(snowflake);
}

function SetBodyChristmasStyle() {
    const bodyStyle = document.body.style;
    bodyStyle.color = "white";
    bodyStyle.backgroundImage = "url(\"" + media_url + "stregsystem/background.png\")";
    bodyStyle.backgroundRepeat = "repeat-x";
    bodyStyle.backgroundSize = "auto 100%";
    bodyStyle.padding = "0";
    bodyStyle.margin = "0";
    bodyStyle.width = "100vw";
    bodyStyle.height = "100vh";
    bodyStyle.position = "relative"
}
