// This is your test publishable API key.
const stripe = Stripe("pk_test_51OfpDEDOahdbfVYL1Vc9nQ4TnnkZgWxaUghqWXNbMeuTIT7DRJQDGZoGucdQ2ws9xs1p4MlpNFFCWrjhewchZO3L00lf2gWEz8");

let elements;



checkStatus();

document
  .querySelector("#payment-form")
  .addEventListener("submit", handleSubmit);

// Fetches a payment intent and captures the client secret
async function initialize() {
    const totalAmount = $('#totalAmountDisplay').text().replace('Total Amount: €', '').trim();

    const formData = {
        vip_admin_tickets: document.getElementById("vip_admin_tickets")?.value,
        number_member_tickets: document.getElementById("number_member_tickets")?.value,
        number_child_member_tickets: document.getElementById("number_child_member_tickets")?.value,
        number_guest_tickets: document.getElementById("number_guest_tickets").value,
        number_child_tickets: document.getElementById("number_child_tickets").value,
        guests_names: document.getElementById("guests_names").value,
        totalAmount: totalAmount,
        event_id: document.getElementById('eventId').dataset.eventId
    };

    var payCashCheckbox = document.getElementById('pay_cash');


    if (
        formData.vip_admin_tickets === "0" &&
        formData.number_member_tickets === "0" &&
        formData.number_child_member_tickets === "0" &&
        formData.number_guest_tickets === "0" &&
        formData.number_child_tickets === "0"
    ) {
        console.error("Error: No puedes comprar 0 entradas en todos los tipos.");
        alert("No puedes comprar 0 entradas en todos los tipos.");
        window.location.href =  `/event-attendance/${formData.event_id}`;
        return;
    }


    // Comprobar disponibilidad de entradas
    const availabilityResponse = await fetch("/check-ticket-availability", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
    });

    if (availabilityResponse.ok) {

        if (
        formData.vip_admin_tickets !== "0" &&
        formData.number_member_tickets === "0" &&
        formData.number_child_member_tickets === "0" &&
        formData.number_guest_tickets === "0" &&
        formData.number_child_tickets === "0"
        ) {
            fetch('/success_vip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (response.ok) {
                    console.log('Datos enviados correctamente a /success-vip.'); 
                    window.location.href = '/success_cash_template';
                    // Aquí puedes realizar otras acciones después de enviar los datos correctamente
                } else {
                    console.error('Error al enviar los datos a /success-cash.');
                    // Aquí puedes manejar el error de envío de datos
                }
            })
            .catch(error => {
                console.error('Error al enviar los datos a /success-cash:', error);
                // Aquí puedes manejar cualquier otro error
            });
        }else{
              if (
        (formData.vip_admin_tickets !== "0" ||
        formData.number_member_tickets !== "0" ||
        formData.number_child_member_tickets !== "0" ||
        formData.number_guest_tickets !== "0" ||
        formData.number_child_tickets !== "0") &&
        formData.totalAmount === "0"
        ) {
            fetch('/success_free', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (response.ok) {
                    console.log('Datos enviados correctamente a /success-vip.'); 
                    window.location.href = '/success_cash_template';
                    // Aquí puedes realizar otras acciones después de enviar los datos correctamente
                } else {
                    console.error('Error al enviar los datos a /success-cash.');
                    // Aquí puedes manejar el error de envío de datos
                }
            })
            .catch(error => {
                console.error('Error al enviar los datos a /success-cash:', error);
                // Aquí puedes manejar cualquier otro error
            });
        }
        }
        

        


        if (payCashCheckbox.checked) {
            console.log("La casilla 'Pay with cash' está marcada.");

            // Envía los datos del formulario a la vista Flask utilizando fetch
            fetch('/success_cash', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (response.ok) {
                    console.log('Datos enviados correctamente a /success-cash.'); 
                    window.location.href = '/success_cash_template';
                    // Aquí puedes realizar otras acciones después de enviar los datos correctamente
                } else {
                    console.error('Error al enviar los datos a /success-cash.');
                    // Aquí puedes manejar el error de envío de datos
                }
            })
            .catch(error => {
                console.error('Error al enviar los datos a /success-cash:', error);
                // Aquí puedes manejar cualquier otro error
            });
        } else {
            const response = await fetch("/create-payment-intent", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            const { clientSecret } = await response.json();

            const appearance = {
                theme: 'stripe',
            };
            elements = stripe.elements({ appearance, clientSecret });

            const paymentElementOptions = {
                layout: "tabs",
            };

            const paymentElement = elements.create("payment", paymentElementOptions);
            paymentElement.mount("#payment-element");
        }
    } else {
        const errorData = await availabilityResponse.json();
        console.error('Error: ', errorData.message);
        alert(errorData.message);
        window.location.href = `/event-attendance/${formData.event_id}?error=${encodeURIComponent(errorData.message)}`;
    }
}


