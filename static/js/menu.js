document.addEventListener('DOMContentLoaded', function() {
    const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfElement) {
        console.error('CSRF token element not found.');
        return;
    }
    const csrftoken = csrfElement.value;

    function updateCartUI(itemId, newQuantity, isNewItem) {
        // Get the quantity-control container using the first element with the matching data attribute.
        const quantityControl = document.querySelector(`[data-item-id="${itemId}"]`).closest('.quantity-control');

        if (newQuantity === 0) {
            // When quantity is zero, revert to the add button.
            quantityControl.innerHTML = `
                <button class="add-btn" data-item-id="${itemId}">
                    <span class="plus-icon">+</span> Add
                </button>
            `;
            quantityControl.querySelector('.add-btn').addEventListener('click', handleCartAction);
        } else {
            if (isNewItem) {
                // Replace the add button with a new stepper (including count, decrement, and increment buttons).
                quantityControl.innerHTML = `
                    <div class="stepper">
                        <button class="step-btn decrement" data-item-id="${itemId}">−</button>
                        <span class="count">${newQuantity}</span>
                        <button class="step-btn increment" data-item-id="${itemId}">+</button>
                    </div>
                `;
                quantityControl.querySelector('.decrement').addEventListener('click', handleCartAction);
                quantityControl.querySelector('.increment').addEventListener('click', handleCartAction);
            } else {
                // Update the count element if the stepper already exists.
                const countElement = quantityControl.querySelector('.count');
                if (countElement) {
                    countElement.textContent = newQuantity;
                } else {
                    console.error('Count element not found for item ' + itemId);
                }
            }
        }

        // Update cart counter (number of distinct items in the cart)
        const cartCount = document.querySelector('.item-count');
        const currentCount = parseInt(cartCount.textContent);
        cartCount.textContent = isNewItem ? currentCount + 1 : Math.max(0, currentCount + (newQuantity === 0 ? -1 : 0));
    }

    async function handleCartAction(e) {
        e.preventDefault();
        const itemId = this.dataset.itemId;
        const action = this.classList.contains('increment') ? 'increment' :
                      this.classList.contains('decrement') ? 'decrement' : 'add';

        try {
            const response = await fetch('/update_cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    item_id: itemId,
                    action: action
                })
            });

            const data = await response.json();
            if (data.status === 'added') {
                updateCartUI(itemId, 1, true);
            } else if (data.status === 'updated') {
                updateCartUI(itemId, data.quantity, false);
            } else if (data.status === 'removed') {
                updateCartUI(itemId, 0, false);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Attach event listeners to all initial add and step buttons
    document.querySelectorAll('.add-btn, .step-btn').forEach(btn => {
        btn.addEventListener('click', handleCartAction);
    });
});
