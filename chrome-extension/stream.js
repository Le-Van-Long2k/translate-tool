// stream.js
console.log('[Stream] Stream page loaded');

let currentStream = null;
const videoElement = document.getElementById('videoStream');
const stopBtn = document.getElementById('stopStreamBtn');
const statusMsg = document.getElementById('statusMsg');
const setRegionBtn = document.getElementById('setRegionBtn');
const startBtn = document.getElementById('startBtn');
const viewResultsBtn = document.getElementById('viewResultsBtn');
const screenChangesMode = document.getElementById('screenChangesMode');
const intervalMode = document.getElementById('intervalMode');
const intervalInput = document.getElementById('intervalInput');
const sourceLangSelect = document.getElementById('sourceLang');
const targetLangSelect = document.getElementById('targetLang');
const submitSettingBtn = document.getElementById('submitSettingBtn');
const toastElement = document.getElementById('toast');

let isSelectingRegion = false;
let selectionStartX = 0;
let selectionStartY = 0;
let selectionRect = null;
let isStreamActive = false;

// Toast notification function
function showToast(message, isError = false) {
  console.log('[Toast]', message);

  toastElement.textContent = message;
  toastElement.className = isError ? 'toast error' : 'toast';
  toastElement.classList.remove('hidden');

  // Auto close after 3 seconds
  setTimeout(() => {
    toastElement.classList.add('hidden');
  }, 3000);
}

// Load saved language settings on page load
function loadSavedSettings() {
  chrome.storage.local.get(['sourceLang', 'targetLang'], (data) => {
    if (data.sourceLang) {
      sourceLangSelect.value = data.sourceLang;
      console.log('[Stream] Loaded source language:', data.sourceLang);
    }
    if (data.targetLang) {
      targetLangSelect.value = data.targetLang;
      console.log('[Stream] Loaded target language:', data.targetLang);
    }
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  console.log('[Stream] DOM loaded, initializing stream...');

  // Load saved settings
  loadSavedSettings();

  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    console.log('[Stream] Received message:', msg.type);

    if (msg.type === 'STREAM_READY') {
      console.log('[Stream] Stream is ready in popup');
      sendResponse({ received: true });
    }
  });

  // Try to get stream from background/popup first
  // If that fails, request a new stream
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'REQUEST_STREAM'
    });

    console.log('[Stream] Background response:', response);

    if (response && response.success && response.streamData) {
      console.log('[Stream] Stream data received from background');
      updateStatus('✓ Stream đang chạy...', 'success');
    } else {
      console.log('[Stream] No stream from background, requesting new one');
      await requestNewStream();
    }
  } catch (err) {
    console.error('[Stream] Error getting stream from background:', err);
    console.log('[Stream] Requesting new stream from user...');
    await requestNewStream();
  }

  // Stop button handler
  stopBtn.addEventListener('click', stopStream);

  // Set region button handler
  setRegionBtn.addEventListener('click', startRegionSelection);

  // Start button handler
  startBtn.addEventListener('click', startTranslation);

  // View Results button handler
  viewResultsBtn.addEventListener('click', viewResults);

  // Save Settings button handler
  submitSettingBtn.addEventListener('click', saveLanguageSettings);

  // Disable interval input when Screen Changes is selected
  screenChangesMode.addEventListener('change', () => {
    intervalInput.disabled = true;
  });

  // Enable interval input when Interval is selected
  intervalMode.addEventListener('change', () => {
    intervalInput.disabled = false;
  });

  // Monitor stream status
  if (videoElement.srcObject) {
    videoElement.srcObject.getTracks().forEach((track) => {
      track.onended = () => {
        console.log('[Stream] Track ended:', track.kind);
        updateStatus('Stream bị dừng', 'error');
        isStreamActive = false;
        setTimeout(() => {
          window.close();
        }, 2000);
      };
    });
  }
});

