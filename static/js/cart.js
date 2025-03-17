document.addEventListener('DOMContentLoaded', function() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let pendingAction = null;

    // Confirmation modal handlers
    const modal = document.getElementById('confirmationModal');
    const confirmBtn = document.querySelector('.modal-confirm');
    const cancelBtn = document.querySelector('.modal-cancel');

    confirmBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        if (pendingAction) {
            performCartAction(pendingAction.itemId, pendingAction.action);
        }
    });

    cancelBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        // Reset quantity to 1 if canceled
        if (pendingAction) {
            const quantityDisplay = document.querySelector(`[data-item-id="${pendingAction.itemId}"] .quantity-display`);
            quantityDisplay.textContent = 1;
        }
    });

    async function performCartAction(itemId, action) {
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
            updateCartUI(itemId, data);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    function updateCartUI(itemId, data) {
        const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);

        if (data.status === 'removed') {
            itemElement.remove();
        } else if (data.status === 'updated') {
            itemElement.querySelector('.quantity-display').textContent = data.quantity;
        }

        // Update total price
        fetch('/cart/')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newTotal = doc.querySelector('.total-amount').textContent;
                document.querySelector('.total-amount').textContent = newTotal;
            });
    }

    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const itemId = btn.closest('.cart-item').dataset.itemId;
            const action = btn.dataset.action;
            const currentQuantity = parseInt(btn.parentElement.querySelector('.quantity-display').textContent);

            if (action === 'decrement' && currentQuantity === 1) {
                // Show confirmation modal
                pendingAction = { itemId, action };
                modal.style.display = 'flex';
            } else {
                performCartAction(itemId, action);
            }
        });
    });
});