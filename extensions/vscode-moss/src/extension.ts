/**
 * MOSS v9.3 - VSCode Extension Entry Point
 *
 * 核心功能:
 * 1. LSP 客户端连接管理
 * 2. 命令注册
 * 3. 状态栏
 * 4. 侧边栏面板
 */

import * as path from 'path';
import * as fs from 'fs';
import {
    workspace,
    ExtensionContext,
    StatusBarAlignment,
    WindowState,
    commands,
    window,
    Uri,
    TextEditor,
    ViewColumn,
    WebviewPanel,
    ProgressLocation,
    Diagnostic,
    DiagnosticSeverity,
    Range,
    Position,
    languages,
    CodeActionProvider,
    CodeAction,
    CodeActionKind,
    ProviderResult,
    EventEmitter,
    Event,
    Disposable,
    TextDocument,
    CancellationToken,
    CodeActionContext
} from 'vscode';

import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind,
    NotificationType,
    RequestType
} from 'vscode-languageclient/node';


// ──────────────────────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────────────────────

const MOSS_OUTPUT_CHANNEL = window.createOutputChannel('MOSS');
let client: LanguageClient | undefined;
let statusBarItem: any;
let mossPanel: WebviewPanel | undefined;

// ──────────────────────────────────────────────────────────────
// Extension Activation
// ──────────────────────────────────────────────────────────────

export function activate(context: ExtensionContext) {
    MOSS_OUTPUT_CHANNEL.appendLine('MOSS v9.3.0 - Extension Activating...');

    // 1. 创建状态栏
    statusBarItem = window.createStatusBarItem(StatusBarAlignment.Right, 100);
    statusBarItem.text = '$(beaker) MOSS';
    statusBarItem.tooltip = 'MOSS - Smart Code Refactoring';
    statusBarItem.command = 'moss.showDiagnostics';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // 2. 注册命令
    registerCommands(context);

    // 3. 自动启动 LSP 服务器
    if (workspace.getConfiguration('moss').get('autoStart', true)) {
        startServer(context);
    }

    // 4. 注册代码操作提供器
    const codeActionProvider = new MossCodeActionProvider();
    context.subscriptions.push(
        languages.registerCodeActionsProvider(
            { scheme: 'file', language: 'python' },
            codeActionProvider,
            { providedCodeActionKinds: MossCodeActionProvider.providedKinds }
        )
    );

    MOSS_OUTPUT_CHANNEL.appendLine('MOSS v9.3.0 - Extension Activated');
}

// ──────────────────────────────────────────────────────────────
// Command Registration
// ──────────────────────────────────────────────────────────────

function registerCommands(context: ExtensionContext) {
    // Server management
    context.subscriptions.push(
        commands.registerCommand('moss.startServer', () => startServer(context)),
        commands.registerCommand('moss.stopServer', () => stopServer()),
        commands.registerCommand('moss.restartServer', async () => {
            await stopServer();
            await startServer(context);
        }),
    );

    // Analysis
    context.subscriptions.push(
        commands.registerCommand('moss.analyzeProject', () => analyzeProject()),
        commands.registerCommand('moss.analyzeFile', () => analyzeCurrentFile()),
        commands.registerCommand('moss.showDiagnostics', () => showDiagnosticsPanel()),
    );

    // Refactoring
    context.subscriptions.push(
        commands.registerCommand('moss.quickRefactor', () => quickRefactor()),
        commands.registerCommand('moss.extractFunction', () => extractFunction()),
        commands.registerCommand('moss.extractVariable', () => extractVariable()),
        commands.registerCommand('moss.organizeImports', () => organizeImports()),
        commands.registerCommand('moss.moveSymbol', () => moveSymbol()),
    );

    // Impact analysis
    context.subscriptions.push(
        commands.registerCommand('moss.showImpactAnalysis', () => showImpactAnalysis()),
        commands.registerCommand('moss.showPerformanceStats', () => showPerformanceStats()),
    );

    // Settings
    context.subscriptions.push(
        commands.registerCommand('moss.configureSettings', () => {
            commands.executeCommand('workbench.action.openSettings', 'moss');
        }),
    );
}

// ──────────────────────────────────────────────────────────────
// LSP Server Management
// ──────────────────────────────────────────────────────────────

