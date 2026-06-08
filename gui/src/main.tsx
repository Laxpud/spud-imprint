import React, { useMemo, useState } from "react";
import ReactDOM, { type Root } from "react-dom/client";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import {
  CheckCircle2,
  FileCog,
  FolderOpen,
  FolderInput,
  FolderOutput,
  Loader2,
  Play,
  TerminalSquare,
} from "lucide-react";
import "./styles.css";

declare global {
  interface Window {
    __SPUD_IMPRINT_ROOT__?: Root;
    __TAURI_INTERNALS__?: unknown;
  }
}

type BatchRequest = {
  inputDir: string;
  outputDir: string;
  configFile: string;
};

type BatchRunResult = {
  command: string[];
  statusCode: number | null;
  stdout: string;
  stderr: string;
};

type FieldKey = keyof BatchRequest;

const initialRequest: BatchRequest = {
  inputDir: "",
  outputDir: "",
  configFile: "",
};

function normalizeDialogPath(value: string | string[] | null): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function App() {
  const isDesktopRuntime = isTauriRuntime();
  const [request, setRequest] = useState<BatchRequest>(initialRequest);
  const [isRunning, setIsRunning] = useState(false);
  const [logText, setLogText] = useState("Ready.");
  const [lastStatus, setLastStatus] = useState<number | null>(null);

  const canRun = useMemo(
    () => Boolean(request.inputDir && request.outputDir && request.configFile),
    [request],
  );

  const updateField = (key: FieldKey, value: string) => {
    setRequest((current) => ({ ...current, [key]: value }));
  };

  const chooseDirectory = async (key: "inputDir" | "outputDir") => {
    if (!isDesktopRuntime) {
      showBrowserPreviewMessage(setLogText);
      return;
    }

    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: key === "inputDir" ? "Select input directory" : "Select output directory",
      });
      const path = normalizeDialogPath(selected);
      if (path) {
        updateField(key, path);
      }
    } catch (error) {
      setLogText(formatUiError(error));
    }
  };

  const chooseConfig = async () => {
    if (!isDesktopRuntime) {
      showBrowserPreviewMessage(setLogText);
      return;
    }

    try {
      const selected = await open({
        multiple: false,
        title: "Select config file",
        filters: [{ name: "TOML config", extensions: ["toml"] }],
      });
      const path = normalizeDialogPath(selected);
      if (path) {
        updateField("configFile", path);
      }
    } catch (error) {
      setLogText(formatUiError(error));
    }
  };

  const runBatch = async () => {
    if (!isDesktopRuntime) {
      showBrowserPreviewMessage(setLogText);
      setLastStatus(1);
      return;
    }

    if (!canRun || isRunning) {
      return;
    }

    setIsRunning(true);
    setLastStatus(null);
    setLogText("Starting batch run...");

    try {
      const result = await invoke<BatchRunResult>("run_batch", { request });
      setLastStatus(result.statusCode);
      setLogText(formatRunLog(result));
    } catch (error) {
      setLastStatus(1);
      setLogText(error instanceof Error ? error.message : String(error));
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="control-panel" aria-label="Batch controls">
          <div className="brand-row">
            <div className="brand-mark">SI</div>
            <div>
              <h1>Spud Imprint</h1>
              <p>Batch desktop prototype</p>
            </div>
          </div>

          <PathField
            icon={<FolderInput size={18} />}
            label="Input directory"
            value={request.inputDir}
            onChange={(value) => updateField("inputDir", value)}
            onBrowse={() => chooseDirectory("inputDir")}
          />
          <PathField
            icon={<FolderOutput size={18} />}
            label="Output directory"
            value={request.outputDir}
            onChange={(value) => updateField("outputDir", value)}
            onBrowse={() => chooseDirectory("outputDir")}
          />
          <PathField
            icon={<FileCog size={18} />}
            label="Config file"
            value={request.configFile}
            onChange={(value) => updateField("configFile", value)}
            onBrowse={chooseConfig}
          />

          <button
            className="run-button"
            type="button"
            disabled={!canRun || isRunning}
            onClick={runBatch}
          >
            {isRunning ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            <span>{isRunning ? "Running" : "Run batch"}</span>
          </button>
        </aside>

        <section className="log-panel" aria-label="Processing log">
          <div className="log-header">
            <div className="log-title">
              <TerminalSquare size={18} />
              <span>Processing log</span>
            </div>
            <StatusPill status={lastStatus} running={isRunning} />
          </div>
          <pre>{logText}</pre>
        </section>
      </section>
    </main>
  );
}

function isTauriRuntime(): boolean {
  return typeof window.__TAURI_INTERNALS__ !== "undefined";
}

function showBrowserPreviewMessage(setLogText: (value: string) => void) {
  setLogText(
    [
      "This page is running in browser preview mode.",
      "",
      "Native folder and file pickers are only available inside the Tauri desktop window.",
      "",
      "Start it with:",
      "  cd gui",
      "  npm run tauri dev",
      "",
      "You can still paste absolute paths into the fields while previewing the layout in a browser.",
    ].join("\n"),
  );
}

function formatUiError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function PathField(props: {
  icon: React.ReactNode;
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBrowse: () => void;
}) {
  return (
    <label className="path-field">
      <span className="field-label">
        {props.icon}
        {props.label}
      </span>
      <span className="path-input-row">
        <input
          value={props.value}
          onChange={(event) => props.onChange(event.target.value)}
          placeholder="Choose or paste a path"
        />
        <button type="button" title={`Browse ${props.label}`} onClick={props.onBrowse}>
          <FolderOpen size={17} />
        </button>
      </span>
    </label>
  );
}

function StatusPill(props: { status: number | null; running: boolean }) {
  if (props.running) {
    return <span className="status-pill running">Running</span>;
  }
  if (props.status === null) {
    return <span className="status-pill idle">Idle</span>;
  }
  if (props.status === 0) {
    return (
      <span className="status-pill success">
        <CheckCircle2 size={14} />
        Done
      </span>
    );
  }
  return <span className="status-pill failed">Failed</span>;
}

function formatRunLog(result: BatchRunResult): string {
  const sections = [
    `$ ${result.command.join(" ")}`,
    `Exit code: ${result.statusCode ?? "unknown"}`,
  ];

  if (result.stdout.trim()) {
    sections.push(`\n[stdout]\n${result.stdout.trimEnd()}`);
  }
  if (result.stderr.trim()) {
    sections.push(`\n[stderr]\n${result.stderr.trimEnd()}`);
  }

  return sections.join("\n");
}

const rootElement = document.getElementById("root") as HTMLElement;
const root = window.__SPUD_IMPRINT_ROOT__ ?? ReactDOM.createRoot(rootElement);
window.__SPUD_IMPRINT_ROOT__ = root;

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
