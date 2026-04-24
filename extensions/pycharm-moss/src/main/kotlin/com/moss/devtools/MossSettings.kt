/**
 * MOSS v9.3 - PyCharm Plugin: Settings
 *
 * 管理插件配置，包括 LSP 服务器路径、分析参数等
 */

package com.moss.devtools

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.util.xmlb.XmlSerializerUtil

@State(
    name = "com.moss.devtools.MossSettings",
    storages = [Storage("moss_settings.xml")]
)
class MossSettings : PersistentStateComponent<MossSettings> {

    // LSP Server
    var serverPath: String = ""
    var pythonPath: String = "python3"
    var autoStartServer: Boolean = true

    // Analysis
    var enableIncrementalAnalysis: Boolean = true
    var enableParallelProcessing: Boolean = true
    var maxWorkers: Int = 0  // 0 = auto-detect

    // Diagnostics
    var enableDiagnostics: Boolean = true
    var longFunctionThreshold: Int = 50
    var highComplexityThreshold: Int = 10
    var showUnusedImports: Boolean = true

    // Refactoring
    var previewChanges: Boolean = true
    var autoUpdateImports: Boolean = true

    // Performance
    var cacheLevel: String = "full"  // none, memory, disk, full

    // Server State
    var serverPort: Int = 2087
    var serverRunning: Boolean = false

    override fun getState(): MossSettings = this

    override fun loadState(state: MossSettings) {
        XmlSerializerUtil.copyBean(state, this)
    }

    companion object {
        fun getInstance(): MossSettings =
            ApplicationManager.getApplication().getService(MossSettings::class.java)
    }
}
