d = new Date();

if(d.getMonth() === 8){
    //spawning beercans/beerflakes. Adds another beerflake each day for the first 24 days.
    for(let beerflakes=0; beerflakes < Math.min(d.getDate(), 24); beerflakes++){
        SpawnBeerflake();
    }

    const kylle = document.createElement('div');
    kylle.classList.add("kylle");
    const gif = document.createElement("img")
    gif.src="/static/stregsystem/kylle.gif";
    kylle.appendChild(gif);
    document.body.querySelector(".easter-container").appendChild(kylle);

    SetBodyEasterStyle();
}

function SpawnBeerflake () {
    const beerflake = document.createElement('div');
    beerflake.classList.add("beerflake");
    beerflake.style.zIndex="0";
    const gif = document.createElement("img")
    gif.src="/static/stregsystem/beerflake.webp";
    beerflake.appendChild(gif);
    document.body.querySelector(".easter-container").appendChild(beerflake);
}

function SetBodyEasterStyle() {
    const bodyStyle = document.body.style;
    bodyStyle.color = "black";
    bodyStyle.backgroundImage = "url(\"" + media_url + "stregsystem/easter.jpg\")";
    bodyStyle.backgroundRepeat = "repeat-x";
    bodyStyle.backgroundSize = "auto 100%";
    bodyStyle.padding = "0";
    bodyStyle.margin = "0";
    bodyStyle.width = "100vw";
    bodyStyle.height = "100vh";
    bodyStyle.position = "relative";
}