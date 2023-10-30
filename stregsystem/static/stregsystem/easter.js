d = new Date();

if(d.getMonth() === 3){
    if(d.getHours() === 13 && d.getMinutes() === 37){
        for(let beerflakes=0; beerflakes < Math.min(d.getDate(), 24); beerflakes++){
            SpawnBeerflakeCursed();
        }
    }else{
        for(let beerflakes=0; beerflakes < Math.min(d.getDate(), 24); beerflakes++){
            SpawnBeerflake();
        }
    }

    const kylle = document.createElement('div');
    kylle.classList.add("kylle");
    const gif = document.createElement("img")
    if(d.getHours() === 13 && d.getMinutes() === 37){
        gif.src="/static/stregsystem/kylleCursed.gif";
        kylle.setAttribute('style', 'top: 60%');
    }else{
        gif.src="/static/stregsystem/kylle.gif";
    }
    kylle.appendChild(gif);
    document.body.querySelector(".easter-container").appendChild(kylle);

    SetBodyEasterStyle();
}

function SpawnBeerflakeCursed () {
    const beerflakeCursed = document.createElement('div');
    beerflakeCursed.classList.add("beerflake");
    const gif = document.createElement("img")
    gif.src="/static/stregsystem/beerflakeCursed.gif";
    beerflakeCursed.appendChild(gif);
    document.body.querySelector(".easter-container").appendChild(beerflakeCursed);
}

function SpawnBeerflake () {
    const beerflake = document.createElement('div');
    beerflake.classList.add("beerflake");
    const gif = document.createElement("img")
    gif.src="/static/stregsystem/beerflake.gif";
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