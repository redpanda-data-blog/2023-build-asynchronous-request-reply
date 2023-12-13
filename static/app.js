document.getElementById('imageInput').addEventListener('change', function (event) {
    let reader = new FileReader();
    reader.onload = function () {
        let output = document.getElementById('selectedImage');
        output.src = reader.result;
    };
    reader.readAsDataURL(event.target.files[0]);
});

document.getElementById('processButton').addEventListener('click', async function () {
    let imageInput = document.getElementById('imageInput');
    let file = imageInput.files[0];
    let formData = new FormData();
    formData.append("file", file);

    await fetch('/upload-image/', {
        method: 'POST',
        body: formData
    });
});

async function connectWebSocket() {
    let socket = new WebSocket('ws://localhost:8000/ws');
    socket.onmessage = function (event) {
        console.log("got data: " + event.data);
        let imageGrid = document.getElementById('imageGrid');
        let newImage = document.createElement('img');
        newImage.src = `static/images/${event.data}`;
        newImage.classList.add('max-h-32');
        imageGrid.appendChild(newImage);
    };
}

connectWebSocket();