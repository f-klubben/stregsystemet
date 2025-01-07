// Clear everything and start fresh
console.log('QuickBuy script loading...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded');
    
    // Get the form
    const form = document.getElementById('quickbuy-form');
    console.log('Found form:', form);
    
    if (form) {
        // Remove the existing onsubmit attribute
        form.removeAttribute('onsubmit');
        
        form.addEventListener('submit', async function(event) {
            // Prevent the form from submitting immediately
            event.preventDefault();
            console.log('Form submission intercepted');
            
            // Get the input value
            const quickbuyInput = document.getElementById('quickbuy');
            const inputValue = quickbuyInput.value.trim();
            console.log('Input value:', inputValue);
            
            // Split the input to check if it's a purchase
            const parts = inputValue.split(' ');
            
            // If it's just a username (no product ID), submit normally
            if (parts.length <= 1) {
                console.log('Username only - submitting form normally');
                form.submit();
                return;
            }
            
            // If it's a purchase, show confirmation
            const confirmed = await confirmPurchase(parts[0], parts.slice(1));
            console.log('Purchase confirmed:', confirmed);
            
            if (confirmed) {
                // Disable the button (as per original functionality)
                const buyButton = document.getElementById('buybutton');
                if (buyButton) buyButton.disabled = true;
                
                // Submit the form
                console.log('Submitting purchase');
                form.submit();
            }
        });
    }
});

function confirmPurchase(username, productIds) {
    return new Promise((resolve) => {
        const message = `Are you sure you want to buy product(s) ${productIds.join(', ')}?`;
        const result = window.confirm(message);
        console.log('Confirmation result:', result);
        resolve(result);
    });
}

// Keep the original button re-enable functionality
window.addEventListener("pageshow", (event) => {
    const buyButton = document.getElementById('buybutton');
    if (buyButton) buyButton.disabled = false;
}); 