const statusClasses = {
  operational: "ok",
  maintenance: "warn",
  degraded: "warn",
  outage: "bad"
};

function formatKst(value) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Seoul"
  }).format(new Date(value));
}

function renderServices(services) {
  const grid = document.querySelector("#service-grid");
  grid.innerHTML = services.map((service) => `
    <article class="service-card">
      <div>
        <h3>${service.name}</h3>
        <p>${service.latencyMs}ms latency</p>
      </div>
      <span class="service-status ${statusClasses[service.status] ?? "warn"}">${service.status}</span>
    </article>
  `).join("");
}

async function main() {
  const response = await fetch("/api/status");
  const payload = await response.json();
  const overall = document.querySelector("#overall-status");

  overall.textContent = payload.summary.label;
  overall.className = `status-pill ${statusClasses[payload.summary.level] ?? "warn"}`;
  document.querySelector("#generated-at").textContent = `Last generated: ${formatKst(payload.generatedAt)}`;

  renderServices(payload.services);
}

main().catch((error) => {
  document.querySelector("#overall-status").textContent = "Status unavailable";
  console.error(error);
});