async function startServer(context: ExtensionContext): Promise<void> {
    if (client) {
        window.showWarningMessage('MOSS server is already running');
        return;
    }

    const config = workspace.getConfiguration('moss');
    const pythonPath = config.get<string>('pythonPath', 'python3');
    const serverPath = config.get<string>('serverPath', '');

    // 确定 LSP 服务器脚本路径
    let serverScript: string;
    if (serverPath) {
        serverScript = serverPath;
    } else {
        // 使用默认路径
        serverScript = path.join(
            context.extensionPath,
            '..',
            '..',
            'moss',
            'core',
            'lsp_server.py'
        );
    }

    // 验证文件存在
    if (!fs.existsSync(serverScript)) {
        // 使用内置服务器
        serverScript = path.join(context.extensionPath, 'server', 'lsp_server.py');
    }

    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: [serverScript, '--stdio'],
        transport: TransportKind.stdio,
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'python' }],
        synchronize: {
            configurationSection: 'moss',
            fileEvents: workspace.createFileSystemWatcher('**/*.py'),
        },
        outputChannel: MOSS_OUTPUT_CHANNEL,
        traceOutputChannel: MOSS_OUTPUT_CHANNEL,
    };

    try {
        client = new LanguageClient(
            'moss-lsp',
            'MOSS Language Server',
            serverOptions,
            clientOptions
        );

        await client.start();

        // 更新状态栏
        statusBarItem.text = '$(check) MOSS';
        statusBarItem.tooltip = 'MOSS Server: Running';

        window.showInformationMessage('MOSS Language Server started');

        // 监听诊断
        client.onNotification(
            new NotificationType('textDocument/publishDiagnostics'),
            (params: any) => {
                updateDiagnosticsCount(params.diagnostics?.length || 0);
            }
        );

    } catch (error) {
        MOSS_OUTPUT_CHANNEL.appendLine(`Failed to start MOSS server: ${error}`);
        statusBarItem.text = '$(error) MOSS';
        statusBarItem.tooltip = 'MOSS Server: Failed to start';
        window.showErrorMessage(`Failed to start MOSS server: ${error}`);
    }
}

async function stopServer(): Promise<void> {
    if (!client) {
        return;
    }

    try {
        await client.stop();
        client = undefined;

        statusBarItem.text = '$(beaker) MOSS';
        statusBarItem.tooltip = 'MOSS Server: Stopped';

        window.showInformationMessage('MOSS Language Server stopped');
    } catch (error) {
        MOSS_OUTPUT_CHANNEL.appendLine(`Failed to stop MOSS server: ${error}`);
    }
}

// ──────────────────────────────────────────────────────────────
// Analysis Commands
// ──────────────────────────────────────────────────────────────

async function analyzeProject(): Promise<void> {
    if (!client) {
        window.showWarningMessage('MOSS server is not running. Start it first.');
        return;
    }

    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: 'MOSS: Analyzing project...',
            cancellable: true,
        },
        async (progress, token) => {
            try {
                // 发送自定义分析请求
                const result = await client.sendRequest(
                    new RequestType('moss/analyzeProject'),
                    { uri: workspace.rootPath },
                    token
                );

                window.showInformationMessage(
                    `MOSS: Analysis complete. ${result?.issues || 0} issues found.`
                );
            } catch (error) {
                window.showErrorMessage(`MOSS: Analysis failed - ${error}`);
            }
        }
    );
}

async function analyzeCurrentFile(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'python') {
        window.showWarningMessage('Please open a Python file');
        return;
    }

    if (!client) {
        window.showWarningMessage('MOSS server is not running');
        return;
    }

    // 触发诊断
    const uri = editor.document.uri.toString();
    window.showInformationMessage('MOSS: Analyzing current file...');
}

async function showDiagnosticsPanel(): Promise<void> {
    // 创建或显示 Webview 面板
    if (mossPanel) {
        mossPanel.reveal();
        return;
    }

    mossPanel = window.createWebviewPanel(
        'moss-diagnostics',
        'MOSS Diagnostics',
        ViewColumn.Two,
        { enableScripts: true }
    );

    mossPanel.webview.html = getDiagnosticsHtml();

    mossPanel.onDidDispose(() => {
        mossPanel = undefined;
    });
}

