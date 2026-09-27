const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/research";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Opens a WebSocket, sends the goal, and forwards every event the backend
// streams back (plan, step_start, thought, tool_call, observation,
// step_complete, synthesizing, done, error) to onEvent.
export function connectResearchSocket(goal, onEvent) {
  const socket = new WebSocket(WS_URL);
  socket.onopen = () => socket.send(JSON.stringify({ goal }));
  socket.onmessage = (msg) => onEvent(JSON.parse(msg.data));
  socket.onerror = () => onEvent({ type: "error", data: { message: "WebSocket error" } });
  return socket;
}

export async function fetchReports() {
  const res = await fetch(`${API_URL}/api/reports`);
  return res.json();
}
