spawn_snowflake = () => {
    const snowflake = document.createElement('div');
    snowflake.classList.add("snowflake");
    document.body.querySelector(".snow-container").appendChild(snowflake);
}

d = new Date();
if(d.getMonth() === 10){
    for(let n_snowflakes=0; n_snowflakes < d.getDate(); n_snowflakes++){
        spawn_snowflake();
    }
    const santa = document.createElement('div');
    santa.classList.add("santa");
    const gif = document.createElement("img")
    gif.src="https://www.animatedimages.org/data/media/359/animated-santa-claus-image-0420.gif";
    santa.appendChild(gif);
    document.body.querySelector(".snow-container").appendChild(santa);
}

