let currentImageUrl = null;

function loadImage() {
    chrome.storage.local.get('resultImage', (data) => {
        console.log('[Result] Storage data retrieved');
        if (data.resultImage) {
            console.log('[Result] Loading image from storage, URL length:', data.resultImage.length);
            const content = document.getElementById('content');
            const img = new Image();
            img.src = data.resultImage;
            img.onload = () => {
                console.log('[Result] Image loaded successfully');
                content.innerHTML = '';
                content.appendChild(img);
                currentImageUrl = data.resultImage;
            };
            img.onerror = (err) => {
                console.error('[Result] Image load error:', err);
                content.textContent = 'Lỗi tải ảnh';
            };
        } else {
            console.log('[Result] No resultImage in storage');
        }
    });
}


// Load image on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Result] Page loaded, calling loadImage()');
    loadImage();

    // Listen for storage changes
    chrome.storage.onChanged.addListener((changes, areaName) => {
        console.log('[Result] Storage changed event');
        if (areaName === 'local' && changes.resultImage) {
            console.log('[Result] resultImage changed, reloading...');
            loadImage();
        }
    });

    // Auto-reload every 2 seconds to check for new results
    setInterval(() => {
        console.log('[Result] Auto-refreshing...');
        loadImage();
    }, 2000);
});
