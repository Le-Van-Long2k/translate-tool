/////////////
// popup.js
// ===== DOM READY =====
document.addEventListener("DOMContentLoaded", () => {
  console.log("[Popup] Popup loaded");

  const setBtn = document.getElementById("setRegion");
  const clearBtn = document.getElementById("clearRegion");
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
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
      });

      console.log("[Popup] content.js injected");

      // Send message to start selection mode
      chrome.tabs.sendMessage(tab.id, { type: "START_SELECTION" }, () => {
        if (chrome.runtime.lastError) {
          console.error("[Popup] START_SELECTION failed:", chrome.runtime.lastError.message);
          alert("Không thể bắt đầu chọn vùng. Hãy thử lại trên một trang web bình thường.");
        } else {
          console.log("[Popup] Message sent: START_SELECTION");
        }

        window.close();
      });

    } catch (err) {
      console.error("[Popup] Error while setting region:", err);
    }
  };

  // ===== CLEAR REGION BUTTON =====
  clearBtn.onclick = () => {
    console.log("[Popup] Clear region button clicked");

    chrome.storage.local.remove("rect", () => {
      console.log("[Popup] Saved region removed");

      // Optional feedback
      alert("Capture area has been cleared");
    });
  };
});