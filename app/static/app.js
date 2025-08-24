async function analyze() {
  const dep = document.getElementById("departure").value.trim();
  const arr = document.getElementById("arrival").value.trim();
  const alertEl = document.getElementById("alert");
  const plotWrap = document.getElementById("plotWrap");
  const plotEl = document.getElementById("plot");
  const tableWrap = document.getElementById("tableWrap");
  const tbody = document.querySelector("#results tbody");
  alertEl.style.display = "none"; plotWrap.style.display = "none"; tableWrap.style.display = "none"; tbody.innerHTML = "";
  const btn = document.getElementById("runBtn"); btn.disabled = true; btn.textContent = "Analyzing";
  try {
    const res = await fetch("/api/analyze", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ departure: dep, arrival: arr })});
    const data = await res.json(); if (!res.ok) throw new Error(data.error || "Request failed");
    alertEl.textContent = data.alert; alertEl.style.display = "block";
    plotEl.src = data.plot; plotWrap.style.display = "block";
    data.rows.forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${idx+1}</td><td>${r.nearest_city ?? ""}</td>
        <td class="${r.safety === "Safe to continue" ? "ok" : (r.safety === "Unsafe to continue" ? "bad" : "")}">${r.safety}</td>
        <td>${r.temp_c ?? ""}</td><td>${r.wind_ms ?? ""}</td><td>${r.condition ?? ""}</td>`;
      tbody.appendChild(tr);
    }); tableWrap.style.display = "block";
  } catch (e) { alertEl.textContent = e.message; alertEl.style.display = "block"; }
  finally { btn.disabled = false; btn.textContent = "Analyze Route"; }
}
document.getElementById("runBtn").addEventListener("click", analyze);
