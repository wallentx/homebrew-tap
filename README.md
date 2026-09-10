# wallentx Homebrew tap

Install [Panoptes](https://github.com/wallentx/panoptes) on macOS or Linux:

```sh
brew install wallentx/tap/panoptes
```

Homebrew automatically adds this tap and builds Panoptes from source using Rust.
Prebuilt Homebrew bottles are not published yet.

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

## Packaged source

The initial `0.1.0` formula pins Panoptes commit
`1c0052b5d12a624a53c6d756cff021166bb7833d` with a verified SHA-256 checksum.
Panoptes has no release tags yet; this is a source snapshot, not an upstream
tagged release.

## Maintain the formula

When publishing a new Panoptes version, update `Formula/panoptes.rb` with its
source archive URL, version, checksum, and build commit. For a tagged archive,
Homebrew can infer the version from the tag URL, so remove the explicit `version`
line. Use `revision` for packaging changes that need an upgrade without changing
the upstream version.

On a machine with Homebrew:

```sh
brew style wallentx/tap/panoptes
brew install --build-from-source wallentx/tap/panoptes
brew audit --strict wallentx/tap/panoptes
brew test wallentx/tap/panoptes
```

GitHub Actions runs these checks on macOS and Linux for every push and pull
request. The formula test indexes a small TypeScript repository and verifies
search results and index freshness.
