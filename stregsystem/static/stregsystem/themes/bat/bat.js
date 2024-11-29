// Fallback for WebKit: https://caniuse.com/requestidlecallback
// TODO: remove this crap as soon as WebKit supports the real deal
const requestIdleCallback =
	globalThis.requestIdleCallback ??
	((func, { timeout }) => {
		const maxWait = Math.min(timeout ?? Infinity, 100);
		return setTimeout(func, maxWait);
	});
const cancelIdleCallback = globalThis.cancelIdleCallback ?? clearTimeout;

// The minimum amount of time that CSS animations should be buffered for
const minAnimationBuffer = 5_000;
// The maximum amount of time that CSS animations should be buffered for
const maxAnimationBuffer = 10_000;
// Make this bigger to make bats go faster
const speedMultiplier = 150;

// The HTML container that our bats exist in
const container = document.querySelector("#bat-container");

// The ID of the timeout that is currently waiting to call `pointAndShoot`
let timeoutId;
// A queue of all the bats, ordered by when they will need new coordinates
const batQueue = [];

// Initial setup of the bats queue
for (const element of container.querySelectorAll(".bat")) {
	batQueue.push({
		element,
		nextFly: 0,
	});
}

// Ensure that we disable this stuff if the user prefers reduced motion,
// or if the user is not looking at the page
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion)");
prefersReducedMotion.addEventListener("change", handleStationaryChange);
document.addEventListener("visibilitychange", handleStationaryChange);
handleStationaryChange();
function handleStationaryChange() {
	if (prefersReducedMotion.matches || document.visibilityState === "hidden") {
		pauseShooting();
	} else {
		resumeShooting();
	}
}
/**
 * Makes sure everything stops running and removes any animations.
 */
function pauseShooting() {
	// Let CSS know to stop moving
	container.classList.add("stationary");
	// Stop shooting bats around
	clearTimeout(timeoutId);
	cancelIdleCallback(timeoutId);
	timeoutId = undefined;
}
/**
 * Kickstarts everything again.
 */
function resumeShooting() {
	// Let CSS know to start moving again
	container.classList.remove("stationary");
	// Start shooting bats around again
	prepareNextShot();
}

/**
 * Call this function to ensure that bats are getting new coordinates.
 * DO NOT call the `pointAndShoot` function directly, as that might
 * cause two functions to be running simultaneously.
 */
function prepareNextShot() {
	if (timeoutId !== undefined) {
		return;
	}
	const bat = batQueue[0];
	const timeToNextFly = Math.max(0, bat.nextFly - Date.now());
	if (timeToNextFly < 10) {
		// If the bat needs new coordinates RIGHT NOW, schedule it quick
		// with a very short timeout.
		// We do not run it directly, as running this back-to-back 30 times
		// in a row would block user input and make the page feel janky.
		timeoutId = setTimeout(pointAndShoot, 0);
	} else if (timeToNextFly < maxAnimationBuffer) {
		// If the bat needs new coordinates sometime before the max buffer time,
		// schedule an idle callback, so it doesn't interfere with more important tasks.
		timeoutId = requestIdleCallback(pointAndShoot, { timeout: timeToNextFly });
	} else {
		// If the bat needs new coordinates later than our max buffer time,
		// take a chill pill and schedule a timeout that wakes us up when
		// we get close to our min buffer time limit.
		timeoutId = setTimeout(() => {
			timeoutId = undefined;
			prepareNextShot();
		}, timeToNextFly - minAnimationBuffer);
	}
}
/**
 * Gives the next bat in the queue some new coordinates.
 * DO NOT call this directly, call `prepareNextShot` instead.
 */
function pointAndShoot() {
	// Make it clear that a new timeout can be scheduled
	timeoutId = undefined;

	// Get the next bat in the queue.
	const bat = batQueue.shift();

	// On first load, we need to get the bat position from the HTML
	bat.x ??= Number(bat.element.style.getPropertyValue("--bat-x"));
	bat.y ??= Number(bat.element.style.getPropertyValue("--bat-y"));

	// Calculate new coordinates
	const { coordinate: newX, direction } = newCoordinate(bat.x);
	const { coordinate: newY } = newCoordinate(bat.y);
	// Calculate the animation time based on how far
	// the new coordinates are from the previous
	const distance = Math.sqrt((bat.x - newX) ** 2 + (bat.y - newY) ** 2);
	const flyTime = speedMultiplier * distance;

	const now = Date.now();
	// If we are late to the party, we pretend that the bat was supposed to fly right now
	bat.nextFly = Math.max(bat.nextFly, now);

	// Set the animation in the DOM
	const batDirection = direction * -1;
	bat.element.animate(
		[
			{ "--bat-x": bat.x, "--bat-y": bat.y, "--bat-direction": batDirection },
			{ "--bat-x": newX, "--bat-y": newY, "--bat-direction": batDirection },
		],
		{
			delay: bat.nextFly - now,
			duration: flyTime,
			fill: "forwards",
		},
	);

	// Set everything in our local bat object so we know what's up next time
	bat.nextFly += flyTime;
	bat.x = newX;
	bat.y = newY;

	// Put it back in the bats array.
	// Bats must be ordered such that the first element is always the next one that needs to be shot.
	let i;
	for (i = 0; i < batQueue.length; i++) {
		if (batQueue[i].nextFly > bat.nextFly) {
			break;
		}
	}
	batQueue.splice(i, 0, bat);

	// Move on to the next bat in need
	prepareNextShot();
}

/**
 * Generates a new coordinate that is at least 2% different from
 * the previous, and at most 15% different.
 *
 * @param {number} previous - The previous coordinate.
 */
function newCoordinate(previous) {
	// The minimum amount it can change in percentage
	const min = 2;
	// The amount it can change beyond the minimum, in percentage
	const maxRange = 13;

	const change = min + maxRange * Math.random();
	let direction = Math.random() < 0.5 ? 1 : -1;
	let coordinate = previous + change * direction;
	// Make sure that the bat doesn't move outside the page
	if (coordinate < 0 || 100 < coordinate) {
		direction *= -1;
		coordinate = previous + change * direction;
	}
	return { coordinate, direction };
}

/**
 * Ensure that the value is somewhere between a min and max value.
 *
 * @param {number} min - The smallest permitted value.
 * @param {number} value - The value to clamp.
 * @param {number} max - The largest permitted value.
 */
function clamp(min, value, max) {
	return Math.max(min, Math.min(max, value));
}