// Save language settings
async function saveLanguageSettings() {
  const source = sourceLangSelect.value;
  const target = targetLangSelect.value;

  console.log('[Stream] Save settings:', {
    source,
    target
  });

  try {
    // Save settings to Chrome storage
    await chrome.storage.local.set({
      sourceLang: source,
      targetLang: target
    });

    // Call API to set config
    const apiResponse = await fetch('http://localhost:8052/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source_lang: source,
        target_lang: target,
        font_size_ratio: null,
        detect_model: null,
        ocr_model: null,
        inpaint_model: null,
        translate_model: null
      })
    });

    if (!apiResponse.ok) {
      throw new Error(`API error: ${apiResponse.status}`);
    }

    console.log('[Stream] Settings saved successfully');

    // Show success message to user
    showToast('✓ Cài đặt đã được lưu thành công!');
  } catch (err) {
    console.error('[Stream] Failed to save settings:', err);

    showToast('✗ Lỗi khi lưu cài đặt. Vui lòng thử lại.', true);
  }
}

async function requestNewStream() {
  try {
    console.log('[Stream] Requesting display media from user...');
    updateStatus('Chọn màn hình để stream...', 'loading');

    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        cursor: 'always'
      },
      audio: false
    });

    console.log('[Stream] New stream obtained:', stream);

    currentStream = stream;
    videoElement.srcObject = stream;

    updateStatus('✓ Stream đang chạy...', 'success');

    // Monitor for stream end
    stream.getTracks().forEach((track) => {
      track.onended = () => {
        console.log('[Stream] Track ended:', track.kind);
        updateStatus('Stream bị dừng', 'error');
        setTimeout(() => {
          window.close();
        }, 2000);
      };
    });

    // Notify background that stream is active
    chrome.runtime.sendMessage(
      {
        type: 'STREAM_ACTIVE',
        streamData: {
          trackCount: stream.getTracks().length,
          videoTracks: stream.getVideoTracks().length,
          audioTracks: stream.getAudioTracks().length
        }
      },
      (response) => {
        if (chrome.runtime.lastError) {
          console.log(
            '[Stream] Note: Could not notify background:',
            chrome.runtime.lastError.message
          );
        } else {
          console.log('[Stream] Background notified:', response);
        }
      }
    );
  } catch (err) {
    console.error('[Stream] Error requesting stream:', err);

    if (err.name === 'NotAllowedError') {
      updateStatus('❌ Stream bị từ chối', 'error');
    } else if (err.name === 'NotFoundError') {
      updateStatus('❌ Không tìm thấy màn hình', 'error');
    } else {
      updateStatus(`❌ Lỗi: ${err.message}`, 'error');
    }

    setTimeout(() => {
      window.close();
    }, 3000);
  }
}

function stopStream() {
  console.log('[Stream] Stopping stream...');
  updateStatus('Dừng stream...', 'loading');

  if (currentStream) {
    currentStream.getTracks().forEach((track) => {
      console.log('[Stream] Stopping track:', track.kind);
      track.stop();
    });
    currentStream = null;
  }

  videoElement.srcObject = null;

  // Notify background
  chrome.runtime.sendMessage({ type: 'STOP_STREAM' }, (response) => {
    if (!chrome.runtime.lastError) {
      console.log('[Stream] Stop message sent:', response);
    }
    setTimeout(() => {
      window.close();
    }, 500);
  });
}

function updateStatus(message, type = 'success') {
  console.log('[Stream] Status:', message);
  statusMsg.textContent = message;
  statusMsg.className = `status ${type}`;
}

