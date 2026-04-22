# Required release secrets

## `NPM_TOKEN`

Token with publish access to the npm package. Used by the release workflow when running `npm publish --provenance --access public`.

## `PYPI_API_TOKEN`

Optional PyPI API token for publishing if you choose token-based upload instead of GitHub trusted publishing.

If you configure trusted publishing for `pypa/gh-action-pypi-publish@release/v1`, this token is not needed.