async function handleSubmit(e) {
  e.preventDefault();
  setLoading(true);
  console.log("Submitting form...");
  // Obtener el totalAmount del elemento #totalAmountDisplay
  const totalAmount = parseFloat(document.getElementById("totalAmountDisplay").textContent.replace('Total Amount: €', '').trim());

  // Obtener el event_id del elemento #eventId
  const eventId = document.getElementById("eventId").dataset.eventId;

  // Obtener los datos del formulario
  const formData = new FormData(document.getElementById("payment-form"));

// Agregar el totalAmount y el event_id al formData
  formData.append('totalAmount', totalAmount);
  formData.append('event_id', eventId);
  

  // Convertir los datos del formulario en un objeto JSON
  const formDataJSON = {};
  formData.forEach((value, key) => {
    formDataJSON[key] = value;
  });
  console.log(formDataJSON);
  const { error } = await stripe.confirmPayment({
    elements,
    confirmParams: {
      // Make sure to change this to your payment completion page
      return_url: "http://localhost:5000/success?" + new URLSearchParams(formData).toString(),
      //receipt_email: document.getElementById("email").value,
    },
  });

  console.log("Confirmation result:", error);
  if (error.type === "card_error" || error.type === "validation_error") {
    showMessage(error.message);
  } else {
    showMessage("Payment succeeded!");
  }

  setLoading(false);
}

// Fetches the payment intent status after payment submission
async function checkStatus() {
  const clientSecret = new URLSearchParams(window.location.search).get(
    "payment_intent_client_secret"
  );

  if (!clientSecret) {
    return;
  }

  const { paymentIntent } = await stripe.retrievePaymentIntent(clientSecret);

  switch (paymentIntent.status) {
    case "succeeded":
      showMessage("Payment succeeded!");
      break;
    case "processing":
      showMessage("Your payment is processing.");
      break;
    case "requires_payment_method":
      showMessage("Your payment was not successful, please try again.");
      break;
    default:
      showMessage("Something went wrong.");
      break;
  }
}

// ------- UI helpers -------

function showMessage(messageText) {
  const messageContainer = document.querySelector("#payment-message");

  messageContainer.classList.remove("hidden");
  messageContainer.textContent = messageText;

  setTimeout(function () {
    messageContainer.classList.add("hidden");
    messageContainer.textContent = "";
  }, 4000);
}

// Show a spinner on payment submission
function setLoading(isLoading) {
  if (isLoading) {
    // Disable the button and show a spinner
    document.querySelector("#submit").disabled = true;
    document.querySelector("#spinner").classList.remove("hidden");
    document.querySelector("#button-text").classList.add("hidden");
  } else {
    document.querySelector("#submit").disabled = false;
    document.querySelector("#spinner").classList.add("hidden");
    document.querySelector("#button-text").classList.remove("hidden");
  }
}

function isFormValid() {
  // Obtén todos los campos del formulario
  const inputs = document.querySelectorAll("#payment-form input[type='number'], #payment-form input[type='text']:not(#guests_names)");

  // Verifica si algún campo está vacío
  for (const input of inputs) {
    
    if (!input.value) {
      return false; // Devuelve false si algún campo está vacío
    }
  }
  return true; // Devuelve true si todos los campos están llenos
}

document.getElementById("continue-btn").addEventListener("click", function() {
  event.preventDefault();
  if (isFormValid()) {
    initialize();
    document.getElementById("hidden-payment-form").classList.remove("hidden");
    document.getElementById("formulario_a_ocultar").classList.add("hidden");
  } else {
    document.getElementById("error-message").classList.remove("hidden");
    showMessage("You must fill in all the fields."); // Muestra un mensaje si el formulario no está completo
  }
  setTimeout(function() {
      document.getElementById("error-message").classList.add("hidden");
    }, 3000);
});