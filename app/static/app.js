// Meshtastic MQTT Monitor - Frontend JavaScript

class MeshtasticMonitor {
  constructor() {
    this.map = null;
    this.markers = {};
    this.selectedNode = null;
    this.nodes = [];
    this.messages = [];
    this.init();
  }

  init() {
    // Initialize map
    this.initMap();

    // Set up event listeners
    this.setupEventListeners();

    // Load initial data
    this.loadStats();
    this.loadNodes();
    this.loadMessages();

    // Set up auto-refresh
    setInterval(() => this.autoRefresh(), 10000); // Refresh every 10 seconds
  }

  initMap() {
    // Initialize Leaflet map
    this.map = L.map("map").setView([0, 0], 2);

    // Add OpenStreetMap tiles
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(this.map);

    // Load location markers
    this.loadLocations();
  }

  setupEventListeners() {
    // Refresh button
    document.getElementById("refreshBtn").addEventListener("click", () => {
      this.loadMessages();
      this.loadNodes();
      this.loadStats();
      this.loadLocations();
    });

    // Node filter
    document
      .getElementById("nodeFilterSelect")
      .addEventListener("change", (e) => {
        this.selectedNode = e.target.value || null;
        this.loadMessages();
      });

    // Node search filter
    document.getElementById("nodeFilter").addEventListener("input", (e) => {
      this.filterNodes(e.target.value);
    });
  }

  async loadStats() {
    try {
      const response = await fetch("/api/stats");
      const data = await response.json();

      if (data.success) {
        document.getElementById("totalMessages").textContent =
          data.stats.total_messages;
        document.getElementById("totalNodes").textContent =
          data.stats.total_nodes;
        document.getElementById("messagesWithLocation").textContent =
          data.stats.messages_with_location;
      }
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  }

  async loadNodes() {
    try {
      const response = await fetch("/api/nodes");
      const data = await response.json();

      if (data.success) {
        this.nodes = data.nodes;
        this.displayNodes(this.nodes);
        this.updateNodeFilter(this.nodes);
      }
    } catch (error) {
      console.error("Error loading nodes:", error);
      this.showError("nodesList", "Failed to load nodes");
    }
  }

  displayNodes(nodes) {
    const nodesList = document.getElementById("nodesList");

    if (nodes.length === 0) {
      nodesList.innerHTML = '<p class="loading">No nodes found</p>';
      return;
    }

    nodesList.innerHTML = nodes
      .map((node) => {
        const lastSeen = new Date(node.last_seen).toLocaleString();
        return `
                <div class="node-item" data-node-id="${node.node_id}">
                  <div class="node-id">${this.nodeDisplayName(node.node_id, { long: true })}</div>
                    <div class="node-meta">
                        <span>${node.message_count || 0} msgs</span>
                        <span>${this.formatTime(node.last_seen)}</span>
                    </div>
                </div>
            `;
      })
      .join("");

    // Add click handlers to nodes
    nodesList.querySelectorAll(".node-item").forEach((item) => {
      item.addEventListener("click", () => {
        const nodeId = item.dataset.nodeId;
        this.selectNode(nodeId);
      });
    });
  }

  filterNodes(searchTerm) {
    const filtered = this.nodes.filter((node) =>
      node.node_id.toLowerCase().includes(searchTerm.toLowerCase()),
    );
    this.displayNodes(filtered);
  }

  selectNode(nodeId) {
    this.selectedNode = nodeId;

    // Update UI
    document.querySelectorAll(".node-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.nodeId === nodeId);
    });

    // Update filter dropdown
    document.getElementById("nodeFilterSelect").value = nodeId;

    // Load messages for this node
    this.loadMessages();

    // Zoom to node on map if it has location
    const node = this.nodes.find((n) => n.node_id === nodeId);
    if (node && node.last_latitude && node.last_longitude) {
      this.map.setView([node.last_latitude, node.last_longitude], 13);
    }
  }

