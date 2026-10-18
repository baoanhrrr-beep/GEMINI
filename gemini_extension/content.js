// Content script running inside Google pages to check Gemini activation links
(function () {
  const currentHref = window.location.href;
  console.log("[EXT Content Script] Checking URL:", currentHref);

  function checkStatus() {
    const text = (document.body ? document.body.innerText : "").toLowerCase();
    const url  = window.location.href.toLowerCase();

    // 1. Check if redirected to sign-in (not logged in)
    if (
      url.includes("accounts.google.com/v3/signin") ||
      url.includes("accounts.google.com/signin") ||
      url.includes("accounts.google.com/servicelogin") ||
      text.includes("sign in with your google account") ||
      text.includes("đăng nhập vào tài khoản google") ||
      text.includes("choose an account") ||
      text.includes("chọn tài khoản")
    ) {
      return { status: "not_logged_in", details: "Profile not logged into Google" };
    }

    // 2. Check if expired / invalid link (Screen from user: "You need a new activation link")
    const expiredKw = [
      "you need a new activation link",
      "need a new activation link",
      "please ask your provider to send a new link",
      "ask your provider to send a new link",
      "explore google one",
      "khám phá google one",
      "cần một đường liên kết kích hoạt mới",
      "hãy yêu cầu nhà cung cấp",
      "link is no longer valid",
      "liên kết không còn hợp lệ",
      "link expired",
      "activation link has expired",
      "đường liên kết đã hết hạn",
      "liên kết hết hạn",
      "liên kết kích hoạt này đã hết hạn",
      "request a new link"
    ];
    for (const kw of expiredKw) {
      if (text.includes(kw)) {
        return { status: "expired", details: "Activation link expired: " + kw };
      }
    }

    // 3. Check if already used / redeemed
    const usedKw = [
      "subscription has been used",
      "already been used",
      "already redeemed",
      "gói thuê bao này đã được sử dụng",
      "đã được sử dụng",
      "offer is not available",
      "ưu đãi không có sẵn",
      "this offer has already been used",
      "you've already redeemed"
    ];
    for (const kw of usedKw) {
      if (text.includes(kw)) {
        return { status: "used", details: "Link already used/redeemed: " + kw };
      }
    }

    // 4. Check if current profile already has a subscription
    const ineligibleKw = [
      "already have a subscription",
      "already a google one member",
      "current plan",
      "gói hiện tại",
      "đã là thành viên",
      "you already have google one",
      "bạn đã có google one",
      "bạn đã đăng ký",
      "already subscribed"
    ];
    for (const kw of ineligibleKw) {
      if (text.includes(kw)) {
        return { status: "account_already_pro", details: "Current profile already subscribed: " + kw };
      }
    }

    // 5. Check if LIVE / FRESH LINK (Contains activation button or plan banner)
    const activateBtnKw = [
      "kích hoạt gói", "kích hoạt", "nhận ưu đãi", "đổi ưu đãi",
      "bắt đầu", "dùng thử", "sử dụng gói", "tiếp tục",
      "get started", "redeem", "activate", "claim", "subscribe",
      "start free", "try now"
    ];

    const isActivatePage = (
      url.includes("one.google.com/activate") ||
      url.includes("serviceactivation.google.com/subscription/new") ||
      url.includes("one.google.com/activate-plan")
    );

    if (isActivatePage) {
      const btns = Array.from(document.querySelectorAll("button, [role='button'], a, .VfPpkd-LgbsSe"));
      for (const btn of btns) {
        const btnText = (btn.innerText || btn.textContent || "").trim().toLowerCase();
        if (!btnText || btnText.length > 80) continue;
        for (const kw of activateBtnKw) {
          if (btnText.includes(kw)) {
            // DO NOT CLICK! Keep the link intact for the user!
            console.log("[EXT] LIVE link detected with button:", btnText);
            return { status: "live", details: "Live activation button: " + btnText };
          }
        }
      }

      // Check if plan text is present on the page
      if (
        (text.includes("gemini") || text.includes("ai premium") || text.includes("google one")) &&
        (text.includes("18") || text.includes("tháng") || text.includes("month") || text.includes("2 tb"))
      ) {
        return { status: "live", details: "Live plan text loaded" };
      }
    }

    return null;
  }

  let attempts = 0;
  const maxAttempts = 12; // Wait up to ~9.6 seconds for Google One SPA to render

  const interval = setInterval(() => {
    attempts++;
    const res = checkStatus();

    if (res) {
      clearInterval(interval);
      console.log("[EXT] Final Status:", res.status, res.details);
      chrome.runtime.sendMessage({
        action: "report_status",
        status: res.status,
        url: currentHref,
        details: res.details
      });
    } else if (attempts >= maxAttempts) {
      clearInterval(interval);
      console.log("[EXT] Timeout waiting for known page status");
      chrome.runtime.sendMessage({
        action: "report_status",
        status: "unknown",
        url: currentHref,
        details: "Timed out waiting for page status"
      });
    }
  }, 800);
})();
