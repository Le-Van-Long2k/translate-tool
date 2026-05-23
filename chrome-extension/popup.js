/////////////
// popup.js
/////////////

document.addEventListener('DOMContentLoaded', () => {
  console.log('[Popup] Popup loaded');

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

    const mode = modeSelect?.value;

    console.log('[Popup] Save settings:', {
      source,
      target,
      mode
    });

    // TODO:
    // chrome.storage.local.set(...)
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
        alert('Không tìm thấy tab hiện tại.');

        return;
      }

      if (/^(chrome|edge|about|view-source):/.test(tab.url)) {
        alert('Không thể chọn vùng trên trang nội bộ.');

        return;
      }

      console.log('[Popup] Active tab:', tab.id, tab.url);

      // inject content.js
      try {
        await chrome.scripting.executeScript({
          target: {
            tabId: tab.id
          },
          files: ['content.js']
        });

        console.log('[Popup] content.js injected');

        // IMPORTANT:
        // wait content.js initialize
        await new Promise((resolve) => setTimeout(resolve, 300));

        // ping content script first
        chrome.tabs.sendMessage(
          tab.id,
          {
            type: 'PING'
          },
          (pingResponse) => {
            if (chrome.runtime.lastError) {
              console.error(
                '[Popup] Content script not ready:',
                chrome.runtime.lastError.message
              );

              alert('Content script chưa sẵn sàng.');

              return;
            }

            console.log('[Popup] Ping success:', pingResponse);

            // START_SELECTION
            chrome.tabs.sendMessage(
              tab.id,
              {
                type: 'START_SELECTION'
              },
              (response) => {
                if (chrome.runtime.lastError) {
                  console.error(
                    '[Popup] START_SELECTION failed:',
                    chrome.runtime.lastError.message
                  );

                  alert('Không thể bắt đầu chọn vùng.');
                } else {
                  console.log('[Popup] Selection started', response);

                  window.close();
                }
              }
            );
          }
        );
      } catch (err) {
        console.error('[Popup] Injection failed:', err);

        alert('Không thể inject content script.');
      }
    } catch (err) {
      console.error('[Popup] Region selection error:', err);
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
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: false
      });

      console.log('[Popup] Stream selected:', stream);

      alert('Đã chọn màn hình stream thành công.');

      // TODO:
      // save stream
      // send to background
    } catch (err) {
      console.error('[Popup] Stream select failed:', err);
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
