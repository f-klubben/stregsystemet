var queue = [].slice.call(document.querySelectorAll(".dummy"));
var front = queue.shift();
var this_id = -1;

function swap(tag) {
    //Flip in the DOM
    front.classList.remove("front");

    queue.push(front);
    front = queue.shift();

    front.classList.add("front");
}

function updateKiosk() {
    var t = front;
    t.addEventListener("transitionend", function loadnext(tag) {
        t.removeEventListener("transitionend", loadnext);
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.onreadystatechange = function() {
            if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
                obj = JSON.parse(xmlHttp.responseText);
                this_id = obj.id;
                t.style.backgroundImage = 'url("' + obj.url +'")';
            }
        }
        //Start by asking random for the first image
        if(this_id === -1) {
            xmlHttp.open("GET", "/kiosk/random", true);
        } else {
            xmlHttp.open("GET", "/kiosk/next_real/" + this_id + "/", true);
        }
        xmlHttp.send(null);
    });
    swap();
}

setInterval("updateKiosk()", 10000);
updateKiosk();
