import Dashboard from "./pages/Dashboard.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>AI Research Agent</h1>
        <p>Plan → Act → Observe → Respond</p>
      </header>
      <Dashboard />
    </div>
  );
}
