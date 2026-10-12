# wallentx Homebrew tap

Install [Panoptes](https://github.com/wallentx/panoptes) on macOS or Linux:

```sh
brew install wallentx/tap/panoptes
```

Homebrew automatically adds this tap and installs the matching upstream release
binary for Apple Silicon or Intel macOS, or ARM64 or x86-64 Linux. Stable installs
verify the archive's SHA-256 checksum and include Bash, Zsh, and Fish completions;
Rust and Cargo are not required.

To build the development version from source instead:

```sh
brew install --HEAD wallentx/tap/panoptes
```

Configure your coding agent after installation:

```sh
panoptes init --provider cursor --provider opencode
```

Other providers include `claude`, `codex`, `gemini`, `antigravity`, and `copilot`.
Run `panoptes init` to open the provider picker.

## Upgrade

```sh
brew update
brew upgrade wallentx/tap/panoptes
```

After upgrading, rerun `panoptes init` for your providers and restart their MCP
clients. Existing clients may still be running the previous executable.

## Packaged release

The [formula](Formula/panoptes.rb) tracks stable Panoptes releases with complete
[release assets](https://github.com/wallentx/panoptes/releases).
Each supported OS/architecture has a versioned archive URL and verified checksum.

## Maintain the formula

The `Update Panoptes formula` workflow checks the latest stable release every
15 minutes on the default `wallentx/tap` branch. GitHub can delay scheduled runs.
It uses this repository's `GITHUB_TOKEN`; no personal or cross-repository token
is needed for scheduled updates. Partial uploads are retried on a later run.

Before changing the formula, the updater downloads all four archives, verifies
`SHA256SUMS`, and checks each embedded `release.json` against the release tag,
version, platform, and tag commit. It refuses downgrades and leaves the formula
unchanged if verification fails. After pushing a formula update it explicitly
dispatches the install/test workflow, because pushes made with `GITHUB_TOKEN`
do not trigger ordinary push workflows.

To request an update immediately:

```sh
gh workflow run update-panoptes.yml --repo wallentx/homebrew-tap --ref wallentx/tap -f version=v1.0.2
```

The Panoptes release workflow can also dispatch this updater immediately after
publishing assets when its optional `HOMEBREW_TAP_TOKEN` secret is configured.
That token only needs Actions write access to this tap; without it, scheduled
updates remain automatic. Pre-releases are not promoted into the stable formula.

For a local, verified manual edit (requires Python 3.11+ and authenticated `gh`):

```sh
python3 scripts/update-panoptes.py --version v1.0.2
```

Review and commit the resulting formula diff. `brew update` picks up formula
updates; `brew upgrade` installs the newer release. Use `revision` for packaging
changes that need an upgrade without changing the upstream version.

On a machine with Homebrew:

```sh
brew style wallentx/tap/panoptes
brew install wallentx/tap/panoptes
brew audit --strict wallentx/tap/panoptes
brew test wallentx/tap/panoptes
```

GitHub Actions runs these checks on ARM64 and x86-64 macOS and Linux for every
push and pull request. The formula test indexes a small TypeScript repository
and verifies search results and index freshness.
