document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();
    const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0); // Midnight

    const countdown = document.createElement("p");
    countdown.id = "countdown";
    document.getElementById("newyear-theme").appendChild(countdown);

    function updateCountdown() {
        const timeLeft = midnight - new Date();
        if (timeLeft > 0) {
            const hours = Math.floor(timeLeft / (1000 * 60 * 60));
            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
            countdown.textContent = `Time left: ${hours}h ${minutes}m ${seconds}s`;
        } else {
            countdown.textContent = "Happy New Year!";
            clearInterval(interval);
        }
    }

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
});

