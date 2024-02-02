function deleteEvent(eventId) {
    console.log('Executing deleteEvent function for event with ID:', eventId);
  fetch("/delete-event/" + eventId, {
    method: "POST",
  })
  .then(response => response.json())
  .then(data => {
    console.log(data.message);
    // Puedes realizar acciones adicionales después de la eliminación si es necesario
  }).then((_res) => {
    window.location.href = "/";
  })
  .catch(error => {
    console.error('Error:', error);
  });
}


