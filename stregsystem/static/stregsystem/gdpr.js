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
  }, 5000);
}