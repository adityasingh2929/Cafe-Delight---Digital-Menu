document.addEventListener('DOMContentLoaded', function() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    document.querySelector('.checkout-btn').addEventListener('click', async function(e) {
        e.preventDefault();

        try {
            const response = await fetch('/create_razorpay_order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                }
            });

            const data = await response.json();

            const options = {
                "key": "rzp_test_QTmdq1PBiByYN9",  // Replace with your actual Razorpay key
                "amount": data.amount,
                "currency": "INR",
                "name": "Cafe Delight",
                "order_id": data.id,
                "handler": function(response) {
                    fetch('/payment_success/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrftoken
                        },
                        body: JSON.stringify({
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_signature: response.razorpay_signature
                        })
                    }).then(() => window.location.href = '/order-success/');
                },
                "theme": {
                    "color": "#6F4E37"
                }
            };

            const rzp = new Razorpay(options);
            rzp.open();
        } catch (error) {
            console.error('Payment failed:', error);
        }
    });
});
