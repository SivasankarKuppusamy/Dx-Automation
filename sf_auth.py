# sf_auth.py
# Salesforce OAuth 2.0 authentication helpers

import logging
import requests

logger = logging.getLogger(__name__)


def _token_url(instance_url: str) -> str:
    """Return the OAuth token endpoint for sandbox or production."""
    is_sandbox = '.sandbox.' in instance_url or '--' in instance_url
    return (
        'https://test.salesforce.com/services/oauth2/token'
        if is_sandbox
        else 'https://login.salesforce.com/services/oauth2/token'
    )


from credentials import ENVIRONMENTS


def get_access_token(env_key: str):
    """
    Look up credentials for env_key from credentials.py and authenticate.

    Returns:
        (access_token, instance_url) tuple on success.

    Raises:
        RuntimeError with the Salesforce error detail on failure.
    """
    env = ENVIRONMENTS.get(env_key)
    if not env:
        raise RuntimeError(f"No credentials configured for environment '{env_key}' in credentials.py.")

    client_id      = env.get('client_id', '')
    client_secret  = env.get('client_secret', '')
    instance_url   = env['instance_url']
    username       = env.get('username', '')
    password       = env.get('password', '')
    security_token = env.get('security_token', '')

    if not client_id or not client_secret:
        raise RuntimeError(f"client_id and client_secret must not be empty for '{env_key}'.")
    if not username or not password:
        raise RuntimeError(f"username and password must not be empty for '{env_key}'.")

    token_url = _token_url(instance_url)
    logger.debug("POST %s", token_url)

    resp = requests.post(
        token_url,
        data={
            'grant_type':   'password',
            'client_id':    client_id,
            'client_secret': client_secret,
            'username':     username,
            'password':     password + security_token,
        },
        timeout=30,
    )

    logger.debug("Response %s: %s", resp.status_code, resp.text)

    if resp.status_code == 200:
        result = resp.json()
        logger.info("✅ Authenticated — instance: %s", result.get('instance_url', instance_url))
        return result['access_token'], result.get('instance_url', instance_url)

    try:
        err = resp.json()
        detail = f"{err.get('error')}: {err.get('error_description', err)}"
    except Exception:
        detail = resp.text
    raise RuntimeError(f"Salesforce auth failed [{resp.status_code}] {detail}")


def main():
    import os
    env_key = os.environ.get('SF_ENV', 'tecq')
    token, instance_url = get_access_token(env_key)
    print(f"✅ Access token: {token[:20]}...")
    print(f"✅ Instance URL: {instance_url}")
if __name__ == "__main__":
    main()
