<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-24 | release runbook -->
# Releasing the Recall client SDKs

Tag-driven, GitHub Actions-driven, no local secrets required after one-time setup.

## One-time setup

### PyPI

1. Create a PyPI account if you don't have one: <https://pypi.org/account/register/>.
2. Reserve the project name once by manually uploading the first build, OR set up
   a [pending publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
   for `RecallWorks/Recall` with workflow file `release-python-sdk.yml` and
   environment (none).
3. Generate a project-scoped API token at <https://pypi.org/manage/account/token/>
   (scope = `Project: recall-client`).
4. Add it as a GitHub repo secret named `PYPI_API_TOKEN`:
   <https://github.com/RecallWorks/Recall/settings/secrets/actions/new>.

### npm

1. Sign in / create the `recallworks` org at <https://www.npmjs.com/org/create>.
2. Generate an automation token: <https://www.npmjs.com/settings/{user}/tokens/granular-access-tokens/new>
   - Type: **Granular Access Token**
   - Permissions: `Read and write` on packages of `@recallworks` scope
   - Expiration: 90 days (rotate via this same procedure)
3. Add it as repo secret `NPM_TOKEN`.

## Cutting a release

### Python SDK

```pwsh
cd C:\Dev\Recall\clients\python
# bump version in pyproject.toml first, then:
git add pyproject.toml
git commit -m "chore(python-sdk): bump to 0.1.1"
git tag python-sdk-v0.1.1
git push && git push --tags
```

The `release-python-sdk.yml` workflow will:
1. Verify the tag suffix matches `pyproject.toml` version.
2. Build sdist + wheel.
3. Publish to PyPI using `PYPI_API_TOKEN`.

### TypeScript SDK

```pwsh
cd C:\Dev\Recall\clients\typescript
# bump version in package.json first, then:
git add package.json
git commit -m "chore(ts-sdk): bump to 0.1.1"
git tag ts-sdk-v0.1.1
git push && git push --tags
```

The `release-ts-sdk.yml` workflow will typecheck, test, build, and `npm publish --provenance`.

## Verification

- PyPI: <https://pypi.org/project/recall-client/>
- npm: <https://www.npmjs.com/package/@recallworks/recall-client>
- Both should show the new version within ~60 seconds of the workflow finishing.

## Rollback

- **PyPI** does NOT allow re-uploading the same version. To "yank":
  `pip` will skip yanked versions; do it from the project admin page.
- **npm**: `npm unpublish @recallworks/recall-client@0.1.1` works for ~72 hours
  after publish; otherwise issue a patch release with the fix.