function startRegionSelection() {
  console.log('[Stream] Starting region selection');

  if (isSelectingRegion) {
    console.log('[Stream] Cancelling region selection');
    cancelRegionSelection();
    return;
  }

  isSelectingRegion = true;
  setRegionBtn.classList.add('active');
  updateStatus('Kéo để chọn vùng...', 'loading');

  // Create overlay
  const overlay = document.createElement('div');
  overlay.id = 'selection-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);
    cursor: crosshair;
    z-index: 10000;
  `;

  // Create rectangle element
  const rect = document.createElement('div');
  rect.id = 'selection-rect';
  rect.style.cssText = `
    position: fixed;
    border: 2px solid #3b82f6;
    background: rgba(59, 130, 246, 0.1);
    display: none;
    z-index: 10001;
    pointer-events: none;
  `;

  overlay.appendChild(rect);
  document.body.appendChild(overlay);

  let startX = 0;
  let startY = 0;

  overlay.addEventListener('mousedown', (e) => {
    startX = e.clientX;
    startY = e.clientY;
    rect.style.display = 'block';
    rect.style.left = startX + 'px';
    rect.style.top = startY + 'px';
    rect.style.width = '0px';
    rect.style.height = '0px';
  });

  overlay.addEventListener('mousemove', (e) => {
    if (e.buttons !== 1) return; // Only if mouse button is pressed

    const currentX = e.clientX;
    const currentY = e.clientY;

    const width = Math.abs(currentX - startX);
    const height = Math.abs(currentY - startY);

    rect.style.left = Math.min(startX, currentX) + 'px';
    rect.style.top = Math.min(startY, currentY) + 'px';
    rect.style.width = width + 'px';
    rect.style.height = height + 'px';
  });

  overlay.addEventListener('mouseup', (e) => {
    const endX = e.clientX;
    const endY = e.clientY;

    const x = Math.min(startX, endX);
    const y = Math.min(startY, endY);
    const width = Math.abs(endX - startX);
    const height = Math.abs(endY - startY);

    if (width > 10 && height > 10) {
      // Valid selection
      selectionRect = { x, y, width, height };
      saveRegion(selectionRect);
      console.log('[Stream] Region selected:', selectionRect);
      updateStatus('✓ Vùng đã lưu!', 'success');
    } else {
      console.log('[Stream] Selection too small');
      updateStatus('Vùng quá nhỏ, hãy thử lại', 'error');
    }

    overlay.remove();
    isSelectingRegion = false;
    setRegionBtn.classList.remove('active');
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      console.log('[Stream] Selection cancelled');
      overlay.remove();
      isSelectingRegion = false;
      setRegionBtn.classList.remove('active');
      updateStatus('✓ Stream đang chạy...', 'success');
    }
  });

  // Also allow ESC to cancel
  const cancelHandler = (e) => {
    if (e.key === 'Escape') {
      console.log('[Stream] Selection cancelled with ESC');
      overlay.remove();
      isSelectingRegion = false;
      setRegionBtn.classList.remove('active');
      updateStatus('✓ Stream đang chạy...', 'success');
      document.removeEventListener('keydown', cancelHandler);
    }
  };
  document.addEventListener('keydown', cancelHandler);
}

function cancelRegionSelection() {
  isSelectingRegion = false;
  setRegionBtn.classList.remove('active');
  const overlay = document.getElementById('selection-overlay');
  if (overlay) {
    overlay.remove();
  }
  updateStatus('✓ Stream đang chạy...', 'success');
}

function saveRegion(rect) {
  console.log('[Stream] Saving region:', rect);
  chrome.storage.local.set(
    {
      streamRegion: rect
    },
    () => {
      console.log('[Stream] Region saved to storage');
    }
  );

  // Also notify background
  chrome.runtime.sendMessage(
    {
      type: 'REGION_SELECTED',
      region: rect
    },
    (response) => {
      if (!chrome.runtime.lastError) {
        console.log('[Stream] Region sent to background:', response);
      }
    }
  );
}

function startTranslation() {
  console.log('[Stream] Start translation clicked');

  const captureMode = screenChangesMode.checked ? 'screen_changes' : 'interval';
  const interval = intervalInput.value;

  console.log('[Stream] Capture mode:', captureMode, 'Interval:', interval);

  // Check if stream is active
  if (!currentStream || !videoElement.srcObject) {
    updateStatus('❌ Stream không hoạt động', 'error');
    return;
  }

  // Check if region is selected
  chrome.storage.local.get('streamRegion', (data) => {
    if (!data.streamRegion) {
      updateStatus('❌ Chưa chọn vùng', 'error');
      alert('Vui lòng chọn vùng trước khi dịch');
      return;
    }

    isStreamActive = true;
    updateStatus('▶ Bắt đầu dịch...', 'loading');

    // Send start message to background
    chrome.runtime.sendMessage(
      {
        type: 'START_STREAM_TRANSLATION',
        captureMode: captureMode,
        interval: interval,
        region: data.streamRegion
      },
      (response) => {
        if (chrome.runtime.lastError) {
          console.error(
            '[Stream] Error starting translation:',
            chrome.runtime.lastError
          );
          updateStatus('❌ Lỗi: Không thể bắt đầu dịch', 'error');
          isStreamActive = false;
        } else {
          console.log('[Stream] Translation started:', response);
          updateStatus('✓ Đang dịch...', 'success');
        }
      }
    );
  });
}

function viewResults() {
  console.log('[Stream] View results clicked');

  const resultUrl = chrome.runtime.getURL('result.html');

  chrome.tabs.create({
    url: resultUrl
  });
}
