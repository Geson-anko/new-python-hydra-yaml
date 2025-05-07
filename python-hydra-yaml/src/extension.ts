import * as vscode from 'vscode';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind
} from 'vscode-languageclient/node';
import { PythonExtension } from '@vscode/python-extension';

let client: LanguageClient | undefined;

/**
 * Gets the path to the active Python interpreter from VS Code Python extension
 */
export async function getActivePythonPath(): Promise<string | undefined> {
  try {
    const pythonApi = await PythonExtension.api();
    const activePath = pythonApi.environments.getActiveEnvironmentPath();
    return activePath?.path;
  } catch {
    return undefined;
  }
}

/**
 * Prompts the user to select a Python interpreter
 */
async function selectPythonInterpreter(): Promise<string | undefined> {
  await vscode.commands.executeCommand('python.setInterpreter');
  return await getActivePythonPath();
}

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  console.log('Activating Hydra YAML extension');

  // Register the selectConfigDir command
  const selectConfigDirCommand = vscode.commands.registerCommand(
    'python-hydra-yaml.selectConfigDir',
    selectConfigDir
  );
  context.subscriptions.push(selectConfigDirCommand);

  // Check if configDir is set, and prompt user if not
  let configDir = vscode.workspace.getConfiguration('pythonHydraYaml').get('configDir', '');
  if (!configDir) {
    const result = await vscode.window.showInformationMessage(
      'No Hydra configuration directory selected. Would you like to select one?',
      'Select Directory', 'Cancel'
    );

    if (result === 'Select Directory') {
      configDir = await selectConfigDir() || '';
    }
  }
  if (!configDir){
    return;
  }

  try {
    // Get Python interpreter path
    let pythonPath = await getActivePythonPath();

    // If no Python interpreter is selected, prompt the user to select one
    if (!pythonPath) {
      const result = await vscode.window.showInformationMessage(
        'No Python interpreter selected. Would you like to select one?',
        'Select Interpreter', 'Cancel'
      );

      if (result === 'Select Interpreter') {
        pythonPath = await selectPythonInterpreter();
      }

      if (!pythonPath) {
        console.log("Can not get Python Interpreter.");
        vscode.window.showErrorMessage('Failed to start Hydra YAML Language Server: No Python interpreter selected');
        return;
      }
    }

    console.log(`Using Python interpreter: ${pythonPath}`);

    // Server module path
    const serverArgs = ['-m', 'hydra_yaml_lsp'];

    // Server options
    const serverOptions: ServerOptions = {
      command: pythonPath,
      args: serverArgs,
      transport: TransportKind.stdio,
      options: {
        env: { ...process.env }
      }
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
      outputChannelName: 'Hydra YAML Language Server',
      documentSelector: [
        { scheme: 'file', language: 'yaml' }
      ],
      synchronize: {
        fileEvents: vscode.workspace.createFileSystemWatcher('**/*.{yaml,yml}'),
      },
      initializationOptions: {
        configDir: configDir
      }
    };

    // Create and start the client
    client = new LanguageClient(
      'hydraYamlLanguageServer',
      'Hydra YAML Language Server',
      serverOptions,
      clientOptions
    );

    client.start();

    context.subscriptions.push({
      dispose: () => {
        if (client) {
          client.stop();
        }
      }
    });

    console.log('Hydra YAML Language Server started');

    // Register restart command
    const restartCommand = vscode.commands.registerCommand('python-hydra-yaml.restart', async () => {
      if (!client) {
        return;
      }
      try {
        await client.stop();
        client.start();
        vscode.window.showInformationMessage('Hydra YAML Language Server restarted');
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to restart server: ${error instanceof Error ? error.message : String(error)}`);
      }
    });

    context.subscriptions.push(restartCommand);

    // Shift+Enter for trigger completion.
    const triggerCompletionCommand = vscode.commands.registerCommand('python-hydra-yaml.triggerCompletionWithEnter', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        return;
      }

      await vscode.commands.executeCommand('type', { text: '\n' });
      await vscode.commands.executeCommand('editor.action.triggerSuggest');
    });

    context.subscriptions.push(triggerCompletionCommand);

    // Register status bar item to show server status
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = '$(plug) Hydra YAML';
    statusBarItem.tooltip = 'Hydra YAML Language Server active';
    statusBarItem.command = 'python-hydra-yaml.restart';
    statusBarItem.show();

    context.subscriptions.push(statusBarItem);

  } catch (error) {
    vscode.window.showErrorMessage(`Failed to start Hydra YAML Language Server: ${error instanceof Error ? error.message : String(error)}`);
  }
}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined;
  }
  console.log('Deactivating Hydra YAML extension');
  return client.stop();
}

// Function to select config directory
async function selectConfigDir(): Promise<string | undefined> {
  const options: vscode.OpenDialogOptions = {
    canSelectFolders: true,
    canSelectFiles: false,
    canSelectMany: false,
    openLabel: 'Select Hydra Config Directory'
  };

  const fileUri = await vscode.window.showOpenDialog(options);
  if (fileUri && fileUri.length > 0) {
    const dirPath = fileUri[0].fsPath;
    // Update configuration
    await vscode.workspace.getConfiguration('pythonHydraYaml').update('configDir', dirPath);
    vscode.window.showInformationMessage(`Hydra config directory set to: ${dirPath}`);
    return dirPath;
  }

  return undefined;
}
