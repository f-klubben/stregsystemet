# Stregsystem SSO

Authenticate Members through proof-of-email via One-time password / Magic-link.

## Why?

This provides a unified login experience for our Members and Volunteers across services,
similar to how the tech giants do it (FFAANG: F-club, Facebook ... etc.).

- Enables unrestricted publicly facing services without eroding Member-trust
- Allows access to API endpoints outside whitelisted IP-ranges (AAU network)
- Looks cool, and makes Members feel something familiar

## Scopes
Scopes limit what a client may do. They are permissions requested by the
client, not claims returned in the ID token. Every API scope must be enforced
by its corresponding endpoint before that endpoint is considered protected.

- `openid`: Required for OpenID Connect (ID token / userinfo).
- `groups`: Adds a `groups` claim listing the names of the member's groups.
- `member:balance`: Access to the member balance endpoint.
- `member:active`: Access to the member active-status endpoint.
- `member:sales`: Access to the member sales endpoint.
- `member:id`: Access to the member ID endpoint.
- `member:email`: Access to the member e-mail endpoint.
- `member:name`: Access to the member name endpoint.
- `member:year`: Access to the member enrollment-year endpoint.
- `member:gender`: Access to the member gender endpoint.

At present, only the `openid` and `groups` OIDC behavior is implemented. The
`member:*` scopes are reserved for the corresponding APIs and must not be
presented as protecting those APIs until token and scope checks are added.

## How to set up

In production, set `ISS_ENDPOINT` in the `[oidc]` section of `local.cfg` to the
public HTTPS origin, for example `https://stregsystem.fklub.dk`. Provide the
signing key in `OIDC_RSA_PRIVATE_KEY`. For local development, `oidc.key` in the
project root is used when the key environment variable is absent. Generate it
with `python manage.py generatekey`. Without a key, the project still
runs, but its OpenID Connect endpoints are disabled.

### 1. Figure out grant type (authorization flow) for your need

More info on grant types: https://oauth.net/2/grant-types/

**Authorization code** - public vs. confidential app: Public = You cannot hide source code (e.g. API-keys).
For public PKCE is necessary.

**Client credentials**: Used for machine-to-machine interaction, typically not concerning users.
These are traditional API-keys as you know them, they are granted directly by us, and are not granted by users.
Not related to SSO.

If you decide on authorization code or device authorization, then this guide is still for you.

### 2. Insert SSO button in your app
If you're using something other than HTML/CSS, then you'll need to recreate the buttons manually.

Put SSO buttons (html and stylesheet) in your application. Located at `misc/sso-buttons/buttons.html`.
Both example buttons start the same `openid groups` flow. The second button is
only an alternative label for sites that present a volunteer/admin entry point;
the service must decide access from the returned `groups` claim. It does not
request extra privileges. Sites without such an entry point should use only the
first button.

### 3. Implement callback in your app

Your app is going to need a landing page to redirect to after the user authorizes the scopes.

### 4. Get API credentials

Contact fit[at]fklub.dk to register an application, then we'll provide `client_id`, `client_secret`, etc.,
and configure redirect URLs and more.

### ?. Profit ???
Now *our* users will be able to use your service, thank you!
