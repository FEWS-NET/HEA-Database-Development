(function () {
  const qs = new URLSearchParams(window.location.search);
  const workbookPath = window.__INITIAL_WORKBOOK_PATH__ || qs.get("path") || "";
  const sheetSelect = document.getElementById("sheet-dd");
  const cellInput = document.getElementById("cell-input");
  const genBtn = document.getElementById("gen-btn");
  const statusText = document.getElementById("status-text");
  const formulaPanel = document.getElementById("formula-panel");
  const wbPathEl = document.getElementById("wb-path");

  let cy = null;
  let formulasMap = {}; // nodeId -> meta

  function setStatus(msg) {
    statusText.textContent = msg || "";
  }

  function a1Valid(s) {
    return /^\$?[A-Z]{1,3}\$?\d{1,7}$/.test((s || "").trim().toUpperCase());
  }

  async function fetchJSON(url, opts) {
    const res = await fetch(url, opts);
    if (!res.ok) {
      let text = await res.text().catch(() => "");
      try { const j = JSON.parse(text); text = j.error || text; } catch {}
      throw new Error(text || (res.status + " " + res.statusText));
    }
    return res.json();
  }

  async function loadSheets() {
    if (!workbookPath) {
      setStatus("No workbook path provided. Go back and enter a path.");
      return;
    }
    wbPathEl.textContent = workbookPath;
    setStatus("Loading sheets...");
    const data = await fetchJSON(`/api/sheets?path=${encodeURIComponent(workbookPath)}`);
    sheetSelect.innerHTML = "";
    data.sheets.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s; opt.textContent = s;
      sheetSelect.appendChild(opt);
    });
    setStatus(`Loaded ${data.sheets.length} sheet(s).`);
  }

  function cytoscapeStyle() {
    return [
      // generic nodes (labels inside)
      { selector: "node", style: {
          "label": "data(label)",
          "color": "#111",
          "font-size": "14px",
          "font-weight": "600",
          "text-wrap": "wrap",
          "text-max-width": "200px",
          "text-valign": "center",
          "text-halign": "center",
          "background-color": "#8da0cb",
          "border-color": "#1f1f1f",
          "border-width": 1.2,
          "shape": "round-rectangle",
          "padding": "10px",
          "opacity": 0.55,
          "width": "label",
          "height": "label"
      }},
      { selector: "node.formula", style: { "shape": "round-rectangle" } },
      { selector: "node.value",   style: { "shape": "ellipse" } },
      { selector: "node.range",   style: { "border-width": 2 } },
      //{ selector: "node.pairwise",style: { "shape": "hexagon", "border-width": 2.6, "background-color": "#c3d6ff" } },

      // edges
      { selector: "edge", style: {
          "curve-style": "bezier",
          "edge-distances": "node-position",
          "control-point-step-size": 40,
          "target-arrow-shape": "triangle",
          "line-color": "#555",
          "target-arrow-color": "#555",
          "width": 1.8,
          "opacity": 0.6
      }},
      { selector: "edge.range-edge",      style: { "line-style": "dashed" } },
      { selector: "edge.rep-bridge",      style: { "line-style": "dotted" } },
      //{ selector: "edge.collapsed-fanin", style: { "line-style": "dashdot", "width": 2.2 } },

      // sheet containers (AFTER generic node so alignment wins)
      { selector: "node.sheet-group", style: {
          "shape": "round-rectangle",
          "background-color": "#eef3ff",
          "background-opacity": 0.35,
          "border-width": 2,
          "border-color": "#7aa2ff",
          "label": "data(label)",
          "color": "#111",
          "font-size": "18px",
          "font-weight": "700",
          "text-valign": "top",
          "text-halign": "center",
          "text-margin-y": "-12px",
          "padding": "22px",
      }},

      // highlight classes
      { selector: ".selected-node", style: {
          "background-color": "#ffcc00", "border-color": "#b58900", "border-width": 3, "opacity": 1.0 }},
      { selector: ".neighbor-node", style: {
          "background-color": "#66c2a5", "border-color": "#2e8b57", "border-width": 2, "opacity": 0.95 }},
      { selector: ".selected-edge", style: {
          "line-color": "#d95f02", "target-arrow-color": "#d95f02", "width": 3.2, "opacity": 1.0 }},
    ];
  }

  function clearHighlight() {
    if (!cy) return;
    cy.elements().removeClass("selected-node neighbor-node selected-edge");
  }

  function bindNodeClicks(startNode, predsIndex, succsIndex, edgeIds) {
    if (!cy) return;
    cy.off("tap", "node"); // avoid duplicate binding
    cy.on("tap", "node", (evt) => {
      clearHighlight();
      const n = evt.target;
      n.addClass("selected-node");

      // neighbors (immediate preds + succs)
      const nodeId = n.data("id");

      const preds = predsIndex[nodeId] || [];
      const succs = succsIndex[nodeId] || [];

      preds.forEach(p => cy.getElementById(p).addClass("neighbor-node"));
      succs.forEach(s => cy.getElementById(s).addClass("neighbor-node"));

      // incident edges
      preds.forEach(p => {
        const eid = edgeIds[`${p}||${nodeId}`];
        if (eid) cy.getElementById(eid).addClass("selected-edge");
      });
      succs.forEach(s => {
        const eid = edgeIds[`${nodeId}||${s}`];
        if (eid) cy.getElementById(eid).addClass("selected-edge");
      });

      // formula panel
      const meta = formulasMap[nodeId];
      formulaPanel.textContent = formatFormulaPanel(nodeId, meta);
    });
  }

  function formatFormulaPanel(nodeId, meta) {
    if (!meta) return `${nodeId}\nFormula: (unknown)`;
    if (meta.type === "cell") {
      const f = meta.formula || "(none)";
      return `${nodeId}\nFormula: ${f}`;
    }
    if (meta.type === "range") {
      const rep = meta.rep || "—";
      const f = meta.formula || "(none)";
      return `${nodeId}  (range)\nRepresentative: ${rep}\nFormula: ${f}`;
    }
    return `${nodeId}\n(unknown type)`;
  }

  async function generateGraph() {
    const sheet = sheetSelect.value;
    const cell = (cellInput.value || "").trim().toUpperCase();
    if (!workbookPath) { setStatus("No workbook path."); return; }
    if (!sheet) { setStatus("Pick a sheet."); return; }
    if (!a1Valid(cell)) { setStatus(`Invalid cell: ${cell}`); return; }

    setStatus("Generating graph...");
    formulaPanel.textContent = "Click a node to see its formula here.";
    clearHighlight();

    const body = { path: workbookPath, sheet, cell };
    let data;
    try {
      data = await fetchJSON("/api/graph", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
    } catch (err) {
      setStatus(`Error: ${err.message}`);
      return;
    }

    formulasMap = data.formulas || {};
    setStatus(`Showing ${data.meta.start_node} (nodes: ${data.meta.counts.nodes}, edges: ${data.meta.counts.edges})`);

    if (!cy) {
      cy = cytoscape({
        container: document.getElementById("cy"),
        elements: data.elements,
        layout: data.layout || { name: "preset", fit: true, padding: 30 },
        style: cytoscapeStyle(),
        wheelSensitivity: 0.2
      });
    } else {
      cy.json({ elements: data.elements });
      cy.layout(data.layout || { name: "preset", fit: true, padding: 30 }).run();
    }

    // Build adjacency indexes for quick highlighting
    const predsIndex = {};  // nodeId -> [preds...]
    const succsIndex = {};  // nodeId -> [succs...]
    const edgeIds = {};     // "u||v" -> edge id

    cy.edges().forEach(e => {
      const u = e.data("source");
      const v = e.data("target");
      (succsIndex[u] = succsIndex[u] || []).push(v);
      (predsIndex[v] = predsIndex[v] || []).push(u);
      edgeIds[`${u}||${v}`] = e.id();
    });

    bindNodeClicks(data.meta.start_node, predsIndex, succsIndex, edgeIds);
  }

  // Init
  window.addEventListener("DOMContentLoaded", async () => {
    await loadSheets();
    genBtn.addEventListener("click", generateGraph);
  });
})();
