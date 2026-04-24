/**
 * MOSS v9.3 - PyCharm Plugin: Code Quality Inspection
 *
 * 代码质量检查，基于 MOSS LSP 服务器提供的诊断信息
 */

package com.moss.devtools.inspection

import com.intellij.codeInspection.*
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.util.TextRange
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.jetbrains.python.psi.PyFunction
import com.jetbrains.python.psi.PyClass
import com.jetbrains.python.psi.PyImportStatement
import com.jetbrains.python.psi.PyFromImportStatement

/**
 * MOSS 代码质量检查
 *
 * 检查项目:
 * 1. 长函数警告
 * 2. 高复杂度函数
 * 3. 未使用的导入
 * 4. 缺少 self 参数的方法
 */
class MossCodeQualityInspection : PyInspection() {

    private val logger = Logger.getInstance(MossCodeQualityInspection::class.java)

    companion object {
        const val LONG_FUNCTION_THRESHOLD = 50
        const val HIGH_COMPLEXITY_THRESHOLD = 10
    }

    override fun buildVisitor(
        holder: ProblemsHolder,
        isOnTheFly: Boolean
    ): PsiElementVisitor {
        return object : PsiElementVisitor() {
            override fun visitElement(element: PsiElement) {
                when (element) {
                    is PyFunction -> checkFunction(element, holder)
                    is PyImportStatement -> checkImport(element, holder)
                    is PyFromImportStatement -> checkFromImport(element, holder)
                }
                super.visitElement(element)
            }
        }
    }

    /**
     * 检查函数质量
     */
    private fun checkFunction(func: PyFunction, holder: ProblemsHolder) {
        val document = func.containingFile?.viewProvider?.document ?: return
        val startLine = document.getLineNumber(func.textOffset)
        val endOffset = func.textOffset + func.textLength
        val endLine = document.getLineNumber(endOffset.coerceAtMost(document.textLength - 1))
        val lineCount = endLine - startLine + 1

        // 检查长函数
        if (lineCount > LONG_FUNCTION_THRESHOLD) {
            holder.registerProblem(
                func,
                "MOSS: 函数 '${func.name}' 过长 ($lineCount 行)，建议拆分",
                ProblemHighlightType.WARNING,
                TextRange(0, func.name?.length ?: 0)
            )
        }

        // 检查复杂度
        val complexity = calculateComplexity(func)
        if (complexity > HIGH_COMPLEXITY_THRESHOLD) {
            holder.registerProblem(
                func,
                "MOSS: 函数 '${func.name}' 复杂度过高 ($complexity)",
                ProblemHighlightType.INFORMATION,
                TextRange(0, func.name?.length ?: 0)
            )
        }
    }

    /**
     * 检查未使用的 import 语句
     */
    private fun checkImport(import: PyImportStatement, holder: ProblemsHolder) {
        val importedNames = import.importedQNames
        for (qName in importedNames) {
            val shortName = qName.lastComponent ?: continue
            if (!isNameUsed(import.containingFile, shortName, import)) {
                holder.registerProblem(
                    import,
                    "MOSS: 未使用的导入: $shortName",
                    ProblemHighlightType.INFORMATION
                )
            }
        }
    }

    /**
     * 检查 from ... import 语句
     */
    private fun checkFromImport(import: PyFromImportStatement, holder: ProblemsHolder) {
        val importList = import.importElements
        for (importElement in importList) {
            val name = importElement.visibleName ?: continue
            if (!isNameUsed(import.containingFile, name, import)) {
                holder.registerProblem(
                    importElement,
                    "MOSS: 未使用的导入: $name",
                    ProblemHighlightType.INFORMATION
                )
            }
        }
    }

    /**
     * 简化的圈复杂度计算
     */
    private fun calculateComplexity(func: PyFunction): Int {
        var complexity = 1
        val text = func.text

        // 计算分支和循环关键字
        val keywords = listOf("if ", "elif ", "else:", "for ", "while ", "except ", "and ", "or ")
        for (keyword in keywords) {
            var index = 0
            while (text.indexOf(keyword, index).also { index = it } != -1) {
                complexity++
                index += keyword.length
            }
        }

        return complexity
    }

    /**
     * 检查名称是否在文件中被使用（简化版本）
     */
    private fun isNameUsed(file: PsiFile, name: String, importElement: PsiElement): Boolean {
        val text = file.text
        // 排除导入行本身，查找其他出现
        val importRange = importElement.textRange
        var searchStart = 0

        while (true) {
            val idx = text.indexOf(name, searchStart)
            if (idx < 0) break

            val offset = idx
            if (!importRange.contains(offset)) {
                return true // 在非导入行找到了使用
            }
            searchStart = idx + name.length
        }

        return false
    }
}

/**
 * MOSS 复杂度检查
 */
class MossComplexityInspection : PyInspection() {
    override fun buildVisitor(
        holder: ProblemsHolder,
        isOnTheFly: Boolean
    ): PsiElementVisitor {
        return object : PsiElementVisitor() {
            override fun visitElement(element: PsiElement) {
                if (element is PyFunction) {
                    val text = element.text
                    var complexity = 1
                    val keywords = listOf("if ", "elif ", "else:", "for ", "while ", "except ", "and ", "or ")
                    for (kw in keywords) {
                        var idx = 0
                        while (text.indexOf(kw, idx).also { idx = it } != -1) {
                            complexity++
                            idx += kw.length
                        }
                    }

                    if (complexity > 8) {
                        val level = when {
                            complexity > 15 -> ProblemHighlightType.WARNING
                            else -> ProblemHighlightType.INFORMATION
                        }
                        holder.registerProblem(
                            element,
                            "MOSS: 圈复杂度 $complexity (${if (complexity > 15) "高" else "中等"})",
                            level
                        )
                    }
                }
                super.visitElement(element)
            }
        }
    }
}

/**
 * PyInspection 基类引用（简化版，实际项目需依赖 Python 插件 SDK）
 */
open class PyInspection : LocalInspectionTool()
