const API_BASE_URL = "http://127.0.0.1:5000";

const form = document.querySelector("#spin-form");
const phoneInput = document.querySelector("#phone");
const spinButton = document.querySelector("#spin-button");
const spinNowButton = document.querySelector("#spin-now-button");
const changePhoneButton = document.querySelector("#change-phone-button");
const statusMessage = document.querySelector("#status");
const spinStep = document.querySelector("#spin-step");
const activePhone = document.querySelector("#active-phone");
const currentPhoneLabel = document.querySelector(".current-phone");
const wheel = document.querySelector("#wheel");
const bulbRing = document.querySelector("#bulb-ring");
const winCard = document.querySelector("#win-card");
const winPrize = document.querySelector("#win-prize");
const confetti = document.querySelector("#confetti");
const invalidPhoneMessage = "Vui lòng nhập đúng số điện thoại của bạn.";

const bulbCount = 32;
for (let index = 0; index < bulbCount; index += 1) {
  const angle = (index / bulbCount) * Math.PI * 2 - Math.PI / 2;
  const bulb = document.createElement("span");
  bulb.className = "bulb";
  bulb.style.left = `${50 + Math.cos(angle) * 50}%`;
  bulb.style.top = `${50 + Math.sin(angle) * 50}%`;
  bulb.style.setProperty("--delay", `${index * -0.025}s`);
  bulbRing.append(bulb);
}

const prizeAngles = {
  voucher: 45,
  "bim-bim": 135,
  "banh-tam-xoan": 225,
  "o-mai-man": 315,
};

const EXAMPLE_PHONE = "0912345678";
let totalRotation = 0;

function showInvalidPhone() {
  phoneInput.value = "";
  setStatus(invalidPhoneMessage, true);
}

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

phoneInput.addEventListener("beforeinput", (event) => {
  if (event.data && /[^0-9]/.test(event.data)) {
    event.preventDefault();
    showInvalidPhone();
  }
});

phoneInput.addEventListener("paste", (event) => {
  const pastedText = event.clipboardData?.getData("text") || "";
  if (/[^0-9]/.test(pastedText)) {
    event.preventDefault();
    showInvalidPhone();
  }
});

phoneInput.addEventListener("input", () => {
  if (/[^0-9]/.test(phoneInput.value)) {
    showInvalidPhone();
  } else if (phoneInput.value.length <= 10) {
    setStatus("");
  } else {
    phoneInput.value = phoneInput.value.slice(0, 10);
  }
});

function showWin(prizeName) {
  winPrize.textContent = prizeName;
  winCard.hidden = false;
  winCard.classList.remove("is-visible");
  void winCard.offsetWidth;
  winCard.classList.add("is-visible");
  winCard.scrollIntoView({
    behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    block: "center",
  });

  confetti.replaceChildren();
  const colors = ["#fff0a6", "#ffd34d", "#ff755e", "#fff9e5", "#73e0c0", "#ff9c39"];
  for (let index = 0; index < 34; index += 1) {
    const piece = document.createElement("span");
    piece.className = "confetti-piece";
    piece.style.setProperty("--confetti-color", colors[index % colors.length]);
    piece.style.setProperty("--confetti-x", `${Math.round(Math.random() * 300 - 150)}px`);
    piece.style.setProperty("--confetti-y", `${Math.round(Math.random() * 100 - 35)}px`);
    piece.style.setProperty("--confetti-rotate", `${Math.round(Math.random() * 900 - 450)}deg`);
    piece.style.setProperty("--confetti-delay", `${Math.random() * 0.2}s`);
    confetti.append(piece);
  }
}

