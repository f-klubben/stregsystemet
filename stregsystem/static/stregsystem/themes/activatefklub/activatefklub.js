
attempt_spawn_activatefklub()

function attempt_spawn_activatefklub() {
    // Easter egg once a month inspired by "Activate Windows". Make the easter
    // egg show itself on each Patch Tuesday for Microsoft, which is placed on
    // every second Tuesday of each month.
    // https://en.wikipedia.org/wiki/Patch_Tuesday
    const now = new Date();
    const isSecondTuesday = now.getDay() === 2 && now.getDate() >= 8 && now.getDate() <= 14;
    if (isSecondTuesday) {
        spawn_activatefklub();
        console.log("Hooray its Patch Tuesday! 🎉🪟");
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
