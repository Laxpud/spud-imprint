use serde::{Deserialize, Serialize};
use std::{
    env,
    path::{Path, PathBuf},
    process::Command,
};

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct BatchRequest {
    input_dir: String,
    output_dir: String,
    config_file: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct BatchRunResult {
    command: Vec<String>,
    status_code: Option<i32>,
    stdout: String,
    stderr: String,
}

enum CliCommand {
    Executable(PathBuf),
    PythonModule(PathBuf),
}

#[tauri::command]
fn run_batch(request: BatchRequest) -> Result<BatchRunResult, String> {
    validate_request(&request)?;

    let repo_root = repo_root()?;
    let cli = resolve_cli(&repo_root);
    let (program, args, display_command) = build_command(&cli, &request);

    let output = Command::new(&program)
        .args(&args)
        .current_dir(&repo_root)
        .env("PYTHONPATH", repo_root.join("src"))
        .output()
        .map_err(|error| format!("Failed to start CLI: {error}"))?;

    Ok(BatchRunResult {
        command: display_command,
        status_code: output.status.code(),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
    })
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![run_batch])
        .run(tauri::generate_context!())
        .expect("failed to run Spud Imprint GUI");
}

fn validate_request(request: &BatchRequest) -> Result<(), String> {
    let input_dir = Path::new(&request.input_dir);
    let output_dir = Path::new(&request.output_dir);
    let config_file = Path::new(&request.config_file);

    if !input_dir.is_dir() {
        return Err("Input directory does not exist.".to_string());
    }
    if !output_dir.is_dir() {
        return Err("Output directory does not exist.".to_string());
    }
    if !config_file.is_file() {
        return Err("Config file does not exist.".to_string());
    }

    Ok(())
}

fn repo_root() -> Result<PathBuf, String> {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest_dir
        .parent()
        .and_then(Path::parent)
        .map(Path::to_path_buf)
        .ok_or_else(|| "Failed to locate repository root.".to_string())
}

fn resolve_cli(repo_root: &Path) -> CliCommand {
    if let Ok(cli_path) = env::var("SPUD_IMPRINT_CLI") {
        return CliCommand::Executable(PathBuf::from(cli_path));
    }

    let packaged_cli = repo_root
        .join("dist")
        .join("spud-imprint-windows-x64")
        .join("spud-imprint.exe");
    if packaged_cli.is_file() {
        return CliCommand::Executable(packaged_cli);
    }

    let venv_python = repo_root.join(".venv").join("Scripts").join("python.exe");
    if venv_python.is_file() {
        return CliCommand::PythonModule(venv_python);
    }

    CliCommand::PythonModule(PathBuf::from("python"))
}

fn build_command(
    cli: &CliCommand,
    request: &BatchRequest,
) -> (PathBuf, Vec<String>, Vec<String>) {
    let batch_args = vec![
        "batch".to_string(),
        "--input".to_string(),
        request.input_dir.clone(),
        "--output".to_string(),
        request.output_dir.clone(),
        "--config".to_string(),
        request.config_file.clone(),
    ];

    match cli {
        CliCommand::Executable(path) => {
            let display = display_command(path, &batch_args);
            (path.clone(), batch_args, display)
        }
        CliCommand::PythonModule(path) => {
            let mut args = vec!["-m".to_string(), "spud_imprint".to_string()];
            args.extend(batch_args);
            let display = display_command(path, &args);
            (path.clone(), args, display)
        }
    }
}

fn display_command(program: &Path, args: &[String]) -> Vec<String> {
    let mut command = vec![program.display().to_string()];
    command.extend(args.iter().cloned());
    command
}
