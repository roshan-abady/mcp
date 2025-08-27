# Snowflake Key Setup - DEPRECATED

> [!IMPORTANT]
> **Key pair authentication is no longer supported.**

This MCP server now only supports `externalbrowser` authentication for security reasons. Private key authentication has been disabled to ensure secure, interactive authentication through your web browser.

## Use External Browser Authentication Instead

The server now enforces the use of external browser authentication which provides:

- Secure authentication without storing credentials
- Support for SSO and identity providers (Okta, AD FS, SAML 2.0)
- Multi-factor authentication through your IdP
- Better security compliance

## Setup

1. Set `SNOWFLAKE_AUTHENTICATOR=externalbrowser` in your environment
2. Remove any private key configuration
3. Ensure your Snowflake account is configured for external browser authentication
4. Use your web browser for authentication when prompted

For more information, see the main README.md file.
