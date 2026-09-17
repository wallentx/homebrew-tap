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

The formula installs Panoptes `v1.0.0` from its
[release assets](https://github.com/wallentx/panoptes/releases/tag/v1.0.0).
Each supported OS/architecture has a versioned archive URL and verified checksum.

## Maintain the formula

After a new stable release has uploaded all four archives and `SHA256SUMS`, update
`Formula/panoptes.rb` with the release version, four asset URLs, and their SHA-256
checksums. Download the archives and verify them against `SHA256SUMS` before
updating the formula. Keep versioned URLs so installs remain reproducible.
`brew update` picks up formula updates; `brew upgrade` installs the newer release.
Use `revision` for packaging changes that need an upgrade without changing the
upstream version.

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
