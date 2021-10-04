/* Based on JS Bat 2013 - v1.2 - Eric Grange - www.delphitools.info

Months using the JS Date .getMonth are indexed with January as month '0' */
var MONTHLYSPRITE = {
    9:"bat.webm" // Spooktober
}

spawn_sprite = function() {
    var v = document.createElement('video');
    var s = document.createElement('source');
    var z = document.createElement('div');
    var zs = z.style;
    var a = window.innerWidth * Math.random();
    var b = window.innerHeight * Math.random();
    z.classList.add("monthly-sprite");
    z.appendChild(v);
    v.appendChild(s);
    v.width = "48";
    v.height = "48";
    v.autoplay = true;
    v.loop = true;
    v.muted = true;
    s.src = media_url + "stregsystem/" +MONTHLYSPRITE[d.getMonth()];
    s.type = "video/webm";
    document.body.querySelector(".monthly-sprite-container").appendChild(z);

    function R(o, m) {
        return Math.max(Math.min(o + (Math.random() - 0.5) * 400, m - 50), 50);
    }

    function A(){
        var x = R(a, window.innerWidth);
        var y = R(b, window.innerHeight);
        var d = Math.round(10 * Math.sqrt((a - x) * (a - x) + (b - y) * (b - y)));
        zs.opacity = 1;
        zs.transitionDuration = zs.transitionDuration = d + 'ms';
        // zs.transform = zs.webkitTransform = 'translate(' + x + 'px, ' + y + 'px)';
        zs.left = x + 'px';
        zs.top = y + 'px';
        v.style.transform = v.style.transform = (a > x) ? '' : 'scaleX(-1)';
        a = x;
        b = y;
        setTimeout(A,d);
    }
    setTimeout(A, Math.random() * 3e3);
};

d = new Date();

if(MONTHLYSPRITE[d.getMonth()] !== undefined){
    for(n_sprites=0; n_sprites < d.getDate(); n_sprites++){
        spawn_sprite();
    }
}