// ──────────────────────────────────────────────────────────────
// Refactoring Commands
// ──────────────────────────────────────────────────────────────

async function quickRefactor(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'python') {
        return;
    }

    // 获取可用的重构操作
    const actions = await commands.executeCommand(
        'vscode.executeCodeActionProvider',
        editor.document.uri,
        editor.selection
    );

    if (!actions || actions.length === 0) {
        window.showInformationMessage('MOSS: No refactoring suggestions available');
        return;
    }

    // 显示快速选择
    const items = actions.map((action: any) => ({
        label: action.title,
        description: action.kind?.replace('refactor.', '') || '',
        action,
    }));

    const selected = await window.showQuickPick(items, {
        placeHolder: 'Select a refactoring action',
    });

    if (selected) {
        await commands.executeCommand(
            'vscode.executeCodeAction',
            selected.action
        );
    }
}

async function extractFunction(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor || !editor.selection) {
        window.showWarningMessage('Select code to extract into a function');
        return;
    }

    const functionName = await window.showInputBox({
        prompt: 'Enter function name',
        placeHolder: 'extracted_function',
    });

    if (!functionName) {
        return;
    }

    // 通过 LSP 发送重构请求
    if (client) {
        try {
            await client.sendRequest(
                new RequestType('moss/extractFunction'),
                {
                    uri: editor.document.uri.toString(),
                    range: {
                        start: { line: editor.selection.start.line, character: editor.selection.start.character },
                        end: { line: editor.selection.end.line, character: editor.selection.end.character },
                    },
                    functionName,
                }
            );
        } catch (error) {
            window.showErrorMessage(`Extract function failed: ${error}`);
        }
    }
}

async function extractVariable(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor || !editor.selection) {
        window.showWarningMessage('Select an expression to extract');
        return;
    }

    const varName = await window.showInputBox({
        prompt: 'Enter variable name',
        placeHolder: 'extracted_var',
    });

    if (!varName) {
        return;
    }

    if (client) {
        try {
            await client.sendRequest(
                new RequestType('moss/extractVariable'),
                {
                    uri: editor.document.uri.toString(),
                    range: {
                        start: { line: editor.selection.start.line, character: editor.selection.start.character },
                        end: { line: editor.selection.end.line, character: editor.selection.end.character },
                    },
                    variableName: varName,
                }
            );
        } catch (error) {
            window.showErrorMessage(`Extract variable failed: ${error}`);
        }
    }
}

async function organizeImports(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'python') {
        return;
    }

    if (client) {
        try {
            await client.sendRequest(
                new RequestType('moss/organizeImports'),
                { uri: editor.document.uri.toString() }
            );
        } catch (error) {
            window.showErrorMessage(`Organize imports failed: ${error}`);
        }
    }
}

async function moveSymbol(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor) {
        return;
    }

    // 获取光标下的符号
    const position = editor.selection.active;
    const symbolName = await window.showInputBox({
        prompt: 'Symbol name to move',
        value: getWordAtPosition(editor, position),
    });

    if (!symbolName) {
        return;
    }

    const targetModule = await window.showInputBox({
        prompt: 'Target module path',
        placeHolder: 'moss.core.new_module',
    });

    if (!targetModule) {
        return;
    }

    if (client) {
        try {
            const result = await client.sendRequest(
                new RequestType('moss/moveSymbol'),
                {
                    symbolName,
                    sourceModule: editor.document.uri.toString(),
                    targetModule,
                }
            );

            if (result?.success) {
                window.showInformationMessage(
                    `MOSS: Moved ${symbolName} to ${targetModule}`
                );
            }
        } catch (error) {
            window.showErrorMessage(`Move symbol failed: ${error}`);
        }
    }
}

// ──────────────────────────────────────────────────────────────
// Impact Analysis
// ──────────────────────────────────────────────────────────────

