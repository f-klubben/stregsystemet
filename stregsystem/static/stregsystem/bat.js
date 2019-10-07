/*! JS Bat 2013 - v1.2 - Eric Grange - www.delphitools.info */

spawn_bat = function() {
    var v = document.createElement('video');
    var s = document.createElement('source');
    var z = document.createElement('div');
    var zs = z.style;
    var a = window.innerWidth * Math.random();
    var b = window.innerHeight * Math.random();
    z.classList.add("bat");
    z.appendChild(v);
    v.appendChild(s);
    v.width = "48";
    v.height = "48";
    v.autoplay = true;
    v.loop = true;
    v.muted = true;
    s.src = media_url + "stregsystem/bat.webm";
    s.type = "video/webm";
    document.body.querySelector(".bat-container").appendChild(z);

    function R(o, m) {
        return Math.max(Math.min(o + (Math.random() - 0.5) * 400, m - 50), 50);
    }

    function A(){
        var x = R(a, window.innerWidth);
        var y = R(b, window.innerHeight);
        var d = Math.round(10 * Math.sqrt((a - x) * (a - x) + (b - y) * (b - y)));
        zs.opacity = 1;
        zs.transitionDuration = zs.webkitTransitionDuration = d + 'ms';
        // zs.transform = zs.webkitTransform = 'translate(' + x + 'px, ' + y + 'px)';
        zs.left = x + 'px';
        zs.top = y + 'px';
        v.style.transform = v.style.webkitTransform = (a > x) ? '' : 'scaleX(-1)';
        a = x;
        b = y;
        setTimeout(A,d);
    }
    setTimeout(A, Math.random() * 3e3);
};

d = new Date();

if(d.getMonth() === 9){
    for(n_bats=0; n_bats < d.getDate(); n_bats++){
        spawn_bat();
    }
}
