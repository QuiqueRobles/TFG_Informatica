document.addEventListener('DOMContentLoaded', async function () {
    const resultDiv = document.getElementById('result');
    const reader = new Html5Qrcode("reader");
    let isProcessing = false; // Variable to track if QR code is being processed

    const video = document.getElementById('video');
    const cameraSelect = document.getElementById('camera-select');
    // Function to setup the camera
    async function setupCamera(deviceId) {
        try {
            const constraints = {
                video: {
                    deviceId: deviceId ? { exact: deviceId } : undefined
                }
            };
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
        } catch (error) {
            console.error('Error accessing the camera:', error);
        }
    }

    // Function to list available cameras
    async function listCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            cameraSelect.innerHTML = '';
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Camera ${index + 1}`;
                cameraSelect.appendChild(option);
            });
            if (videoDevices.length > 0) {
                // Try to select the back camera by default
                const backCamera = videoDevices.find(device => device.label.toLowerCase().includes('back'));
                if (backCamera) {
                    cameraSelect.value = backCamera.deviceId;
                }
                setupCamera(cameraSelect.value);
            }
        } catch (error) {
            console.error('Error listing cameras:', error);
        }
    }

    // Change camera when a different option is selected
    cameraSelect.addEventListener('change', () => {
        setupCamera(cameraSelect.value);
    });

    // List available cameras when the page loads
    await listCameras();

    // Function to handle the QR scan result
    async function handleQrCode(content) {

        if (isProcessing) return; // Prevent multiple simultaneous processing
        isProcessing = true;

        resultDiv.innerHTML = `Processing QR Code...`;
        try {
            const response = await fetch('/process_qr', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ qr_data: content }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === "success") {
                displayQRInfo(data.data);
            } else {
                resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            resultDiv.innerHTML = '<div class="alert alert-danger">An error occurred while processing the QR code.</div>';
        } finally {
            isProcessing = false; // Reset processing flag
        }
    }

    // Function to display the QR info in an HTML table
    function displayQRInfo(qrData) {
        const table = document.createElement('table');
        table.classList.add('table', 'table-bordered');

        // Create rows for each QR field
        for (const [key, value] of Object.entries(qrData)) {
            const row = table.insertRow();
            const cell1 = row.insertCell(0);
            const cell2 = row.insertCell(1);
            cell1.textContent = key;
            cell2.textContent = value;
        }

        // Clear previous content and append the table to the result div
        resultDiv.innerHTML = '';
        resultDiv.appendChild(table);
    }

    // Start the QR scanner
    reader.start({ facingMode: "environment" }, {
        fps: 10,
        qrbox: 250
    }, qrCodeMessage => {
        console.log(`QR Code detected: ${qrCodeMessage}`);
        handleQrCode(qrCodeMessage);
    }).catch(err => {
        console.error(`Unable to start scanning, error: ${err}`);
        resultDiv.innerHTML = '<div class="alert alert-danger">Unable to start scanning. Please ensure camera permissions are granted.</div>';
    });
});
