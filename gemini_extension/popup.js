const HOST_NAME = "com.gemini.tool";
const BACKEND   = "http://127.0.0.1:8765";

let isRunning  = false;
let port       = null;
let pollTimer  = null;
let startTimer = null;   // timeout watchdog khi dang start

// ── UI helpers ────────────────────────────────────────────
function setDot(elId, state) {
  const el = document.getElementById(elId);
  const labels = { on: "Online", off: "Offline", loading: "Starting…" };
  el.innerHTML = `<span class="dot ${state}"></span>${labels[state]}`;
}

function addLog(msg, cls = "") {
  const log = document.getElementById("log-area");
  const now = new Date().toLocaleTimeString("vi-VN",
    { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const line = document.createElement("div");
  if (cls) line.className = cls;
  line.textContent = `[${now}] ${msg}`;
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}

function setBtn(running) {
  const btn = document.getElementById("btn-toggle");
  isRunning = running;
  btn.disabled = false;
  if (running) {
    btn.textContent = "■  Dừng";
    btn.className = "btn-main btn-stop";
  } else {
    btn.textContent = "▶  Bắt đầu";
    btn.className = "btn-main btn-start";
  }
}

function setError(msg) {
  setDot("st-bridge",  "off");
  setDot("st-scanner", "off");
  setBtn(false);
  if (startTimer) { clearTimeout(startTimer); startTimer = null; }
  addLog(msg, "err");
}

// ── Poll bridge server for queue stats ────────────────────
async function pollStats() {
  try {
    const res  = await fetch(`${BACKEND}/next_link`,
      { signal: AbortSignal.timeout(2000) });
    const data = await res.json();
    document.getElementById("stat-links").textContent = data.remaining ?? "—";
    setDot("st-bridge", "on");
  } catch {
    setDot("st-bridge", "off");
    document.getElementById("stat-links").textContent = "—";
  }
}
function startPolling() { pollStats(); pollTimer = setInterval(pollStats, 4000); }
function stopPolling()  { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

// ── Native Messaging ──────────────────────────────────────
function connectNativeHost() {
  if (port) return true;
  try {
    port = chrome.runtime.connectNative(HOST_NAME);

    port.onMessage.addListener((msg) => {
      // Clear watchdog nếu có
      if (startTimer) { clearTimeout(startTimer); startTimer = null; }

      if (msg.error) {
        setError("Native host lỗi: " + msg.error);
        return;
      }

      // Response từ { action: "start" }
      if (msg.bridge_pid !== undefined) {
        if (msg.ok) {
          addLog(`Bridge PID:${msg.bridge_pid} | Scanner PID:${msg.scanner_pid}`, "ok");
          setDot("st-bridge",  "loading"); // chờ server khởi động ~2s
          setDot("st-scanner", "on");
          setBtn(true);
          // Đợi bridge server ready rồi poll
          setTimeout(startPolling, 2000);
        } else {
          setError("Khởi động thất bại");
        }
        return;
      }

      // Response từ { action: "stop" }
      if (msg.killed !== undefined) {
        addLog(`Đã dừng`, "warn");
        setDot("st-bridge",  "off");
        setDot("st-scanner", "off");
        setBtn(false);
        stopPolling();
        return;
      }

      // Response từ { action: "status" }
      if (msg.bridge !== undefined) {
        setDot("st-bridge",  msg.bridge  ? "on" : "off");
        setDot("st-scanner", msg.scanner ? "on" : "off");
        setBtn(msg.bridge || msg.scanner);
        if (msg.bridge || msg.scanner) startPolling();
        return;
      }
    });

    port.onDisconnect.addListener(() => {
      const err = chrome.runtime.lastError;
      port = null;
      if (startTimer) { clearTimeout(startTimer); startTimer = null; }

      const errMsg = err ? err.message : "";
      if (errMsg.includes("not found") || errMsg.includes("cannot find")) {
        document.getElementById("setup-warn").style.display = "block";
        setError("Chưa cài native host → chạy setup_native_host.bat");
      } else if (errMsg.includes("Access")) {
        setError("Lỗi quyền truy cập native host");
      } else {
        // Disconnected sau khi dùng xong — bình thường với connectNative
        setBtn(false);
        stopPolling();
        addLog("Native host đã ngắt kết nối", "warn");
      }
    });

    return true;
  } catch (e) {
    document.getElementById("setup-warn").style.display = "block";
    setError("Không kết nối native host: " + e.message);
    return false;
  }
}

// ── Button ────────────────────────────────────────────────
document.getElementById("btn-toggle").addEventListener("click", () => {
  const btn = document.getElementById("btn-toggle");
  btn.disabled = true;

  if (!isRunning) {
    // START
    btn.textContent = "⌛ Đang khởi động…";
    setDot("st-bridge",  "loading");
    setDot("st-scanner", "loading");
    addLog("Đang khởi động...", "warn");

    const ok = connectNativeHost();
    if (!ok) { btn.disabled = false; return; }

    // Watchdog: nếu 6s không có response → báo lỗi
    startTimer = setTimeout(() => {
      startTimer = null;
      if (!isRunning) {
        setError("Timeout — native host không phản hồi. Chạy lại setup_native_host.bat?");
        document.getElementById("setup-warn").style.display = "block";
      }
    }, 6000);

    setTimeout(() => { if (port) port.postMessage({ action: "start" }); }, 400);

  } else {
    // STOP
    btn.textContent = "⌛ Đang dừng…";
    addLog("Đang dừng...", "warn");
    stopPolling();
    if (port) {
      port.postMessage({ action: "stop" });
      // Watchdog dừng
      setTimeout(() => { if (isRunning) setBtn(false); }, 3000);
    } else {
      setBtn(false);
    }
  }
});

// ── Init ──────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  addLog("Extension sẵn sàng");

  // Load activated count
  chrome.storage.local.get(["activatedCount"], (res) => {
    if (res.activatedCount)
      document.getElementById("stat-activated").textContent = res.activatedCount;
  });

  // Kết nối native host để check status ngay (không block UI)
  const ok = connectNativeHost();
  if (ok) {
    setTimeout(() => { if (port) port.postMessage({ action: "status" }); }, 300);
  }

  // Thử poll bridge server ngay — nếu đang chạy sẵn sẽ hiện stats
  pollStats();
});
