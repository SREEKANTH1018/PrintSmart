// Drag and Drop for Upload
const dropZone = document.getElementById('drop-zone');
if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.background = 'rgba(0,255,255,0.2)';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.background = 'rgba(255,255,255,0.1)';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length) {
            document.getElementById('file-input').files = files;
            updatePreview(files[0]);
        }
    });
}

function updatePreview(file) {
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = (file.size / 1024).toFixed(2) + ' KB';
}

// Price Calculator
function calculatePrice() {
    const copies = document.getElementById('copies').value;
    const color = document.getElementById('color').checked;
    const sides = document.getElementById('sides').value;
    let price = (color ? 2 : 1) * copies;
    if (sides === 'double') price *= 1.5;
    document.getElementById('price').textContent = '₹' + price.toFixed(2);
}

// Attach to elements if present
document.addEventListener('DOMContentLoaded', () => {
    const copiesInput = document.getElementById('copies');
    if (copiesInput) {
        copiesInput.addEventListener('input', calculatePrice);
        document.getElementById('color').addEventListener('change', calculatePrice);
        document.getElementById('sides').addEventListener('change', calculatePrice);
    }
});
