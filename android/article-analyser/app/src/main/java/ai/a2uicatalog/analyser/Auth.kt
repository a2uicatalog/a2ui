package ai.a2uicatalog.analyser

import android.content.Context
import android.content.Intent
import android.net.Uri
import kotlinx.coroutines.suspendCancellableCoroutine
import net.openid.appauth.AuthState
import net.openid.appauth.AuthorizationException
import net.openid.appauth.AuthorizationRequest
import net.openid.appauth.AuthorizationResponse
import net.openid.appauth.AuthorizationService
import net.openid.appauth.AuthorizationServiceConfiguration
import net.openid.appauth.ResponseTypeValues
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * Sign-in against the catalog's own OAuth server (mcp-worker/src/oauth.js): a public PKCE client, `a2ui-android`,
 * redirecting to ai.a2uicatalog.android:/oauth2redirect. AppAuth opens a Custom Tab, where Cloudflare Access does
 * the Google sign-in and the worker shows its consent page; PKCE (S256) is AppAuth's default, and the server
 * requires it for this client. Tokens: 1 h access, 30-day refresh, refreshed by [freshToken] when needed.
 *
 * The AuthState lives in app-private SharedPreferences: a sideloaded personal app on one phone. A Play build would
 * move it to Keystore-backed storage.
 */
object Auth {
    const val CLIENT_ID = "a2ui-android"
    private val REDIRECT = Uri.parse("ai.a2uicatalog.android:/oauth2redirect")
    private val CONFIG = AuthorizationServiceConfiguration(
        Uri.parse("https://a2uicatalog.ai/mcp-oauth/authorize"),
        Uri.parse("https://a2uicatalog.ai/mcp-oauth/token"),
    )
    private const val PREFS = "auth"
    private const val KEY = "state"

    class SignInRequired : Exception("Sign in to read articles")

    private fun load(ctx: Context): AuthState =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, null)
            ?.let { runCatching { AuthState.jsonDeserialize(it) }.getOrNull() } ?: AuthState(CONFIG)

    private fun save(ctx: Context, s: AuthState) =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY, s.jsonSerializeString()).apply()

    fun isSignedIn(ctx: Context) = load(ctx).refreshToken != null

    fun signOut(ctx: Context) = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()

    fun signInIntent(ctx: Context): Intent {
        val req = AuthorizationRequest.Builder(CONFIG, CLIENT_ID, ResponseTypeValues.CODE, REDIRECT).build()
        val service = AuthorizationService(ctx)
        return service.getAuthorizationRequestIntent(req).also { service.dispose() }
    }

    /** Finishes the redirect: swaps the code (plus the PKCE verifier AppAuth kept) for tokens. */
    suspend fun complete(ctx: Context, data: Intent?) {
        val resp = data?.let { AuthorizationResponse.fromIntent(it) }
        val err = data?.let { AuthorizationException.fromIntent(it) }
        if (resp == null) throw Exception(err?.errorDescription ?: err?.error ?: "Sign-in was cancelled")
        val state = AuthState(resp, err)
        val service = AuthorizationService(ctx)
        try {
            val tokens = suspendCancellableCoroutine { cont ->
                service.performTokenRequest(resp.createTokenExchangeRequest()) { t, e ->
                    if (t != null) cont.resume(t) else cont.resumeWithException(Exception(e?.errorDescription ?: e?.error ?: "Token exchange failed"))
                }
            }
            state.update(tokens, null)
            save(ctx, state)
        } finally {
            service.dispose()
        }
    }

    /** A valid access token, refreshing it first if it has expired. Throws [SignInRequired] when there is none. */
    suspend fun freshToken(ctx: Context): String {
        val state = load(ctx)
        if (state.refreshToken == null) throw SignInRequired()
        val service = AuthorizationService(ctx)
        try {
            return suspendCancellableCoroutine { cont ->
                state.performActionWithFreshTokens(service) { token, _, e ->
                    save(ctx, state)
                    when {
                        token != null -> cont.resume(token)
                        e?.type == AuthorizationException.TYPE_OAUTH_TOKEN_ERROR -> cont.resumeWithException(SignInRequired())
                        else -> cont.resumeWithException(java.io.IOException(e?.errorDescription ?: "Could not refresh sign-in"))
                    }
                }
            }
        } finally {
            service.dispose()
        }
    }
}
