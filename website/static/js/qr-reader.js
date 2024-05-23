document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('preview');
    const resultDiv = document.getElementById('result');

    // Crear un nuevo escáner
    let scanner = new Instascan.Scanner({ video: video });

    // Función para manejar los resultados del escaneo
    scanner.addListener('scan', function(content) {
        resultDiv.innerText = `QR Code: ${content}`;
        // Realizar aquí las operaciones que deseas con el contenido del código QR
        // Por ejemplo, enviar los datos al servidor mediante una solicitud POST
        fetch('/process_qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ qr_data: content }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            if (data.status === "success") {
            displayQRInfo(data.data);
        } else {
            resultDiv.innerText = "QR data is incorrect.";
        }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });

    // Iniciar la cámara y el escáner
    Instascan.Camera.getCameras().then(function(cameras) {
        if (cameras.length > 0) {
            scanner.start(cameras[0]); // Comienza con la primera cámara disponible
        } else {
            console.error('No cameras found.');
        }
    }).catch(function(error) {
        console.error('Error accessing cameras:', error);
    });
    
});
