import { useRef, useState } from "react";
import TaskInput from "../components/TaskInput.jsx";
import AgentPlan from "../components/AgentPlan.jsx";
import AgentSteps from "../components/AgentSteps.jsx";
import ToolExecution from "../components/ToolExecution.jsx";
import Sources from "../components/Sources.jsx";
import ReportViewer from "../components/ReportViewer.jsx";
import { connectResearchSocket } from "../services/api.js";

export default function Dashboard() {
  const [plan, setPlan] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [logs, setLogs] = useState([]);
  const [observations, setObservations] = useState([]);
  const [report, setReport] = useState("");
  const [reportPath, setReportPath] = useState("");
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const socketRef = useRef(null);

  const reset = () => {
    setPlan([]);
    setCurrentStep(0);
    setCompletedSteps([]);
    setLogs([]);
    setObservations([]);
    setReport("");
    setReportPath("");
    setError("");
  };

  const handleStart = (goal) => {
    reset();
    setRunning(true);

    socketRef.current = connectResearchSocket(goal, (event) => {
      switch (event.type) {
        case "plan":
          setPlan(event.data);
          break;
        case "step_start":
          setCurrentStep(event.data.step);
          break;
        case "thought":
        case "tool_call":
          setLogs((prev) => [...prev, event]);
          break;
        case "observation":
          setLogs((prev) => [...prev, event]);
          setObservations((prev) => [...prev, event.data]);
          break;
        case "step_complete":
          setCompletedSteps((prev) => [...prev, event.data.step]);
          break;
        case "done":
          setReport(event.data.report);
          setReportPath(event.data.path);
          setRunning(false);
          break;
        case "error":
          setError(event.data?.message || "Something went wrong while running the agent.");
          setRunning(false);
          break;
        default:
          break;
      }
    });
  };

  return (
    <main className="dashboard">
      <TaskInput onStart={handleStart} disabled={running} />
      {error && (
        <section className="panel error-panel">
          <h2>Error</h2>
          <p>{error}</p>
        </section>
      )}
      <AgentPlan plan={plan} />
      <AgentSteps plan={plan} currentStep={currentStep} completedSteps={completedSteps} />
      <ToolExecution logs={logs} />
      <Sources observations={observations} />
      <ReportViewer report={report} path={reportPath} />
    </main>
  );
}
