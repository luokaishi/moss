/**
 * MOSS v9.3 - PyCharm Plugin: LSP Client
 *
 * 与 MOSS LSP 服务器通信的核心客户端
 * 支持 stdio 和 TCP 两种传输方式
 */

package com.moss.devtools

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import java.io.*
import java.net.Socket
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

/**
 * MOSS LSP 客户端
 *
 * 通过 JSON-RPC 2.0 协议与 MOSS Language Server 通信
 */
class MossLspClient(private val project: Project) {

    private val logger = Logger.getInstance(MossLspClient::class.java)
    private val gson = Gson()
    private val requestId = AtomicInteger(0)
    private val pendingRequests = ConcurrentHashMap<Int, (JsonObject?) -> Unit>()

    private var process: Process? = null
    private var socket: Socket? = null
    private var writer: BufferedWriter? = null
    private var reader: BufferedReader? = null
    private var readerThread: Thread? = null
    private var running = false

    // 事件监听器
    var onDiagnostics: ((uri: String, diagnostics: List<MossDiagnostic>) -> Unit)? = null
    var onServerStatus: ((running: Boolean) -> Unit)? = null

    /**
     * 启动 LSP 服务器 (stdio 模式)
     */
    fun startStdio(serverScript: String, pythonPath: String = "python3"): Boolean {
        try {
            val processBuilder = ProcessBuilder(pythonPath, serverScript, "--stdio")
            processBuilder.redirectErrorStream(true)
            process = processBuilder.start()

            writer = BufferedWriter(OutputStreamWriter(process!!.outputStream, "UTF-8"))
            reader = BufferedReader(InputStreamReader(process!!.inputStream, "UTF-8"))

            running = true
            startReaderThread()

            logger.info("MOSS LSP Server started (stdio)")
            onServerStatus?.invoke(true)
            return true
        } catch (e: Exception) {
            logger.error("Failed to start MOSS LSP server", e)
            return false
        }
    }

    /**
     * 启动 LSP 服务器 (TCP 模式)
     */
    fun startTcp(host: String = "127.0.0.1", port: Int = 2087): Boolean {
        try {
            socket = Socket(host, port)
            writer = BufferedWriter(OutputStreamWriter(socket!!.getOutputStream(), "UTF-8"))
            reader = BufferedReader(InputStreamReader(socket!!.getInputStream(), "UTF-8"))

            running = true
            startReaderThread()

            logger.info("MOSS LSP Server connected (TCP $host:$port)")
            onServerStatus?.invoke(true)
            return true
        } catch (e: Exception) {
            logger.error("Failed to connect to MOSS LSP server", e)
            return false
        }
    }

    /**
     * 停止 LSP 服务器
     */
    fun stop() {
        running = false

        try {
            sendRequest("shutdown", emptyMap<String, Any>()) {}
        } catch (_: Exception) {}

        try {
            sendNotification("exit", emptyMap<String, Any>())
        } catch (_: Exception) {}

        readerThread?.interrupt()
        writer?.close()
        reader?.close()
        process?.destroy()
        socket?.close()

        process = null
        socket = null
        writer = null
        reader = null
        readerThread = null

        onServerStatus?.invoke(false)
        logger.info("MOSS LSP Server stopped")
    }