function spinToPrize(prizeId) {
  const centerAngle = prizeAngles[prizeId];
  if (centerAngle === undefined) {
    throw new Error("Máy chủ trả về mã phần thưởng không hợp lệ.");
  }

  const matrix = new DOMMatrixReadOnly(getComputedStyle(wheel).transform);
  const currentAngle = (Math.atan2(matrix.b, matrix.a) * 180 / Math.PI + 360) % 360;
  wheel.style.transform = `rotate(${currentAngle}deg)`;
  wheel.classList.remove("is-idle");
  void wheel.offsetWidth;

  const desiredRotation = (360 - centerAngle) % 360;
  const alignment = (desiredRotation - currentAngle + 360) % 360;
  totalRotation = currentAngle + 6 * 360 + alignment;

  return new Promise((resolve) => {
    let fallbackTimer;
    const finish = () => {
      clearTimeout(fallbackTimer);
      wheel.removeEventListener("transitionend", onTransitionEnd);
      bulbRing.classList.remove("is-spinning");
      bulbRing.classList.add("is-winner");
      setTimeout(() => bulbRing.classList.remove("is-winner"), 1800);
      resolve();
    };
    const onTransitionEnd = (event) => {
      if (event.target === wheel && event.propertyName === "transform") finish();
    };

    bulbRing.classList.remove("is-winner");
    bulbRing.classList.remove("is-idle");
    bulbRing.classList.add("is-spinning");
    wheel.addEventListener("transitionend", onTransitionEnd);
    fallbackTimer = setTimeout(finish, 6500);
    wheel.style.transform = `rotate(${totalRotation}deg)`;
  });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  setStatus("");

  const phone = phoneInput.value.trim();
  if (!/^0[0-9]{9}$/.test(phone)) {
    setStatus(invalidPhoneMessage, true);
    phoneInput.focus();
    return;
  }
  const digits = phone.replace(/[\s().-]/g, "").replace(/^\+/, "");
  const normalizedPhone = digits.startsWith("84") && digits.length === 11
    ? `0${digits.slice(2)}`
    : digits;
  if (normalizedPhone === EXAMPLE_PHONE) {
    setStatus("Đây là số điện thoại ví dụ. Vui lòng nhập số điện thoại của bạn.", true);
    phoneInput.focus();
    return;
  }

  activePhone.textContent = phone;
  form.hidden = true;
  spinStep.hidden = false;
  wheel.classList.add("is-idle");
  bulbRing.classList.add("is-idle");
  spinNowButton.disabled = false;
  setStatus("");
});

changePhoneButton.addEventListener("click", () => {
  if (spinNowButton.disabled) return;
  spinStep.hidden = true;
  wheel.classList.remove("is-idle");
  bulbRing.classList.remove("is-idle");
  form.hidden = false;
  phoneInput.focus();
});

spinNowButton.addEventListener("click", async () => {
  const phone = phoneInput.value.trim();
  if (!/^0[0-9]{9}$/.test(phone)) {
    setStatus(invalidPhoneMessage, true);
    spinStep.hidden = true;
    form.hidden = false;
    phoneInput.focus();
    return;
  }
  if (!API_BASE_URL) {
    setStatus(
      "Website chưa được cấu hình địa chỉ máy chủ.",
      true,
    );
    spinStep.hidden = true;
    form.hidden = false;
    phoneInput.focus();
    return;
  }

  setStatus("Đang xác nhận lượt quay...");
  spinNowButton.disabled = true;
  changePhoneButton.disabled = true;
  currentPhoneLabel.classList.add("is-spinning");
  let response;
  try {
    response = await fetch(`${API_BASE_URL.replace(/\/+$/, "")}/api/spin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone }),
    });
  } catch {
    setStatus(
      "Không kết nối được máy chủ. Nếu lượt quay đã được ghi nhận, số này không thể quay lại; vui lòng nhờ nhân viên kiểm tra.",
      true,
    );
    spinNowButton.disabled = false;
    changePhoneButton.disabled = false;
    currentPhoneLabel.classList.remove("is-spinning");
    return;
  }

  let result;
  try {
    result = await response.json();
  } catch {
    setStatus("Máy chủ trả về dữ liệu không hợp lệ. Vui lòng nhờ nhân viên kiểm tra.", true);
    spinNowButton.disabled = false;
    changePhoneButton.disabled = false;
    currentPhoneLabel.classList.remove("is-spinning");
    return;
  }

  if (!response.ok) {
    setStatus(result.error || "Không thể thực hiện lượt quay.", true);
    spinNowButton.disabled = false;
    changePhoneButton.disabled = false;
    currentPhoneLabel.classList.remove("is-spinning");
    if (response.status === 409 || response.status === 400) {
      spinStep.hidden = true;
      form.hidden = false;
      phoneInput.focus();
    }
    return;
  }

  try {
    activePhone.textContent = result.phone || phone;
    setStatus("");
    await spinToPrize(result.prize?.id);
    showWin(result.prize.name);
    setStatus(`Chúc mừng bạn nhận được: ${result.prize.name}!`);
  } catch {
    setStatus(
      "Máy chủ đã xác nhận lượt quay nhưng không thể hiển thị kết quả. Hãy giữ nguyên số này và nhờ nhân viên kiểm tra.",
      true,
    );
  } finally {
    currentPhoneLabel.classList.remove("is-spinning");
    spinNowButton.disabled = true;
    changePhoneButton.disabled = false;
  }
});
