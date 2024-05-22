document.addEventListener('DOMContentLoaded', async function() {
    const video = document.getElementById('video');
    const resultDiv = document.getElementById('result');

    // Función para configurar la cámara
    async function setupCamera() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        
        // Encuentra el ID de la cámara trasera o utiliza la primera disponible
        let deviceId;
        for (const device of videoDevices) {
            if (device.label.includes('back')) {
                deviceId = device.deviceId;
                break;
            }
        }

        // Si no se encontró una cámara trasera, utiliza la primera disponible
        if (!deviceId && videoDevices.length > 0) {
            deviceId = videoDevices[0].deviceId;
        }

        const constraints = {
            video: {
                deviceId: { exact: deviceId }
            }
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
    } catch (error) {
        console.error('Error accessing the camera:', error);
    }
}


    // Llama a la función setupCamera para configurar la cámara cuando se carga el DOM
    setupCamera();

    // Este código maneja el escaneo del código QR y el envío de datos al servidor
    const qrScanner = new QrScanner(video, result => handleQrCode(result));
    qrScanner.start();

    function handleQrCode(result) {
        qrScanner.stop();
        resultDiv.innerText = `QR Code: ${result}`;

        fetch('/process_qr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ qr_data: result }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }
});
