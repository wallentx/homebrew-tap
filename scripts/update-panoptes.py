#!/usr/bin/env python3
"""Update Panoptes only from complete, checksum-verified stable release assets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

REPO = "wallentx/panoptes"
ROOT = f"https://github.com/{REPO}/releases/download"
TARGETS = (
    "aarch64-apple-darwin", "x86_64-apple-darwin",
    "aarch64-unknown-linux-gnu", "x86_64-unknown-linux-gnu",
)
TAG = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
ENTRY = re.compile(
    rf'url "{re.escape(ROOT)}/(?P<tag>v[^/]+)/panoptes-(?P<version>[^/]+?)-'
    r'(?P<target>aarch64-apple-darwin|x86_64-apple-darwin|aarch64-unknown-linux-gnu|x86_64-unknown-linux-gnu)\.tar\.gz"'
    r'(?P<gap>\s+)sha256 "(?P<sha>[0-9a-f]{64})"'
)


def version(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f"expected a stable vMAJOR.MINOR.PATCH tag, got {tag!r}")
    return tuple(map(int, match.groups()))


def current_tag(formula):
    entries = list(ENTRY.finditer(formula))
    if len(entries) != 4 or {m['target'] for m in entries} != set(TARGETS):
        raise ValueError("formula must have exactly one URL/checksum pair per supported target")
    tags = {m['tag'] for m in entries}
    if len(tags) != 1 or any(m['version'] != m['tag'][1:] for m in entries):
        raise ValueError("formula release URLs contain inconsistent versions")
    tag = tags.pop()
    version(tag)
    return tag


def expected_assets(tag):
    version(tag)
    return {t: f"panoptes-{tag[1:]}-{t}.tar.gz" for t in TARGETS}


def release_ready(release, tag):
    if release['tag_name'] != tag or release['draft'] or release['prerelease']:
        raise ValueError("release must be published, stable, and match the requested tag")
    required = set(expected_assets(tag).values()) | {"SHA256SUMS"}
    assets = [a for a in release['assets'] if a['name'] in required]
    if len(assets) != len(required) or {a['name'] for a in assets} != required:
        return False
    for asset in assets:
        if asset['state'] != 'uploaded' or asset['size'] <= 0:
            return False
        if asset['browser_download_url'] != f"{ROOT}/{tag}/{asset['name']}":
            raise ValueError("unexpected release asset download URL")
    return True


def verified_checksums(directory, tag, commit):
    sums = {}
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64}) [ *]([^/\\]+)', line)
        if not match or match[2] in sums:
            raise ValueError("malformed or duplicate SHA256SUMS entry")
        sums[match[2]] = match[1].lower()
    expected = expected_assets(tag)
    if set(sums) != set(expected.values()):
        raise ValueError("SHA256SUMS must cover exactly the four supported archives")
    result = {}
    for target, name in expected.items():
        archive = directory / name
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != sums[name]:
            raise ValueError(f"checksum mismatch: {name}")
        with tarfile.open(archive, 'r:gz') as tar:
            member = tar.getmember(f"{name[:-7]}/release.json")
            if not member.isfile() or member.size > 65536:
                raise ValueError(f"invalid release metadata entry: {name}")
            with tar.extractfile(member) as stream:
                metadata = json.load(stream)
        for key, value in {'tag': tag, 'version': tag[1:], 'target': target, 'commit': commit}.items():
            if metadata.get(key) != value:
                raise ValueError(f"release metadata {key} mismatch: {name}")
        result[target] = digest
    return result


def render(formula, tag, checksums):
    old = current_tag(formula)
    if version(tag) < version(old):
        raise ValueError("refusing to downgrade the formula")
    if set(checksums) != set(TARGETS) or any(not re.fullmatch(r'[0-9a-f]{64}', s) for s in checksums.values()):
        raise ValueError("invalid target checksum set")
    return ENTRY.sub(lambda m: f'url "{ROOT}/{tag}/{expected_assets(tag)[m["target"]]}"'
                     f'{m["gap"]}sha256 "{checksums[m["target"]]}"', formula)


def output(changed, tag, message):
    print(message)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            stream.write(f"changed={str(changed).lower()}\nversion={tag}\n")


def gh_json(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint], text=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='', help='stable tag; default: latest published release')
    parser.add_argument('--formula', type=Path, default=Path('Formula/panoptes.rb'))
    args = parser.parse_args()
    original = args.formula.read_text()
    old = current_tag(original)
    if args.version:
        version(args.version)
    endpoint = f'repos/{REPO}/releases/' + (f'tags/{args.version}' if args.version else 'latest')
    release = gh_json(endpoint)
    tag = release['tag_name']
    version(tag)
    if args.version and tag != args.version:
        raise ValueError('release tag differs from the requested version')
    if release['draft'] or release['prerelease']:
        raise ValueError('refusing unpublished or prerelease assets')
    if version(tag) <= version(old):
        output(False, tag, f'No update: formula {old}, release {tag}')
        return
    if not release_ready(release, tag):
        if args.version:
            raise ValueError(f'{tag} does not yet have all four archives and SHA256SUMS')
        output(False, tag, f'Waiting for complete {tag} release assets; formula remains {old}')
        return
    commit = gh_json(f'repos/{REPO}/commits/{tag}')['sha']
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        raise ValueError('invalid release commit')
    with tempfile.TemporaryDirectory(prefix='panoptes-tap-', dir=os.environ.get('TMPDIR')) as temp:
        directory = Path(temp)
        command = ['gh', 'release', 'download', tag, '--repo', REPO, '--dir', str(directory)]
        for name in ['SHA256SUMS', *expected_assets(tag).values()]:
            command.extend(['--pattern', name])
        subprocess.run(command, check=True)
        updated = render(original, tag, verified_checksums(directory, tag, commit))
    # Do not discard an edit made while archives were downloading.
    if args.formula.read_text() != original:
        raise ValueError('formula changed during verification; retry')
    args.formula.write_text(updated)
    output(updated != original, tag, f'Updated {old} -> {tag}; all four archives and release metadata verified')


if __name__ == '__main__':
    main()
