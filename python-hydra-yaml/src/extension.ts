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

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  console.log('Activating Hydra YAML extension');

  try {
    // Get Python interpreter path
    const pythonPath = await getActivePythonPath();
	if (!pythonPath){
		console.log("Can not get Python Interpreter.");
		return;
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
      // Register the server for YAML files
      documentSelector: [
        { scheme: 'file', language: 'yaml' }
      ],
      // Synchronize relevant file events
      synchronize: {
        fileEvents: vscode.workspace.createFileSystemWatcher('**/*.{yaml,yml}')
      },
      // Enable output channel for debugging
      outputChannelName: 'Hydra YAML Language Server'
    };

    // Create and start the client
    client = new LanguageClient(
      'hydraYamlLanguageServer',
      'Hydra YAML Language Server',
      serverOptions,
      clientOptions
    );

    // Start the client - client.start() returns a Promise, not a Disposable
    client.start();

    // Add a proper disposable for the client
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
