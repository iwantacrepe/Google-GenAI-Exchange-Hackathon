// ----------------------------------------------
// 🧭 SIDEBAR NAVIGATION
// ----------------------------------------------
document.querySelectorAll(".sidebar li").forEach((item) => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".sidebar li").forEach((i) => i.classList.remove("active"));
    item.classList.add("active");

    const target = item.getAttribute("data-panel");
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    document.getElementById(target).classList.add("active");
  });
});

// ----------------------------------------------
// 🧩 1️⃣ MARKDOWN RENDERING HELPERS
// ----------------------------------------------
// ---------- Markdown helpers ----------
function mdToHtml(raw = "") {
  try {
    const html = window.marked ? marked.parse(raw) : raw;
    return window.DOMPurify ? DOMPurify.sanitize(html) : html;
  } catch {
    return raw;
  }
}

function hydrateSummaryFromDataAttr() {
  const box = document.getElementById("summary-content");
  if (!box) return;
  const raw = box.getAttribute("data-md");       // JSON-encoded string
  if (!raw || raw === "null") {
    box.innerHTML = "<p>Upload a file to begin analysis.</p>";
    return;
  }
  // raw is JSON string; parse then render
  const md = JSON.parse(raw);
  box.innerHTML = mdToHtml(md);
  box.scrollTop = 0;
}

document.addEventListener("DOMContentLoaded", () => {
  hydrateSummaryFromDataAttr();
});


// ----------------------------------------------
// 💭 2️⃣ THINKER CHAT SECTION
// ----------------------------------------------
const chatBox = document.getElementById("chat-box");
const sendBtn = document.getElementById("sendBtn");
const inputEl = document.getElementById("user-input");
let history = [];

function appendMessage(role, html) {
  const msg = document.createElement("div");
  msg.className = "message fade-in " + (role === "user" ? "user" : "bot");
  msg.innerHTML = html;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// typing indicator animation
function appendThinking() {
  const wrap = document.createElement("div");
  wrap.className = "message bot typing";
  wrap.innerHTML = `
    <div class="thinking-container">
      <div class="thinking-bubble"></div>
      <div class="thinking-bubble"></div>
      <div class="thinking-bubble"></div>
    </div>
    <p class="thinking-label">Nyay-Sahayak is reasoning...</p>
  `;
  chatBox.appendChild(wrap);
  chatBox.scrollTop = chatBox.scrollHeight;
  return wrap;
}

async function sendMessage() {
  const text = inputEl?.value.trim();
  if (!text) return;

  appendMessage("user", mdToHtml(text));
  inputEl.value = "";
  sendBtn.disabled = true;

  const thinkingNode = appendThinking();

  try {
    const res = await fetch("/api/thinker_chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history: [...history, { role: "user", content: text }] }),
    });

    const data = await res.json();
    const reply = data.reply || "⚠️ No response.";
    thinkingNode.remove();

    appendMessage("bot", mdToHtml(reply));

    history.push({ role: "user", content: text });
    history.push({ role: "assistant", content: reply });
  } catch (err) {
    thinkingNode.remove();
    appendMessage("bot", "⚠️ Error contacting server.");
  } finally {
    sendBtn.disabled = false;
  }
}

if (sendBtn) {
  sendBtn.addEventListener("click", sendMessage);
  inputEl?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

// ----------------------------------------------
// 🎯 AUTO GRAPH GENERATION ON DASHBOARD LOAD
// ----------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  const graphContainer = document.getElementById("graphContainer");
  if (!graphContainer) return;

  graphContainer.innerHTML = `
    <p style="color:#bbb;font-style:italic;">🧩 Building relationship graph...</p>
  `;

  try {
    const res = await fetch("/api/graph", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const data = await res.json();

    let graphData = { nodes: [], edges: [] };
    try {
      graphData = JSON.parse(data.output);
    } catch {
      graphContainer.innerHTML = "<p>⚠️ Could not parse graph data.</p>";
      return;
    }

    // 🧹 Filter out clutter — ignore IPC, CrPC, Article refs, etc.
    graphData.nodes = graphData.nodes.filter(n =>
      !/(IPC|Cr\.?P\.?C|Section|Article|Act|Constitution)/i.test(n.name)
    );
    graphData.edges = graphData.edges.filter(
      e => graphData.nodes.find(n => n.id === e.source) &&
           graphData.nodes.find(n => n.id === e.target)
    );

    renderGraph(graphData);
  } catch (err) {
    graphContainer.innerHTML = "<p>⚠️ Failed to build graph automatically.</p>";
  }
});


// ----------------------------------------------
// 🌌 INTERACTIVE D3 FORCE GRAPH (Zoom + Pan + Physics)
// ----------------------------------------------
function renderGraph(graphData) {
  const container = document.getElementById("graphContainer");
  container.innerHTML = "";

  const width = container.offsetWidth;
  const height = 600;

  const svg = d3.select(container)
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .style("background", "radial-gradient(circle at center, #111 0%, #0b1220 100%)")
    .style("border-radius", "14px")
    .style("cursor", "grab");

  // ⚙️ Enable zoom + pan
  const zoomLayer = svg.append("g");
  const zoom = d3.zoom()
    .scaleExtent([0.3, 4])
    .on("zoom", (event) => zoomLayer.attr("transform", event.transform));
  svg.call(zoom);

  const color = d3.scaleOrdinal()
    .domain(["Judge", "Lawyer", "Person", "Case", "Court", "Police", "Event"])
    .range(["#7dd3fc", "#a3e635", "#f87171", "#c084fc", "#60a5fa", "#fbbf24", "#facc15"]);

  const simulation = d3.forceSimulation(graphData.nodes)
    .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(180))
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(45));

  const link = zoomLayer.selectAll("line")
    .data(graphData.edges)
    .enter()
    .append("line")
    .attr("stroke", "#4b5563")
    .attr("stroke-width", 1.5)
    .attr("opacity", 0.6);

  const node = zoomLayer.selectAll("circle")
    .data(graphData.nodes)
    .enter()
    .append("circle")
    .attr("r", 14)
    .attr("fill", d => color(d.label))
    .style("stroke", "#fff")
    .style("stroke-width", 1.2)
    .on("mouseover", function (event, d) {
      d3.select(this).transition().attr("r", 18);
      tooltip.style("opacity", 1)
        .html(`<b>${d.name}</b><br><i>${d.label}</i>`)
        .style("left", `${event.pageX + 10}px`)
        .style("top", `${event.pageY - 10}px`);
    })
    .on("mouseout", function () {
      d3.select(this).transition().attr("r", 14);
      tooltip.style("opacity", 0);
    })
    .call(
      d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
    );

  const labels = zoomLayer.selectAll("text")
    .data(graphData.nodes)
    .enter()
    .append("text")
    .text(d => d.name)
    .attr("font-size", "12px")
    .attr("fill", "#e5e7eb")
    .attr("dx", 18)
    .attr("dy", 5);

  const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip")
    .style("position", "absolute")
    .style("padding", "6px 10px")
    .style("background", "#1e293b")
    .style("color", "#fff")
    .style("border-radius", "6px")
    .style("font-size", "13px")
    .style("opacity", 0);

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);
    node.attr("cx", d => d.x).attr("cy", d => d.y);
    labels.attr("x", d => d.x).attr("y", d => d.y);
  });

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
  }
  function dragged(event, d) {
    d.fx = event.x; d.fy = event.y;
  }
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
  }
}
