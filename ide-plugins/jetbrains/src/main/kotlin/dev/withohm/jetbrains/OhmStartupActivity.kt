package dev.withohm.jetbrains

import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.ProjectActivity

/**
 * Re-sync MCP config when a project opens if withOhm is enabled.
 */
class OhmStartupActivity : ProjectActivity {
    override suspend fun execute(project: Project) {
        if (!OhmCredentialsStore.enabled) return
        if (OhmCredentialsStore.apiKey.isBlank()) return
        val result = OhmMcpRegistrar.syncFromStore(removeIfDisabled = false)
        if (!result.ok) {
            OhmMcpRegistrar.notifySync(result)
        }
    }
}
