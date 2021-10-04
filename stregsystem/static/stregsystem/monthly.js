/* Based on JS Bat 2013 - v1.2 - Eric Grange - www.delphitools.info

Months using the JS Date .getMonth are indexed with January as month '0' */
var MONTHLYSPRITE = {
    9:"bat.webm" // Spooktober
}

spawn_sprite = function() {
    var video_element = document.createElement('video');
    var video_source = document.createElement('source');
    var z = document.createElement('div');
    var z_style = z.style;
    var scaled_width = window.innerWidth * Math.random();
    var scaled_height = window.innerHeight * Math.random();
    z.classList.add("monthly-sprite");
    z.appendChild(video_element);
    video_element.appendChild(video_source);
    video_element.width = "48";
    video_element.height = "48";
    video_element.autoplay = true;
    video_element.loop = true;
    video_element.muted = true;
    video_source.src = media_url + "stregsystem/" +MONTHLYSPRITE[d.getMonth()];
    video_source.type = "video/webm";
    document.body.querySelector(".monthly-sprite-container").appendChild(z);

    function animation_start_location(scaled_dimension, window_dimension) {
        return Math.max(Math.min(scaled_dimension + (Math.random() - 0.5) * 400, window_dimension - 50), 50);
    }

    function sprite_animation(){
        var x = animation_start_location(scaled_width, window.innerWidth);
        var y = animation_start_location(scaled_height, window.innerHeight);
        var animation_duration = Math.round(10 * Math.sqrt((scaled_width - x) * (scaled_width - x) + (scaled_height - y) * (scaled_height - y)));
        z_style.opacity = 1;
        z_style.transitionDuration = z_style.transitionDuration = animation_duration + 'ms';
        // zs.transform = zs.webkitTransform = 'translate(' + x + 'px, ' + y + 'px)';
        z_style.left = x + 'px';
        z_style.top = y + 'px';
        video_element.style.transform = video_element.style.transform = (scaled_width > x) ? '' : 'scaleX(-1)';
        scaled_width = x;
        scaled_height = y;
        setTimeout(sprite_animation,animation_duration);
    }
    setTimeout(sprite_animation, Math.random() * 3e3);
};

d = new Date();

if(MONTHLYSPRITE[d.getMonth()] !== undefined){
    for(n_sprites=0; n_sprites < d.getDate(); n_sprites++){
        spawn_sprite();
    }
}
