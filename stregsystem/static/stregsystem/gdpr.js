/*
Hides the username after 5 seconds of showing it.
Simply replaces the letters with 'x'.
*/

var username_element = document.querySelectorAll(".username");

if (username_element.length > 0) {
    setTimeout(function () {
        var username_element = document.querySelectorAll(".username");
        for (var i = 0; i < username_element.length; i++) {
            username_element[i].innerText = "xxxxxxxx";
        }
        var remainingbalance_element = document.querySelectorAll(".remainingbalance");
        for (var i = 0; i < remainingbalance_element.length; i++) {
            remainingbalance_element[i].innerText = "xx.xx";
        }
    }, 5000);
}