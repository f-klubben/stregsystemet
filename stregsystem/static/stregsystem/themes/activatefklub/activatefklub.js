
attempt_spawn_activatefklub()

function attempt_spawn_activatefklub() {
    // Only activate on patch tuesdays.
    if (new Date().getDay() == 2) {
        spawn_activatefklub()
    }
}

function spawn_activatefklub() {
    const header = document.createElement("p");
    header.textContent = "Activate your Fklub Account";
    header.classList.add("activatefklub-header");
    document.body.querySelector(".activatefklub-container").appendChild(header);

    const description = document.createElement("p");
    description.textContent = "Go to stregsystemet to pay for membership.";
    document.body.querySelector(".activatefklub-container").appendChild(description);
}
