package dev.withohm.jetbrains

import com.google.gson.GsonBuilder
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.intellij.ide.plugins.PluginManagerCore
import com.intellij.notification.NotificationGroupManager
import com.intellij.notification.NotificationType
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.application.PathManager
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.extensions.PluginId
import com.intellij.openapi.ide.CopyPasteManager
import java.awt.datatransfer.StringSelection
import java.nio.file.Path
import kotlin.io.path.createDirectories
import kotlin.io.path.exists
import kotlin.io.path.readText
import kotlin.io.path.writeText

/**
 * Merges the `ohm` stdio MCP server into JetBrains AI Assistant's mcp.json.
 */
object OhmMcpRegistrar {
    private val log = Logger.getInstance(OhmMcpRegistrar::class.java)
    private val gson = GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create()

    const val SERVER_NAME = "ohm"
    const val AI_ASSISTANT_PLUGIN_ID = "com.intellij.ml.llm"
    private const val NOTIFICATION_GROUP = "withOhm"

    data class SyncResult(
        val ok: Boolean,
        val path: Path?,
        val message: String,
        val jsonForPaste: String,
    )

    fun isAiAssistantInstalled(): Boolean =
        PluginManagerCore.getPlugin(PluginId.getId(AI_ASSISTANT_PLUGIN_ID)) != null

    fun buildOhmServerJson(
        apiKey: String,
        upstreamKey: String,
        baseUrl: String,
    ): JsonObject {
        val env = JsonObject()
        env.addProperty("OHM_API_KEY", apiKey)
        if (upstreamKey.isNotBlank()) {
            env.addProperty("OHM_UPSTREAM_KEY", upstreamKey)
        }
        if (baseUrl.isNotBlank()) {
            env.addProperty("OHM_BASE_URL", baseUrl)
        }
        return JsonObject().apply {
            addProperty("command", "ohm-mcp")
            add("env", env)
        }
    }

    fun buildSnippet(
        apiKey: String = OhmCredentialsStore.apiKey,
        upstreamKey: String = OhmCredentialsStore.upstreamKey,
        baseUrl: String = OhmCredentialsStore.baseUrl,
    ): String {
        val root = JsonObject()
        val servers = JsonObject()
        servers.add(SERVER_NAME, buildOhmServerJson(apiKey, upstreamKey, baseUrl))
        root.add("mcpServers", servers)
        return gson.toJson(root)
    }

    /** Candidate paths used by AI Assistant across OS / IDE layouts. */
    fun candidateMcpPaths(): List<Path> {
        val home = Path.of(System.getProperty("user.home"))
        val os = System.getProperty("os.name").orEmpty().lowercase()
        val paths = mutableListOf<Path>()

        when {
            os.contains("mac") || os.contains("darwin") -> {
                paths.add(home.resolve("Library/Application Support/JetBrains/AIAssistant/mcp.json"))
            }
            os.contains("win") -> {
                val appData = System.getenv("APPDATA")
                if (!appData.isNullOrBlank()) {
                    paths.add(Path.of(appData, "JetBrains", "AIAssistant", "mcp.json"))
                }
            }
            else -> {
                paths.add(home.resolve(".config/JetBrains/AIAssistant/mcp.json"))
            }
        }

        // IDE config dir sibling (some builds keep MCP next to the product config).
        val configPath = Path.of(PathManager.getConfigPath())
        paths.add(configPath.resolve("AIAssistant/mcp.json"))
        paths.add(configPath.resolve("mcp.json"))
        configPath.parent?.resolve("AIAssistant/mcp.json")?.let { paths.add(it) }

        return paths.distinct()
    }

    fun resolveWritePath(): Path {
        val existing = candidateMcpPaths().firstOrNull { it.exists() }
        if (existing != null) return existing
        // Prefer the documented AI Assistant path for this OS.
        return candidateMcpPaths().first()
    }

