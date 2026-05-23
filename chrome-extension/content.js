// content.js
(function () {
  // Prevent duplicate injection
  if (window.__capture_installed__) return;
  window.__capture_installed__ = true;

  console.log('[Content] Script loaded');

  let savedRect = null;

  // Load saved region
  chrome.storage.local.get('rect', (data) => {
    savedRect = data.rect;
    console.log('[Content] Loaded saved rect:', savedRect);
  });

  // Listen messages
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'PING') {
      console.log('[Content] PING received');
      sendResponse({ status: 'pong' });
      return true;
    }

    if (msg.type === 'START_SELECTION') {
      console.log('[Content] Start selection triggered');
      startSelection();
      sendResponse({ status: 'selection_started' });
      return true;
    }

    if (msg.type === 'CAPTURE_SAVED') {
      console.log('[Content] Capture saved triggered');

      if (!savedRect) {
        alert('No region saved!');
        sendResponse({ status: 'error', message: 'No region saved' });
        return true;
      }

      capture(savedRect);
      sendResponse({ status: 'capture_started' });
      return true;
    }
  });

  function startSelection() {
    const overlay = document.createElement('div');
    Object.assign(overlay.style, {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.2)',
      zIndex: 999999,
      cursor: 'crosshair'
    });

    document.body.appendChild(overlay);

    let startX, startY, box;

    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        overlay.remove();
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.removeEventListener('keydown', onKeyDown);
      }
    };

    const onMouseMove = (e) => {
      const currentX = e.clientX;
      const currentY = e.clientY;
      const left = Math.min(startX, currentX);
      const top = Math.min(startY, currentY);
      const width = Math.abs(currentX - startX);
      const height = Math.abs(currentY - startY);

      box.style.left = left + 'px';
      box.style.top = top + 'px';
      box.style.width = width + 'px';
      box.style.height = height + 'px';
    };

    const onMouseUp = (e) => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('keydown', onKeyDown);

      const rect = {
        x: Math.min(startX, e.clientX),
        y: Math.min(startY, e.clientY),
        width: Math.abs(e.clientX - startX),
        height: Math.abs(e.clientY - startY)
      };

      chrome.storage.local.set({ rect });
      savedRect = rect;

      console.log('[Content] Saved region:', rect);

      overlay.remove();
      alert('Region saved!');
    };

    overlay.onmousedown = (e) => {
      e.preventDefault();
      e.stopPropagation();
      startX = e.clientX;
      startY = e.clientY;

      box = document.createElement('div');
      Object.assign(box.style, {
        position: 'absolute',
        border: '2px dashed red',
        background: 'rgba(255,255,255,0.1)'
      });

      overlay.appendChild(box);
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
      document.addEventListener('keydown', onKeyDown);
    };
  }

  function capture(rect) {
    chrome.runtime.sendMessage({ type: 'capture' }, (res) => {
      const img = new Image();
      img.src = res.dataUrl;

      img.onload = () => {
        const scale = window.devicePixelRatio;

        const canvas = document.createElement('canvas');
        canvas.width = rect.width * scale;
        canvas.height = rect.height * scale;

        const ctx = canvas.getContext('2d');

        ctx.drawImage(
          img,
          rect.x * scale,
          rect.y * scale,
          rect.width * scale,
          rect.height * scale,
          0,
          0,
          canvas.width,
          canvas.height
        );

        canvas.toBlob(
          async (blob) => {
            if (!blob) {
              alert('Không thể tạo ảnh. Vui lòng thử lại.');
              return;
            }

            try {
              const arrayBuffer = await blob.arrayBuffer();
              console.log(
                '[Capture] Sending TRANSLATE_COMIC message with image data...'
              );
              const response = await chrome.runtime.sendMessage({
                type: 'TRANSLATE_COMIC',
                imageData: Array.from(new Uint8Array(arrayBuffer)),
                font_size_ratio: 1.0,
                conf_threshold: 0.25
              });

              console.log('[Capture] Response received:', response);
              if (response.error) {
                throw new Error(response.error);
              }

              const imageUrl = response.imageUrl;
              console.log(
                '[Capture] Saving to storage, URL length:',
                imageUrl.length
              );
              chrome.storage.local.set({ resultImage: imageUrl });
            } catch (err) {
              console.error('[Capture] Fetch error:', err);
              alert(
                'Không thể gửi ảnh lên backend. Hãy khởi động backend hoặc thử lại sau.'
              );
            }
          },
          'image/jpeg',
          0.85
        );
      };
    });
  }
})();