    /**
     * 发送 initialize 请求
     */
    fun initialize(rootPath: String, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "processId" to ProcessHandle.current().pid(),
            "rootUri" to "file://$rootPath",
            "capabilities" to mapOf(
                "textDocument" to mapOf(
                    "completion" to mapOf("completionItem" to mapOf("snippetSupport" to true)),
                    "hover" to mapOf("contentFormat" to listOf("markdown", "plaintext")),
                    "codeAction" to mapOf("codeActionLiteralSupport" to emptyMap<String, Any>()),
                    "publishDiagnostics" to mapOf("relatedInformation" to true),
                )
            )
        )
        sendRequest("initialize", params, callback)
    }

    /**
     * 发送 initialized 通知
     */
    fun initialized() {
        sendNotification("initialized", mapOf("capabilities" to emptyMap<String, Any>()))
    }

    /**
     * 发送 textDocument/didOpen 通知
     */
    fun didOpen(uri: String, languageId: String = "python", version: Int = 0, text: String) {
        val params = mapOf(
            "textDocument" to mapOf(
                "uri" to uri,
                "languageId" to languageId,
                "version" to version,
                "text" to text
            )
        )
        sendNotification("textDocument/didOpen", params)
    }

    /**
     * 发送 textDocument/didChange 通知
     */
    fun didChange(uri: String, version: Int, text: String) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri, "version" to version),
            "contentChanges" to listOf(mapOf("text" to text))
        )
        sendNotification("textDocument/didChange", params)
    }

    /**
     * 发送 textDocument/didClose 通知
     */
    fun didClose(uri: String) {
        val params = mapOf("textDocument" to mapOf("uri" to uri))
        sendNotification("textDocument/didClose", params)
    }

    /**
     * 请求代码补全
     */
    fun completion(uri: String, line: Int, character: Int, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri),
            "position" to mapOf("line" to line, "character" to character)
        )
        sendRequest("textDocument/completion", params, callback)
    }

    /**
     * 请求悬停信息
     */
    fun hover(uri: String, line: Int, character: Int, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri),
            "position" to mapOf("line" to line, "character" to character)
        )
        sendRequest("textDocument/hover", params, callback)
    }

    /**
     * 请求跳转定义
     */
    fun definition(uri: String, line: Int, character: Int, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri),
            "position" to mapOf("line" to line, "character" to character)
        )
        sendRequest("textDocument/definition", params, callback)
    }

    /**
     * 请求查找引用
     */
    fun references(uri: String, line: Int, character: Int, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri),
            "position" to mapOf("line" to line, "character" to character),
            "context" to mapOf("includeDeclaration" to true)
        )
        sendRequest("textDocument/references", params, callback)
    }

    /**
     * 请求代码操作
     */
    fun codeAction(uri: String, startLine: Int, startChar: Int,
                   endLine: Int, endChar: Int, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri),
            "range" to mapOf(
                "start" to mapOf("line" to startLine, "character" to startChar),
                "end" to mapOf("line" to endLine, "character" to endChar)
            ),
            "context" to mapOf("diagnostics" to emptyList<Any>())
        )
        sendRequest("textDocument/codeAction", params, callback)
    }

    /**
     * 请求文档符号
     */
    fun documentSymbol(uri: String, callback: (JsonObject?) -> Unit) {
        val params = mapOf("textDocument" to mapOf("uri" to uri))
        sendRequest("textDocument/documentSymbol", params, callback)
    }

    /**
     * 请求重命名
     */
    fun rename(uri: String, line: Int, character: Int, newName: String, callback: (JsonObject?) -> Unit) {
        val params = mapOf(
            "textDocument" to mapOf("uri" to uri),
            "position" to mapOf("line" to line, "character" to character),
            "newName" to newName
        )
        sendRequest("textDocument/rename", params, callback)
    }

    // ──────────────────────────────────────────────────────────
    // JSON-RPC Protocol
    // ──────────────────────────────────────────────────────────

    private fun sendRequest(method: String, params: Map<String, Any>, callback: (JsonObject?) -> Unit) {
        val id = requestId.incrementAndGet()
        pendingRequests[id] = callback

        val message = mapOf(
            "jsonrpc" to "2.0",
            "id" to id,
            "method" to method,
            "params" to params
        )

        writeMessage(gson.toJson(message))
    }

    private fun sendNotification(method: String, params: Map<String, Any>) {
        val message = mapOf(
            "jsonrpc" to "2.0",
            "method" to method,
            "params" to params
        )

        writeMessage(gson.toJson(message))
    }

    private fun writeMessage(content: String) {
        try {
            val header = "Content-Length: ${content.toByteArray(Charsets.UTF_8).size}\r\n\r\n"
            writer?.apply {
                write(header)
                write(content)
                flush()
            }
        } catch (e: Exception) {
            logger.error("Failed to write LSP message", e)
        }
    }

    private fun startReaderThread() {
        readerThread = Thread({
            while (running) {
                try {
                    val message = readMessage() ?: continue
                    handleMessage(message)
                } catch (e: InterruptedException) {
                    break
                } catch (e: Exception) {
                    if (running) logger.error("LSP reader error", e)
                }
            }
        }, "MOSS-LSP-Reader")
        readerThread?.isDaemon = true
        readerThread?.start()
    }

    private fun readMessage(): JsonObject? {
        try {
            var contentLength = -1
            while (true) {
                val line = reader?.readLine() ?: return null
                if (line.isEmpty()) break
                if (line.startsWith("Content-Length:")) {
                    contentLength = line.substring(15).trim().toInt()
                }
            }

            if (contentLength <= 0) return null

            val buffer = CharArray(contentLength)
            var read = 0
            while (read < contentLength) {
                val n = reader?.read(buffer, read, contentLength - read) ?: return null
                if (n == -1) return null
                read += n
            }

            return gson.fromJson(String(buffer), JsonObject::class.java)
        } catch (e: Exception) {
            return null
        }
    }

    private fun handleMessage(message: JsonObject) {
        // 处理响应
        if (message.has("id")) {
            val id = message.get("id").asInt
            pendingRequests.remove(id)?.let { callback ->
                val result = if (message.has("result")) message.getAsJsonObject("result") else null
                callback(result)
            }
        }

        // 处理通知
        if (message.has("method")) {
            val method = message.get("method").asString
            val params = message.getAsJsonObject("params")

            when (method) {
                "textDocument/publishDiagnostics" -> handleDiagnostics(params)
                // 可以添加更多通知处理
            }
        }
    }

    private fun handleDiagnostics(params: JsonObject?) {
        params ?: return

        val uri = params.get("uri")?.asString ?: return
        val diagnosticsArray = params.getAsJsonArray("diagnostics") ?: return

        val diagnostics = diagnosticsArray.map { element ->
            val diag = element.asJsonObject
            val range = diag.getAsJsonObject("range")
            val start = range.getAsJsonObject("start")

            MossDiagnostic(
                uri = uri,
                line = start.get("line").asInt,
                character = start.get("character").asInt,
                message = diag.get("message").asString,
                severity = diag.get("severity")?.asInt ?: 2,
                source = diag.get("source")?.asString ?: "moss",
                code = diag.get("code")?.asString
            )
        }

        onDiagnostics?.invoke(uri, diagnostics)
    }

    fun isRunning(): Boolean = running && (process?.isAlive == true || socket?.isConnected == true)
}

/**
 * MOSS 诊断数据类
 */
data class MossDiagnostic(
    val uri: String,
    val line: Int,
    val character: Int,
    val message: String,
    val severity: Int,
    val source: String,
    val code: String?
)
