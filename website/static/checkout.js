// This is your test publishable API key.
const stripe = Stripe("pk_test_51OfpDEDOahdbfVYL1Vc9nQ4TnnkZgWxaUghqWXNbMeuTIT7DRJQDGZoGucdQ2ws9xs1p4MlpNFFCWrjhewchZO3L00lf2gWEz8");

// The items the customer wants to buy
const items = [{ id: "xl-tshirt" }];

let elements;

initialize();
checkStatus();

document
  .querySelector("#payment-form")
  .addEventListener("submit", handleSubmit);

// Fetches a payment intent and captures the client secret
async function initialize() {
  const response = await fetch("/create-payment-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
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

async function handleSubmit(e) {
  e.preventDefault();
  setLoading(true);
  console.log("Submitting form...");
  // Obtener los datos del formulario
  const formData = new FormData(document.getElementById("payment-form"));

  // Convertir los datos del formulario en un objeto JSON
  const formDataJSON = {};
  formData.forEach((value, key) => {
    formDataJSON[key] = value;
  });

  const { error } = await stripe.confirmPayment({
    elements,
    confirmParams: {
      // Make sure to change this to your payment completion page
      return_url: "http://localhost:5000/success"
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

