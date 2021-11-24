spawn_snowflake = () => {

    const z = document.createElement('div');
    z.classList.add("snowflake");
    document.body.querySelector(".snow-container").appendChild(z);
}

d = new Date();
if(d.getMonth() === 10){
    for(let n_snowflakes=0; n_snowflakes < d.getDate(); n_snowflakes++){
        spawn_snowflake();
    }
    let z = document.createElement('div');
    let gif = document.createElement("img")
    gif.src="https://www.animatedimages.org/data/media/359/animated-santa-claus-image-0420.gif"
    z.classList.add("santa");
}

