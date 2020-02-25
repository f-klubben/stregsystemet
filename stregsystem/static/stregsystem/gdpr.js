/*
Hides the username after 5 seconds of showing it.
Simply replaces the letters with 'x'.
*/

var username_element = document.querySelectorAll(".username");

if (username_element.length > 0) {
    setTimeout(function () {
        var username_element = document.querySelectorAll(".username");
        var replaced_username = "[username_hidden]";
        // Only do username replacements on Fridays
        if (new Date().getDay() === 5) {
            const easter_egg_names = ["user", "admin", "root", "alan_turing", "dijkstra", "knuth", "hackerman", "foo",
                "bar", "Robert\'); DROP TABLE fembers;--", "hunter2", "correcthorsebatterystaple",
                String.fromCodePoint(0x1F4BE), String.fromCodePoint(0x1F37A),
                String.fromCodePoint(0x1F937)];
            // Adding by one as Math.random returns a range [0..1)
            replaced_username = easter_egg_names[Math.floor(Math.random() * easter_egg_names.length + 1)];
        }
        for (var i = 0; i < username_element.length; i++) {
            username_element[i].innerText = replaced_username;
        }
    }, 5000);
}