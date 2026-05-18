/////////////
// popup.js
// ===== DOM READY =====
document.addEventListener("DOMContentLoaded", () => {
  console.log("[Popup] Popup loaded");

  const setBtn = document.getElementById("setRegion");
  const viewBtn = document.getElementById("viewResults");

  // ===== VIEW RESULTS BUTTON =====
  if (viewBtn) {
    viewBtn.onclick = () => {
      console.log("[Popup] View results button clicked");
      const resultUrl = chrome.runtime.getURL("result.html");
      console.log("[Popup] Opening result page:", resultUrl);
      chrome.tabs.create({ url: resultUrl });
      window.close();
    };
  }

  // ===== SET REGION BUTTON =====
  setBtn.onclick = async () => {
    console.log("[Popup] Set region button clicked");

    try {
      // Get current active tab
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
      });

      if (!tab || !tab.url) {
        alert("Không tìm thấy tab hiện tại. Vui lòng thử lại.");
        return;
      }

      if (/^(chrome|edge|about|view-source):/.test(tab.url)) {
        alert("Không thể chọn vùng trên trang nội bộ. Vui lòng mở một trang web bình thường.");
        return;
      }

      console.log("[Popup] Active tab:", tab.id, tab.url);

      // Inject content script to ensure it's loaded
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"]
        });
        console.log("[Popup] content.js injected");
      } catch (injectionErr) {
        console.error("[Popup] Failed to inject content.js:", injectionErr);
      }

      // Send message to start selection mode using Promise-based API
      chrome.tabs.sendMessage(tab.id, { type: "START_SELECTION" }, (response) => {
        if (chrome.runtime.lastError) {
          console.error("[Popup] START_SELECTION failed:", chrome.runtime.lastError.message);
        } else {
          console.log("[Popup] Message sent successfully, response:", response);
        }

        window.close();
      });

    } catch (err) {
      console.error("[Popup] Error while setting region:", err);
    }
  };

});