async function showImpactAnalysis(): Promise<void> {
    const editor = window.activeTextEditor;
    if (!editor) {
        return;
    }

    if (!client) {
        window.showWarningMessage('MOSS server is not running');
        return;
    }

    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: 'MOSS: Analyzing impact...',
        },
        async () => {
            try {
                const result = await client.sendRequest(
                    new RequestType('moss/impactAnalysis'),
                    {
                        uri: editor.document.uri.toString(),
                        position: {
                            line: editor.selection.active.line,
                            character: editor.selection.active.character,
                        },
                    }
                );

                if (result) {
                    const panel = window.createWebviewPanel(
                        'moss-impact',
                        'MOSS Impact Analysis',
                        ViewColumn.Two,
                        {}
                    );
                    panel.webview.html = getImpactHtml(result);
                }
            } catch (error) {
                window.showErrorMessage(`Impact analysis failed: ${error}`);
            }
        }
    );
}

async function showPerformanceStats(): Promise<void> {
    if (!client) {
        window.showWarningMessage('MOSS server is not running');
        return;
    }

    try {
        const stats = await client.sendRequest(
            new RequestType('moss/performanceStats'),
            {}
        );

        if (stats) {
            const panel = window.createWebviewPanel(
                'moss-perf',
                'MOSS Performance Stats',
                ViewColumn.Two,
                {}
            );
            panel.webview.html = getPerformanceHtml(stats);
        }
    } catch (error) {
        window.showErrorMessage(`Failed to get performance stats: ${error}`);
    }
}

// ──────────────────────────────────────────────────────────────
// Code Action Provider
// ──────────────────────────────────────────────────────────────

class MossCodeActionProvider implements CodeActionProvider {
    static readonly providedKinds = [
        CodeActionKind.QuickFix,
        CodeActionKind.Refactor,
        CodeActionKind.Refactor.Extract,
        CodeActionKind.RefactorInline,
        CodeActionKind.RefactorRewrite,
    ];

    provideCodeActions(
        document: TextDocument,
        range: Range,
        context: CodeActionContext,
        token: CancellationToken
    ): ProviderResult<CodeAction[]> {
        const actions: CodeAction[] = [];

        // 基于诊断的快速修复
        for (const diag of context.diagnostics) {
            if (diag.source === 'moss') {
                const action = new CodeAction(
                    `MOSS: Fix ${diag.message}`,
                    CodeActionKind.QuickFix
                );
                action.diagnostics = [diag];
                action.isPreferred = true;
                actions.push(action);
            }
        }

        // 重构操作
        if (!range.isEmpty) {
            const extractFunc = new CodeAction(
                'MOSS: Extract Function',
                CodeActionKind.Refactor.Extract
            );
            actions.push(extractFunc);

            const extractVar = new CodeAction(
                'MOSS: Extract Variable',
                CodeActionKind.Refactor.Extract
            );
            actions.push(extractVar);
        }

        // 导入整理
        const organizeImports = new CodeAction(
            'MOSS: Organize Imports',
            CodeActionKind.RefactorRewrite
        );
        actions.push(organizeImports);

        return actions;
    }
}

// ──────────────────────────────────────────────────────────────
// Utility Functions
// ──────────────────────────────────────────────────────────────

function updateDiagnosticsCount(count: number): void {
    if (count > 0) {
        statusBarItem.text = `$(warning) MOSS (${count})`;
    } else {
        statusBarItem.text = '$(check) MOSS';
    }
}

function getWordAtPosition(editor: TextEditor, position: Position): string {
    const line = editor.document.lineAt(position.line).text;
    let start = position.character;
    let end = position.character;

    while (start > 0 && /\w/.test(line[start - 1])) {
        start--;
    }
    while (end < line.length && /\w/.test(line[end])) {
        end++;
    }

    return line.substring(start, end);
}

