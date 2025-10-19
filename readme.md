# Youtbe App-level OAuth credentials (for trancript service)
## Refresh access token
- execute script /utils/get_youtube_refresh_token.py
- authorize (in web URL) the app video2text to act on behalf of the desired user (in this case is a development user: just...@....com)
- copy refresh token from the console
- update YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN in file .env (for dev environment)
- update YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN in Github Environment Secrers (production)
- Note: how it actually works is that the app video2text is asking the user (in this case is a development user: just...@....com) to grant access to see, edit, and permanently delete your YouTube videos, ratings, comments and captions. Also by using this user just... the app is able to retrieve videos from the channels.
