package dev.withohm.jetbrains

import com.intellij.credentialStore.CredentialAttributes
import com.intellij.credentialStore.Credentials
import com.intellij.credentialStore.generateServiceName
import com.intellij.ide.passwordSafe.PasswordSafe
import com.intellij.ide.util.PropertiesComponent

/**
 * Persists withOhm settings: secrets in PasswordSafe, non-secrets in PropertiesComponent.
 */
object OhmCredentialsStore {
    const val DEFAULT_BASE_URL = "https://api.withohm.dev/v1"
    private const val PROP_ENABLED = "dev.withohm.enabled"
    private const val PROP_BASE_URL = "dev.withohm.baseUrl"
    private const val SERVICE = "withOhm"

    private fun attrs(user: String): CredentialAttributes =
        CredentialAttributes(generateServiceName(SERVICE, user))

    var enabled: Boolean
        get() = PropertiesComponent.getInstance().getBoolean(PROP_ENABLED, false)
        set(value) = PropertiesComponent.getInstance().setValue(PROP_ENABLED, value)

    var baseUrl: String
        get() {
            val v = PropertiesComponent.getInstance().getValue(PROP_BASE_URL)
            return if (v.isNullOrBlank()) DEFAULT_BASE_URL else v.trim()
        }
        set(value) {
            val trimmed = value.trim().ifBlank { DEFAULT_BASE_URL }
            PropertiesComponent.getInstance().setValue(PROP_BASE_URL, trimmed)
        }

    var apiKey: String
        get() = PasswordSafe.instance.getPassword(attrs("apiKey")).orEmpty()
        set(value) {
            val attrs = attrs("apiKey")
            if (value.isBlank()) {
                PasswordSafe.instance.set(attrs, null)
            } else {
                PasswordSafe.instance.set(attrs, Credentials("apiKey", value.trim()))
            }
        }

    var upstreamKey: String
        get() = PasswordSafe.instance.getPassword(attrs("upstreamKey")).orEmpty()
        set(value) {
            val attrs = attrs("upstreamKey")
            if (value.isBlank()) {
                PasswordSafe.instance.set(attrs, null)
            } else {
                PasswordSafe.instance.set(attrs, Credentials("upstreamKey", value.trim()))
            }
        }
}
