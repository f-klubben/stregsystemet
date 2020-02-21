/*
Hides the username after 5 seconds of showing it.
Simply replaces the letters with 'x'.
*/

var username_element = document.querySelectorAll(".username");

if (username_element.length > 0) {
    setTimeout(function () {
        var username_element = document.querySelectorAll(".username");
        var replaced_username = "[username_hidden]";
        var date = new Date();
        // Only do username replacements on Fridays
        if (date.getDay() === 5) {
            const easter_egg_names = ["user", "admin", "root", "alan_turing", "hackerman", "foo", "bar"];
            replaced_username = easter_egg_names[Math.floor(Math.random() * easter_egg_names.length)];
        }
        for (var i = 0; i < username_element.length; i++) {
            username_element[i].innerText = replaced_username;
        }
    }, 5000);
}