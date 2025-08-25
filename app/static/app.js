function preventImplicitSubmit() {
  // If a submit event somehow fires, block it
  document.addEventListener("submit", (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
  // Pressing Enter in inputs should trigger analyze without reloading
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      document.getElementById("runBtn").click();
    }
  });
}

async function analyze() {
  const dep = document.getElementById("departure").value.trim();
  const arr = document.getElementById("arrival").value.trim();

  const alertEl = document.getElementById("alert");
  const plotWrap = document.getElementById("plotWrap");
  const plotEl = document.getElementById("plot");
  const tableWrap = document.getElementById("tableWrap");
  const tbody = document.querySelector("#results tbody");

  // reset UI
  alertEl.style.display = "none";
  plotWrap.style.display = "none";
  tableWrap.style.display = "none";
  tbody.innerHTML = "";

  const btn = document.getElementById("runBtn");
  btn.disabled = true;
  btn.textContent = "Analyzing…";

  // ---- NEW: hard timeout so UI never hangs indefinitely ----
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s cap

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ departure: dep, arrival: arr }),
      signal: controller.signal
    });

    // Read as text first; then parse JSON so we can surface HTML/text errors too
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch { throw new Error(text.slice(0, 400) || "Non-JSON response from server"); }

    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    // Success UI
    alertEl.textContent = data.alert || "Done";
    alertEl.style.display = "block";

    plotEl.src = data.plot;
    plotWrap.style.display = "block";

    (data.rows || []).forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>${r.nearest_city ?? ""}</td>
        <td class="${r.safety === "Safe to continue" ? "ok" : (r.safety === "Unsafe to continue" ? "bad" : "")}">
          ${r.safety}
        </td>
        <td>${r.temp_c ?? ""}</td>
        <td>${r.wind_ms ?? ""}</td>
        <td>${r.condition ?? ""}</td>
      `;
      tbody.appendChild(tr);
    });
    tableWrap.style.display = "block";
  } catch (e) {
    alertEl.textContent =
      e && e.name === "AbortError"
        ? "Request took too long. Please try again."
        : (e && e.message) ? e.message : String(e);
    alertEl.style.display = "block";
    console.error("Analyze error:", e);
  } finally {
    clearTimeout(timeoutId);
    btn.disabled = false;
    btn.textContent = "Analyze Route";
  }
}

preventImplicitSubmit();
document.getElementById("runBtn").addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  analyze();
});
