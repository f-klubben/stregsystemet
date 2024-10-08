
attempt_spawn_activatefklub()

function attempt_spawn_activatefklub() {
    // Only activate on patch tuesdays.
    if (new Date().getDay() == 2) {
        spawn_activatefklub()
    }
}

function spawn_activatefklub() {
    const header = document.createElement("p");
    header.textContent = "Activate Stregsystemet";
    header.classList.add("activatefklub-header");
    document.body.querySelector(".activatefklub-container").appendChild(header);

    const description = document.createElement("p");
    description.textContent = "Go to the Admin panel to activate Stregsystemet.";
    document.body.querySelector(".activatefklub-container").appendChild(description);
}
