plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "2.1.20"
    id("org.jetbrains.intellij.platform") version "2.6.0"
}

group = providers.gradleProperty("group").get()
version = providers.gradleProperty("version").get()

kotlin {
    jvmToolchain(21)
}

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    intellijPlatform {
        val type = providers.gradleProperty("platformType")
        val ver = providers.gradleProperty("platformVersion")
        create(type, ver)
    }
}

intellijPlatform {
    pluginConfiguration {
        id = providers.gradleProperty("pluginId")
        name = providers.gradleProperty("pluginName")
        version = providers.gradleProperty("version")

        ideaVersion {
            sinceBuild = providers.gradleProperty("pluginSinceBuild")
            // No untilBuild — compatible with current and future 251+ builds.
        }

        description.set(
            """
            withOhm — thin MCP bridge for JetBrains AI Assistant.
            Stores your Ohm API key and registers the <code>ohm-mcp</code> stdio
            server so AI Assistant can call the same eight pipe tools as Cursor
            (chat replay, compliant web fetch, usage, savings, models, and more).
            Requires <code>pip install withohm-mcp</code> and AI Assistant (2025.1+).
            """.trimIndent(),
        )

        changeNotes.set(
            """
            <ul>
              <li>Initial release: Settings → Tools → withOhm</li>
              <li>Registers <code>ohm</code> stdio MCP server for AI Assistant</li>
              <li>Stores API keys in the IDE PasswordSafe</li>
            </ul>
            """.trimIndent(),
        )

        vendor {
            name = "Ohm"
            email = "partners@withohm.dev"
            url = "https://www.withohm.dev"
        }
    }
}

tasks {
    wrapper {
        gradleVersion = "9.5.0"
    }
}
