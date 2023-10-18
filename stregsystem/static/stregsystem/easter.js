d = new Date();

if (d.getMonth() === 3) {
    const flakeType = (d.getHours() === 13 && d.getMinutes() === 37) ? "--flake-cursed" : "--flake-normal";
    
    for(let beerflakes = 0; beerflakes < Math.min(d.getDate(), 24); beerflakes++)
        SpawnBeerflake(flakeType);

    const kylle = document.createElement('div'),
        kylleType = (d.getHours() === 13 && d.getMinutes() === 37) ? "--kylle-cursed" : "--kylle-normal";

    kylle.classList.add("kylle", kylleType);
    document.body.querySelector(".easter-container").appendChild(kylle);

    SetBodyEasterStyle();
}

function SpawnBeerflake (type = "--flake-normal") {
    const beerflake = document.createElement('div');
    beerflake.classList.add("beerflake", type);
    document.body.querySelector(".easter-container").appendChild(beerflake);
}

function SetBodyEasterStyle() {
    document.body.classList.add("easter-style");
}