    fun syncFromStore(removeIfDisabled: Boolean = true): SyncResult {
        val snippet = buildSnippet()
        if (!OhmCredentialsStore.enabled) {
            if (removeIfDisabled) {
                return removeOhmEntry(snippet)
            }
            return SyncResult(
                ok = true,
                path = null,
                message = "withOhm MCP sync skipped (disabled in Settings).",
                jsonForPaste = snippet,
            )
        }

        val apiKey = OhmCredentialsStore.apiKey
        if (apiKey.isBlank()) {
            return SyncResult(
                ok = false,
                path = null,
                message = "Set your Ohm API key (sk-at-…) in Settings → Tools → withOhm.",
                jsonForPaste = snippet,
            )
        }

        return writeOhmEntry(
            OhmCredentialsStore.apiKey,
            OhmCredentialsStore.upstreamKey,
            OhmCredentialsStore.baseUrl,
            snippet,
        )
    }

    private fun writeOhmEntry(
        apiKey: String,
        upstreamKey: String,
        baseUrl: String,
        snippet: String,
    ): SyncResult {
        val path = resolveWritePath()
        return try {
            path.parent?.createDirectories()
            val root = if (path.exists()) {
                parseRoot(path.readText())
            } else {
                JsonObject()
            }
            val servers = root.getAsJsonObject("mcpServers")
                ?: JsonObject().also { root.add("mcpServers", it) }
            servers.add(SERVER_NAME, buildOhmServerJson(apiKey, upstreamKey, baseUrl))
            path.writeText(gson.toJson(root) + "\n")
            SyncResult(
                ok = true,
                path = path,
                message = "Registered MCP server \"$SERVER_NAME\" in ${path}.",
                jsonForPaste = snippet,
            )
        } catch (e: Exception) {
            log.warn("Failed to write withOhm MCP config at $path", e)
            SyncResult(
                ok = false,
                path = path,
                message = "Could not write ${path}: ${e.message}. Paste the JSON under Settings → Tools → AI Assistant → Model Context Protocol.",
                jsonForPaste = snippet,
            )
        }
    }

    private fun removeOhmEntry(snippet: String): SyncResult {
        val path = candidateMcpPaths().firstOrNull { it.exists() }
            ?: return SyncResult(
                ok = true,
                path = null,
                message = "withOhm MCP disabled; no mcp.json to update.",
                jsonForPaste = snippet,
            )
        return try {
            val root = parseRoot(path.readText())
            val servers = root.getAsJsonObject("mcpServers")
            if (servers != null && servers.has(SERVER_NAME)) {
                servers.remove(SERVER_NAME)
                path.writeText(gson.toJson(root) + "\n")
            }
            SyncResult(
                ok = true,
                path = path,
                message = "Removed MCP server \"$SERVER_NAME\" from ${path}.",
                jsonForPaste = snippet,
            )
        } catch (e: Exception) {
            log.warn("Failed to remove withOhm MCP entry at $path", e)
            SyncResult(
                ok = false,
                path = path,
                message = "Could not update ${path}: ${e.message}",
                jsonForPaste = snippet,
            )
        }
    }

    private fun parseRoot(text: String): JsonObject {
        if (text.isBlank()) return JsonObject()
        val el = JsonParser.parseString(text)
        return if (el.isJsonObject) el.asJsonObject else JsonObject()
    }

    fun notifySync(result: SyncResult) {
        ApplicationManager.getApplication().invokeLater {
            val type = if (result.ok) NotificationType.INFORMATION else NotificationType.WARNING
            val body = buildString {
                append(result.message)
                if (!isAiAssistantInstalled()) {
                    append(" AI Assistant plugin not detected — install/enable it, or paste MCP JSON manually.")
                }
            }
            val notification = NotificationGroupManager.getInstance()
                .getNotificationGroup(NOTIFICATION_GROUP)
                .createNotification("withOhm", body, type)

            notification.addAction(
                object : com.intellij.openapi.actionSystem.AnAction("Copy MCP JSON") {
                    override fun actionPerformed(e: com.intellij.openapi.actionSystem.AnActionEvent) {
                        CopyPasteManager.getInstance()
                            .setContents(StringSelection(result.jsonForPaste))
                    }
                },
            )

            notification.notify(null)
        }
    }
}
