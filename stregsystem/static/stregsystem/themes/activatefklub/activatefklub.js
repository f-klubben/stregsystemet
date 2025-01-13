
attempt_show_activatefklub()

function attempt_show_activatefklub() {
    // Easter egg once a month inspired by "Activate Windows". Make the easter
    // egg show itself on each Patch Tuesday for Microsoft, which is placed on
    // every second Tuesday of each month.
    // https://en.wikipedia.org/wiki/Patch_Tuesday
    const now = new Date();
    const isSecondTuesday = now.getDay() === 2 && now.getDate() >= 8 && now.getDate() <= 14;
    const container = document.getElementById("activatefklub-container");

    if (isSecondTuesday) {
        container.classList.add("activatefklub-shown");
        console.log("Hooray its Patch Tuesday! 🎉🪟");
    }
}
