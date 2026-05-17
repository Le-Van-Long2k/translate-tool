////////////////
// background.js
chrome.commands.onCommand.addListener(async (command) => {
  if (command === "start-capture") {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });

    chrome.tabs.sendMessage(tab.id, { type: "CAPTURE_SAVED" });
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "capture") {
    chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
      sendResponse({ dataUrl });
    });
    return true;
  }

  if (msg.type === "TRANSLATE_COMIC") {
    console.log("[Background] TRANSLATE_COMIC received");
    (async () => {
      try {
        const uint8Array = new Uint8Array(msg.imageData);
        const blob = new Blob([uint8Array], { type: "image/jpeg" });
        const formData = new FormData();
        formData.append("file", blob, "capture.jpg");
        formData.append("font_size", msg.font_size || 32);
        formData.append("conf_threshold", msg.conf_threshold || 0.25);

        console.log("[Background] Sending request to backend...");
        const response = await fetch("http://localhost:8052/translate_comic", {
          method: "POST",
          body: formData
        });

        if (!response.ok) {
          throw new Error(`Backend error: ${response.status}`);
        }

        const translatedBlob = await response.blob();
        const reader = new FileReader();
        
        reader.onload = () => {
          console.log("[Background] FileReader onload, sending response with imageUrl length:", reader.result.length);
          sendResponse({ imageUrl: reader.result });
        };
        
        reader.onerror = () => {
          console.error("[Background] FileReader onerror");
          sendResponse({ error: "Failed to read blob" });
        };
        
        console.log("[Background] Starting FileReader.readAsDataURL...");
        reader.readAsDataURL(translatedBlob);
      } catch (err) {
        console.error("[Background] Fetch error:", err);
        sendResponse({ error: err.message });
      }
    })();

    return true;
  }
});