  updateNodeFilter(nodes) {
    const select = document.getElementById("nodeFilterSelect");
    const currentValue = select.value;

    select.innerHTML =
      '<option value="">All Nodes</option>' +
      nodes
        .map(
          (node) =>
            `<option value="${node.node_id}">${this.nodeDisplayName(node.node_id)}</option>`,
        )
        .join("");

    if (currentValue) {
      select.value = currentValue;
    }
  }

  async loadMessages() {
    try {
      let url = "/api/messages?limit=100";
      if (this.selectedNode) {
        url += `&node_id=${this.selectedNode}`;
      }

      const response = await fetch(url);
      const data = await response.json();

      if (data.success) {
        this.messages = data.messages;
        this.displayMessages(this.messages);
      }
    } catch (error) {
      console.error("Error loading messages:", error);
      this.showError("messagesList", "Failed to load messages");
    }
  }

  displayMessages(messages) {
    const messagesList = document.getElementById("messagesList");

    if (messages.length === 0) {
      messagesList.innerHTML = '<p class="loading">No messages found</p>';
      return;
    }

    messagesList.innerHTML = messages
      .map((msg) => {
        const hasLocation = msg.latitude && msg.longitude;
        const locationClass = hasLocation ? "has-location" : "";

        return `
                <div class="message-item ${locationClass}">
                    <div class="message-header">
                        <span class="message-from">${this.nodeDisplayName(msg.from_node)}</span>
                        <span class="message-time">${this.formatTime(msg.received_at)}</span>
                    </div>
                    ${msg.packet_type ? `<div class="message-type">${msg.packet_type}</div>` : ""}
                    ${msg.payload ? `<div class="message-payload">${this.escapeHtml(msg.payload)}</div>` : ""}
                    <div class="message-meta">
                        ${msg.to_node ? `<span>To: ${this.nodeDisplayName(msg.to_node)}</span>` : ""}
                        ${msg.snr ? `<span>SNR: ${msg.snr}</span>` : ""}
                        ${msg.rssi ? `<span>RSSI: ${msg.rssi}</span>` : ""}
                        ${hasLocation ? `<span>📍 ${msg.latitude.toFixed(5)}, ${msg.longitude.toFixed(5)}</span>` : ""}
                    </div>
                </div>
            `;
      })
      .join("");
  }

  async loadLocations() {
    try {
      const response = await fetch("/api/messages/locations");
      const data = await response.json();

      if (data.success) {
        this.updateMapMarkers(data.messages);
      }
    } catch (error) {
      console.error("Error loading locations:", error);
    }
  }

  updateMapMarkers(messages) {
    // Clear existing markers
    Object.values(this.markers).forEach((marker) => marker.remove());
    this.markers = {};

    if (messages.length === 0) return;

    const bounds = [];

    messages.forEach((msg) => {
      if (msg.latitude && msg.longitude) {
        const latLng = [msg.latitude, msg.longitude];
        bounds.push(latLng);

        // Create marker
        const marker = L.marker(latLng).addTo(this.map);

        // Create popup content
        const popupContent = `
                    <strong>${this.nodeDisplayName(msg.from_node)}</strong><br>
                    ${msg.packet_type || "Unknown"}<br>
                    ${msg.payload ? msg.payload.substring(0, 100) : ""}<br>
                    <small>${this.formatTime(msg.received_at)}</small>
                `;

        marker.bindPopup(popupContent);

        // Store marker
        this.markers[msg.id] = marker;
      }
    });

    // Fit map to show all markers
    if (bounds.length > 0) {
      this.map.fitBounds(bounds, { padding: [50, 50] });
    }
  }

  formatTime(timestamp) {
    if (!timestamp) return "N/A";

    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // seconds

    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;

    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="error">${message}</div>`;
  }

  nodeDisplayName(node_id, opts = { long: false }) {
    const node = this.nodes.find((n) => n.node_id === node_id);
    if (!node) return node_id;

    if (node.short_name) {
      return opts.long
        ? `${node.long_name} (${node.short_name})`
        : node.short_name;
    }

    return node_id;
  }

  autoRefresh() {
    // Auto-refresh data
    this.loadStats();
    this.loadNodes();
    this.loadMessages();
    this.loadLocations();
  }
}

// Initialize the application when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  new MeshtasticMonitor();
});
