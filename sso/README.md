# Stregsystem SSO

Authenticate Members through proof-of-email via One-time password / Magic-link.

## Why?

This provides a unified login experience for our Members and Volunteers across services,
similar to how the tech giants do it (FFAANG: F-club, Facebook ... etc.).

- Enables unrestricted publicly facing services without eroding Member-trust
- Allows access to API endpoints outside whitelisted IP-ranges (AAU network)
- Looks cool, and makes Members feel something familiar

## Scopes
These allow access to various API endpoints.

- `member:balance`: The member's balance.
- `member:active`: The member's active-status.
- `member:sales`: All past sales of the member.
- `member:id`: The member's ID.
- `member:email`: The member's e-mail address.
- `member:name`: The member's first- and last name.
- `member:year`: The (university) enrollment year of the member.
- `member:gender`: The sex of the member.
- `staff`: Tests whether the user has the 'staff' attribute enabled -> whether the member is a volunteer.

## How to set up

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

### 3. Implement callback in your app

Your app is going to need a landing page to redirect to after the user authorizes the scopes.

### 4. Get API credentials

Contact fit[at]fklub.dk to register an application, then we'll provide `client_id`, `client_secret`, etc.,
and configure redirect URLs and more.

### ?. Profit ???
Now *our* users will be able to use your service, thank you!
