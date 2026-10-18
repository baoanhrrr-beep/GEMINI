const BACKEND_URL = "http://127.0.0.1:8765";
let activeTabId = null;
let currentUrl = null;
let isProcessing = false;
let lastProcessTime = Date.now();

// Restore activeTabId from storage if service worker just woke up
chrome.storage.local.get(["activeTabId", "currentUrl"], (res) => {
  if (res.activeTabId) activeTabId = res.activeTabId;
  if (res.currentUrl) currentUrl = res.currentUrl;
});

// Alarm to keep Service Worker alive and poll next link
chrome.alarms.create("gemini_keepalive", { periodInMinutes: 0.2 }); // Every 12 seconds

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "gemini_keepalive") {
    console.log("[EXT] Alarm heartbeat triggered");
    // If stuck for more than 40 seconds, force reset
    if (isProcessing && Date.now() - lastProcessTime > 40000) {
      console.log("[EXT] Processing timed out, resetting lock");
      isProcessing = false;
    }
    if (!isProcessing) {
      checkNextLink();
    }
  }
});

// Poll server for next link to check/activate
async function checkNextLink() {
  if (isProcessing) return;
  isProcessing = true;
  lastProcessTime = Date.now();

  try {
    const res = await fetch(`${BACKEND_URL}/next_link`);
    const data = await res.json();

    if (!data.url) {
      isProcessing = false;
      return;
    }

    currentUrl = data.url;
    chrome.storage.local.set({ currentUrl });
    console.log("[EXT] Processing link:", currentUrl.substring(0, 60) + "...");

    if (activeTabId) {
      try {
        await chrome.tabs.update(activeTabId, { url: currentUrl });
      } catch (e) {
        const tab = await chrome.tabs.create({ url: currentUrl });
        activeTabId = tab.id;
        chrome.storage.local.set({ activeTabId });
      }
    } else {
      const tab = await chrome.tabs.create({ url: currentUrl });
      activeTabId = tab.id;
      chrome.storage.local.set({ activeTabId });
    }
  } catch (err) {
    console.log("[EXT] Backend not connected yet, retrying in 4s...", err);
    isProcessing = false;
    setTimeout(checkNextLink, 4000);
  }
}

// Receive status report from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "report_status") {
    console.log("[EXT] Link result:", message.status, message.url);
    if (sender && sender.tab && sender.tab.id) {
      activeTabId = sender.tab.id;
      chrome.storage.local.set({ activeTabId });
    }

    fetch(`${BACKEND_URL}/report_result`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: message.url || currentUrl,
        status: message.status,
        details: message.details || ""
      })
    })
      .then(() => {
        isProcessing = false;
        // Wait 3 seconds then process next link
        setTimeout(checkNextLink, 3000);
      })
      .catch((err) => {
        console.error("[EXT] Failed to report result:", err);
        isProcessing = false;
        setTimeout(checkNextLink, 3000);
      });
  } else if (message.action === "trigger_next") {
    isProcessing = false;
    checkNextLink();
    sendResponse({ ok: true });
  }
});

// Start checking when extension loads
checkNextLink();
