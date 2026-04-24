/**
 * MOSS v9.3 - PyCharm Plugin: Tool Window
 *
 * 侧边栏面板，显示代码质量指标、重构建议和性能统计
 */

package com.moss.devtools.ui

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.treeStructure.Tree
import java.awt.*
import javax.swing.*
import javax.swing.tree.DefaultMutableTreeNode
import javax.swing.tree.DefaultTreeModel

/**
 * MOSS 工具窗口工厂
 */
class MossToolWindowFactory : ToolWindowFactory {

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val panel = MossToolWindowPanel(project)
        val content = ContentFactory.getInstance().createContent(panel, "", false)
        toolWindow.contentManager.addContent(content)
    }

    override fun init(toolWindow: ToolWindow) {
        toolWindow.stripeTitle = "MOSS"
    }
}

/**
 * MOSS 工具窗口面板
 */
class MossToolWindowPanel(private val project: Project) : JBPanel<MossToolWindowPanel>(BorderLayout()) {

    private val statusLabel = JLabel("● MOSS Ready")
    private val metricsPanel = JPanel(GridLayout(2, 3, 10, 10))
    private val issuesTree = Tree()
    private val suggestionArea = JTextArea(5, 30)

    init {
        // 顶部状态栏
        val topBar = JPanel(FlowLayout(FlowLayout.LEFT))
        topBar.add(statusLabel)
        topBar.add(Box.createHorizontalStrut(20))
        val analyzeBtn = JButton("Analyze")
        analyzeBtn.addActionListener { runAnalysis() }
        topBar.add(analyzeBtn)
        val refreshBtn = JButton("Refresh")
        refreshBtn.addActionListener { refreshStats() }
        topBar.add(refreshBtn)
        add(topBar, BorderLayout.NORTH)

        // 指标面板
        initMetricsPanel()
        add(metricsPanel, BorderLayout.CENTER)

        // 底部建议面板
        val bottomPanel = JPanel(BorderLayout())
        bottomPanel.add(JLabel("Refactoring Suggestions:"), BorderLayout.NORTH)
        suggestionArea.isEditable = false
        suggestionArea.text = "Run analysis to see suggestions..."
        bottomPanel.add(JBScrollPane(suggestionArea), BorderLayout.CENTER)
        add(bottomPanel, BorderLayout.SOUTH)
    }

    private fun initMetricsPanel() {
        metricsPanel.add(createMetricCard("Total Issues", "0", Color.RED))
        metricsPanel.add(createMetricCard("Warnings", "0", Color.ORANGE))
        metricsPanel.add(createMetricCard("Info", "0", Color.BLUE))
        metricsPanel.add(createMetricCard("Cache Hit Rate", "0%", Color.GREEN))
        metricsPanel.add(createMetricCard("Throughput", "0 f/s", Color.CYAN))
        metricsPanel.add(createMetricCard("Speedup", "1.0x", Color.MAGENTA))
    }

    private fun createMetricCard(title: String, value: String, color: Color): JPanel {
        val card = JPanel(BorderLayout())
        card.border = BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Color.GRAY, 1),
            BorderFactory.createEmptyBorder(8, 12, 8, 12)
        )

        val valueLabel = JLabel(value)
        valueLabel.font = Font(valueLabel.font.name, Font.BOLD, 20)
        valueLabel.foreground = color
        card.add(valueLabel, BorderLayout.CENTER)

        val titleLabel = JLabel(title)
        titleLabel.font = Font(titleLabel.font.name, Font.PLAIN, 11)
        card.add(titleLabel, BorderLayout.SOUTH)

        return card
    }

    private fun runAnalysis() {
        statusLabel.text = "● MOSS Analyzing..."
        statusLabel.foreground = Color.ORANGE

        // 异步执行分析
        Thread {
            try {
                // 模拟分析过程
                Thread.sleep(500)

                SwingUtilities.invokeLater {
                    statusLabel.text = "● MOSS Analysis Complete"
                    statusLabel.foreground = Color.GREEN
                    suggestionArea.text = """
                        📊 Analysis Results:
                        
                        1. [Warning] long_function() is 52 lines - consider splitting
                        2. [Info] Unused import: os (line 1)
                        3. [Info] Unused import: sys (line 2)
                        4. [Hint] MyClass.method_two() complexity: 8
                        
                        💡 Suggested Actions:
                        - Extract sub-function from long_function()
                        - Remove unused imports
                    """.trimIndent()
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    statusLabel.text = "● MOSS Error"
                    statusLabel.foreground = Color.RED
                }
            }
        }.start()
    }

    private fun refreshStats() {
        statusLabel.text = "● MOSS Refreshing..."
        Thread {
            try {
                Thread.sleep(200)
                SwingUtilities.invokeLater {
                    statusLabel.text = "● MOSS Ready"
                    statusLabel.foreground = Color.GREEN
                }
            } catch (_: Exception) {}
        }.start()
    }
}
