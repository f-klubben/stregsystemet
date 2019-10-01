/*
Hides the username after 5 seconds of showing it.´
Simply replaces the letters with 'x'.
*/

var username_element = document.getElementById("username");
if (username_element !== null) {

  setTimeout(function () {

    var username_element = document.getElementById("username");
    if (username_element !== null) {
      username_element.innerText = "x".repeat(username_element.innerText.length);
    }
  }, 5000);
}