function getDiagnosticsHtml(): string {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MOSS Diagnostics</title>
        <style>
            body { font-family: -apple-system, sans-serif; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
            .header { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #4fc1ff; }
            .metric { display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 8px; background: #2d2d2d; }
            .metric-value { font-size: 24px; font-weight: 700; color: #4fc1ff; }
            .metric-label { font-size: 12px; color: #888; }
            .category { margin: 20px 0; }
            .category-title { font-size: 14px; font-weight: 600; color: #ccc; border-bottom: 1px solid #444; padding-bottom: 5px; }
            .issue { padding: 8px 12px; margin: 4px 0; border-radius: 4px; background: #2d2d2d; cursor: pointer; }
            .issue:hover { background: #3d3d3d; }
            .severity-error { border-left: 3px solid #f44747; }
            .severity-warning { border-left: 3px solid #ffcc00; }
            .severity-info { border-left: 3px solid #4fc1ff; }
            .severity-hint { border-left: 3px solid #4ec9b0; }
        </style>
    </head>
    <body>
        <div class="header">MOSS Code Quality Dashboard</div>
        <div id="metrics">
            <div class="metric"><div class="metric-value" id="total">0</div><div class="metric-label">Total Issues</div></div>
            <div class="metric"><div class="metric-value" id="errors">0</div><div class="metric-label">Errors</div></div>
            <div class="metric"><div class="metric-value" id="warnings">0</div><div class="metric-label">Warnings</div></div>
            <div class="metric"><div class="metric-value" id="info">0</div><div class="metric-label">Info</div></div>
        </div>
        <div class="category">
            <div class="category-title">Issues</div>
            <div id="issues">No issues detected. Run analysis to check code quality.</div>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            // Listen for updates from extension
            window.addEventListener('message', event => {
                const data = event.data;
                document.getElementById('total').textContent = data.total || 0;
                document.getElementById('errors').textContent = data.errors || 0;
                document.getElementById('warnings').textContent = data.warnings || 0;
                document.getElementById('info').textContent = data.info || 0;
            });
        </script>
    </body>
    </html>
    `;
}

function getImpactHtml(result: any): string {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MOSS Impact Analysis</title>
        <style>
            body { font-family: -apple-system, sans-serif; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
            .header { font-size: 20px; font-weight: 600; color: #4fc1ff; margin-bottom: 20px; }
            .impact-card { padding: 15px; margin: 10px 0; border-radius: 8px; background: #2d2d2d; }
            .risk-low { border-left: 4px solid #4ec9b0; }
            .risk-medium { border-left: 4px solid #ffcc00; }
            .risk-high { border-left: 4px solid #f44747; }
            .stat { display: inline-block; padding: 5px 15px; margin: 5px; background: #3d3d3d; border-radius: 4px; }
            .stat-value { font-size: 18px; font-weight: 700; color: #4fc1ff; }
            .file-list { font-family: monospace; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="header">Impact Analysis</div>
        <div class="impact-card risk-${result?.riskLevel || 'low'}">
            <div><strong>Risk Level:</strong> ${(result?.riskLevel || 'low').toUpperCase()}</div>
            <div><strong>Affected Files:</strong> ${result?.affectedFiles?.length || 0}</div>
            <div><strong>Affected Symbols:</strong> ${result?.affectedSymbols?.length || 0}</div>
        </div>
    </body>
    </html>
    `;
}

function getPerformanceHtml(stats: any): string {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MOSS Performance</title>
        <style>
            body { font-family: -apple-system, sans-serif; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
            .header { font-size: 20px; font-weight: 600; color: #4fc1ff; margin-bottom: 20px; }
            .perf-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
            .perf-card { padding: 15px; border-radius: 8px; background: #2d2d2d; text-align: center; }
            .perf-value { font-size: 28px; font-weight: 700; color: #4fc1ff; }
            .perf-label { font-size: 12px; color: #888; margin-top: 5px; }
            .bar { height: 4px; background: #4fc1ff; border-radius: 2px; margin-top: 8px; }
        </style>
    </head>
    <body>
        <div class="header">MOSS Performance Stats</div>
        <div class="perf-grid">
            <div class="perf-card">
                <div class="perf-value">${stats?.cacheHitRate?.toFixed(1) || '0'}%</div>
                <div class="perf-label">Cache Hit Rate</div>
                <div class="bar" style="width: ${stats?.cacheHitRate || 0}%"></div>
            </div>
            <div class="perf-card">
                <div class="perf-value">${stats?.throughput?.toFixed(0) || '0'}</div>
                <div class="perf-label">Files/Second</div>
            </div>
            <div class="perf-card">
                <div class="perf-value">${stats?.speedup?.toFixed(1) || '1.0'}x</div>
                <div class="perf-label">Speedup</div>
            </div>
        </div>
    </body>
    </html>
    `;
}

// ──────────────────────────────────────────────────────────────
// Extension Deactivation
// ──────────────────────────────────────────────────────────────

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
