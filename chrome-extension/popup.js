/////////////
// popup.js
/////////////

document.addEventListener('DOMContentLoaded', () => {
  console.log('[Popup] Popup loaded');

  // =========================
  // TOAST NOTIFICATION
  // =========================

  function showToast(message, isError = false) {
    console.log('[Toast]', message);

    // Create alert-style modal
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: ${isError ? '#dc2626' : '#10b981'};
      color: white;
      padding: 20px 30px;
      border-radius: 10px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      z-index: 9999;
      font-size: 16px;
      text-align: center;
      min-width: 250px;
      animation: zoomIn 0.3s ease-out;
    `;
    modal.textContent = message;

    document.body.appendChild(modal);

    // Auto close after 3 seconds
    setTimeout(() => {
      modal.style.animation = 'zoomOut 0.3s ease-in';
      setTimeout(() => {
        modal.remove();
      }, 300);
    }, 3000);
  }

  // Add animations to style
  const style = document.createElement('style');
  style.textContent = `
    @keyframes zoomIn {
      from {
        opacity: 0;
        transform: translate(-50%, -50%) scale(0.8);
      }
      to {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
      }
    }
    
    @keyframes zoomOut {
      from {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
      }
      to {
        opacity: 0;
        transform: translate(-50%, -50%) scale(0.8);
      }
    }
  `;
  document.head.appendChild(style);

  // =========================
  // MODE
  // =========================

  const modeSelect = document.getElementById('mode');

  // SETTINGS MAP
  const settingsMap = {
    manga_auto: document.getElementById('mangaAutoSettings'),

    manga_manual: document.getElementById('mangaManualSettings'),

    screenshot: document.getElementById('screenshotSettings'),

    stream: document.getElementById('streamSettings')
  };

  // ACTIONS MAP
  const actionsMap = {
    manga_auto: document.getElementById('mangaAutoActions'),

    manga_manual: document.getElementById('mangaManualActions'),

    screenshot: document.getElementById('screenshotActions'),

    stream: document.getElementById('streamActions')
  };

  // =========================
  // HIDE ALL
  // =========================

  function hideAllSections() {
    Object.values(settingsMap).forEach((el) => {
      el?.classList.add('hidden');
    });

    Object.values(actionsMap).forEach((el) => {
      el?.classList.add('hidden');
    });
  }

  // =========================
  // UPDATE MODE UI
  // =========================

  function updateModeUI() {
    const mode = modeSelect?.value;

    console.log('[Popup] Current mode:', mode);

    hideAllSections();

    settingsMap[mode]?.classList.remove('hidden');

    actionsMap[mode]?.classList.remove('hidden');
  }

  modeSelect?.addEventListener('change', updateModeUI);

  updateModeUI();

  // =========================
  // SAVE SETTINGS
  // =========================

  const submitSettingBtn = document.getElementById('submitSettingBtn');

  submitSettingBtn?.addEventListener('click', async () => {
    const source = document.getElementById('sourceLang')?.value;

    const target = document.getElementById('targetLang')?.value;

    console.log('[Popup] Save settings:', {
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

      console.log('[Popup] Settings saved successfully');

      // Show success message to user
      showToast('✓ Cài đặt đã được lưu thành công!');
    } catch (err) {
      console.error('[Popup] Failed to save settings:', err);

      showToast('✗ Lỗi khi lưu cài đặt. Vui lòng thử lại.', true);
    }
  });

  // =========================
  // VIEW RESULT BUTTONS
  // =========================

  const viewButtons = document.querySelectorAll('.viewResultsBtn');

  viewButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      console.log('[Popup] View results clicked');

      const resultUrl = chrome.runtime.getURL('result.html');

      chrome.tabs.create({
        url: resultUrl
      });

      window.close();
    });
  });

  // =========================
  // REGION SELECTION
  // =========================

  async function startRegionSelection() {
    console.log('[Popup] Starting region selection');

    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
      });

      if (!tab || !tab.url) {
        showToast('Không tìm thấy tab hiện tại.', true);
        return;
      }

      // Check if the page allows content scripts
      if (
        /^(chrome|edge|about|view-source|file|moz-extension|chrome-extension):/.test(
          tab.url
        )
      ) {
        showToast('Không thể chọn vùng trên trang nội bộ.', true);
        return;
      }

      console.log('[Popup] Active tab:', tab.id, tab.url);

      // Try to inject content.js with better error handling
      try {
        await chrome.scripting.executeScript({
          target: {
            tabId: tab.id,
            allFrames: false
          },
          files: ['content.js']
        });

        console.log('[Popup] content.js injected successfully');
      } catch (injectErr) {
        console.error('[Popup] Failed to inject content.js:', injectErr);
        showToast(
          'Không thể inject script vào trang này. Vui lòng thử trang khác.',
          true
        );
        return;
      }

      // Wait for content.js to initialize
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Send PING message to verify content script is ready
      chrome.tabs.sendMessage(tab.id, { type: 'PING' }, (pingResponse) => {
        if (chrome.runtime.lastError) {
          console.error(
            '[Popup] Content script not ready:',
            chrome.runtime.lastError.message
          );
          showToast('Content script chưa sẵn sàng.', true);
          return;
        }

        console.log('[Popup] Ping success:', pingResponse);

        // Send START_SELECTION message
        chrome.tabs.sendMessage(
          tab.id,
          { type: 'START_SELECTION' },
          (response) => {
            if (chrome.runtime.lastError) {
              console.error(
                '[Popup] START_SELECTION failed:',
                chrome.runtime.lastError.message
              );
              showToast('Không thể bắt đầu chọn vùng.', true);
            } else {
              console.log('[Popup] Selection started', response);
              window.close();
            }
          }
        );
      });
    } catch (err) {
      console.error('[Popup] Region selection error:', err);
      showToast('Lỗi: ' + err.message, true);
    }
  }

  // =========================
  // SET REGION BUTTONS
  // =========================

  const regionButtons = document.querySelectorAll('.setRegionBtn');

  regionButtons.forEach((btn) => {
    btn.addEventListener('click', startRegionSelection);
  });

  // =========================
  // SELECT SCREEN STREAM
  // =========================

  const selectScreenBtn = document.getElementById('selectScreenBtn');

  selectScreenBtn?.addEventListener('click', async () => {
    console.log('[Popup] Select stream screen');

    try {
      // Open stream display page
      const streamUrl = chrome.runtime.getURL('stream.html');

      chrome.tabs.create(
        {
          url: streamUrl
        },
        (newTab) => {
          console.log('[Popup] Stream tab created:', newTab.id);
          showToast('✓ Đã mở tab stream thành công! Chọn màn hình để stream.');
          window.close();
        }
      );
    } catch (err) {
      console.error('[Popup] Stream select failed:', err);
      showToast('✗ Lỗi: Không thể mở tab stream.', true);
    }
  });

  // =========================
  // START BUTTONS
  // =========================

  const startButtons = document.querySelectorAll('.startBtn');

  startButtons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      const mode = modeSelect.value;

      console.log('[Popup] Start mode:', mode);

      // TODO:
      // start OCR loop
      // send message to background
    });
  });

  // =========================
  // STOP BUTTONS
  // =========================

  const stopButtons = document.querySelectorAll('.stopBtn');

  stopButtons.forEach((btn) => {
    btn.addEventListener('click', async () => {
      console.log('[Popup] Stop clicked');

      // TODO:
      // stop OCR loop
      // stop stream
    });
  });
});
