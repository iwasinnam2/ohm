package dev.withohm.jetbrains

import com.intellij.openapi.ui.Messages
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPasswordField
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.FormBuilder
import com.intellij.util.ui.JBUI
import java.awt.BorderLayout
import javax.swing.JButton
import javax.swing.JComponent
import javax.swing.JPanel

/**
 * Settings → Tools → withOhm
 */
class OhmSettingsConfigurable : com.intellij.openapi.options.Configurable {
    private var panel: JPanel? = null
    private val enabledCheck = JBCheckBox("Enable withOhm MCP for AI Assistant")
    private val apiKeyField = JBPasswordField()
    private val upstreamKeyField = JBPasswordField()
    private val baseUrlField = JBTextField()
    private val statusLabel = JBLabel()

    override fun getDisplayName(): String = "withOhm"

    override fun createComponent(): JComponent {
        apiKeyField.columns = 40
        upstreamKeyField.columns = 40
        baseUrlField.columns = 40

        val applyButton = JButton("Apply to AI Assistant").apply {
            addActionListener {
                applyFromUi()
                val result = OhmMcpRegistrar.syncFromStore()
                OhmMcpRegistrar.notifySync(result)
                updateStatus(result)
            }
        }

        val copyButton = JButton("Copy MCP JSON").apply {
            addActionListener {
                applyFromUi()
                val json = OhmMcpRegistrar.buildSnippet()
                com.intellij.openapi.ide.CopyPasteManager.getInstance()
                    .setContents(java.awt.datatransfer.StringSelection(json))
                Messages.showInfoMessage(
                    "MCP JSON copied. Paste under Settings → Tools → AI Assistant → Model Context Protocol if auto-sync fails.",
                    "withOhm",
                )
            }
        }

        val buttons = JPanel().apply {
            add(applyButton)
            add(copyButton)
        }

        statusLabel.border = JBUI.Borders.emptyTop(8)

        val form = FormBuilder.createFormBuilder()
            .addComponent(enabledCheck)
            .addLabeledComponent("Ohm API key (sk-at-…)", apiKeyField, 1, false)
            .addLabeledComponent("Upstream BYOK key (optional)", upstreamKeyField, 1, false)
            .addLabeledComponent("Base URL", baseUrlField, 1, false)
            .addComponent(JBLabel("Requires pip install withohm-mcp (ohm-mcp on PATH)."))
            .addComponent(buttons)
            .addComponent(statusLabel)
            .addComponentFillVertically(JPanel(), 0)
            .panel

        panel = JPanel(BorderLayout()).apply {
            border = JBUI.Borders.empty(10)
            add(form, BorderLayout.NORTH)
        }
        reset()
        return panel!!
    }

    private fun updateStatus(result: OhmMcpRegistrar.SyncResult) {
        val ai = if (OhmMcpRegistrar.isAiAssistantInstalled()) {
            "AI Assistant plugin detected."
        } else {
            "AI Assistant plugin not detected — install/enable it, or paste MCP JSON manually."
        }
        statusLabel.text = "<html>${result.message}<br/>$ai</html>"
    }

    private fun applyFromUi() {
        OhmCredentialsStore.enabled = enabledCheck.isSelected
        OhmCredentialsStore.apiKey = String(apiKeyField.password)
        OhmCredentialsStore.upstreamKey = String(upstreamKeyField.password)
        OhmCredentialsStore.baseUrl = baseUrlField.text.trim()
            .ifBlank { OhmCredentialsStore.DEFAULT_BASE_URL }
    }

    override fun isModified(): Boolean {
        val api = String(apiKeyField.password)
        val upstream = String(upstreamKeyField.password)
        return enabledCheck.isSelected != OhmCredentialsStore.enabled ||
            api != OhmCredentialsStore.apiKey ||
            upstream != OhmCredentialsStore.upstreamKey ||
            baseUrlField.text.trim() != OhmCredentialsStore.baseUrl
    }

    override fun apply() {
        applyFromUi()
        val result = OhmMcpRegistrar.syncFromStore()
        OhmMcpRegistrar.notifySync(result)
        updateStatus(result)
    }

    override fun reset() {
        enabledCheck.isSelected = OhmCredentialsStore.enabled
        apiKeyField.text = OhmCredentialsStore.apiKey
        upstreamKeyField.text = OhmCredentialsStore.upstreamKey
        baseUrlField.text = OhmCredentialsStore.baseUrl
        statusLabel.text = if (OhmMcpRegistrar.isAiAssistantInstalled()) {
            "AI Assistant plugin detected."
        } else {
            "AI Assistant plugin not detected."
        }
    }

    override fun disposeUIResources() {
        panel = null
    }
}
