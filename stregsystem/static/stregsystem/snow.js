spawn_snowflake = () => {

    var z = document.createElement('div');
    z.classList.add("snowflake");
    document.body.querySelector(".snow-container").appendChild(z);
}

d = new Date();
if(d.getMonth() === 10){
    for(let n_snowflakes=0; n_snowflakes < d.getDate(); n_snowflakes++){
        spawn_snowflake();
    }
}

