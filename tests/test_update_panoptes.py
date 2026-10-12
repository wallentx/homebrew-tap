import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('updater', Path(__file__).parents[1] / 'scripts/update-panoptes.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


class UpdateTests(unittest.TestCase):
    def formula(self, tag='v1.0.0'):
        return '\n'.join(f'      url "{u.ROOT}/{tag}/{name}"\n      sha256 "{"a" * 64}"'
                         for name in u.expected_assets(tag).values()) + '\nHEAD stays unchanged\n'

    def release(self):
        tag = 'v1.0.2'
        return {'tag_name': tag, 'draft': False, 'prerelease': False,
                'assets': [{'name': n, 'size': 1, 'state': 'uploaded', 'browser_download_url': f'{u.ROOT}/{tag}/{n}'}
                           for n in ['SHA256SUMS', *u.expected_assets(tag).values()]]}

    def archives(self, root, wrong_target=False):
        lines = []
        for target, name in u.expected_assets('v1.0.2').items():
            body = json.dumps({'version': '1.0.2', 'tag': 'v1.0.2', 'target': 'wrong' if wrong_target else target,
                               'commit': 'b' * 40}).encode()
            with tarfile.open(root / name, 'w:gz') as archive:
                info = tarfile.TarInfo(f'{name[:-7]}/release.json')
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
            lines.append(f'{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}')
        (root / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')

    def test_complete_release_updates_all_four_pairs_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.archives(root)
            sums = u.verified_checksums(root, 'v1.0.2', 'b' * 40)
            result = u.render(self.formula(), 'v1.0.2', sums)
            self.assertEqual(u.current_tag(result), 'v1.0.2')
            self.assertEqual(u.render(result, 'v1.0.2', sums), result)
            self.assertIn('HEAD stays unchanged', result)
            for target, digest in sums.items():
                self.assertIn(f'{target}.tar.gz"\n      sha256 "{digest}"', result)

    def test_missing_duplicate_or_uploading_assets_are_not_ready(self):
        r = self.release()
        self.assertTrue(u.release_ready(r, 'v1.0.2'))
        r['assets'].pop()
        self.assertFalse(u.release_ready(r, 'v1.0.2'))
        r = self.release()
        r['assets'][-1] = r['assets'][0]
        self.assertFalse(u.release_ready(r, 'v1.0.2'))
        r = self.release()
        r['assets'][0]['state'] = 'new'
        self.assertFalse(u.release_ready(r, 'v1.0.2'))

    def test_prereleases_unexpected_urls_and_downgrades_are_rejected(self):
        r = self.release()
        r['prerelease'] = True
        with self.assertRaises(ValueError):
            u.release_ready(r, 'v1.0.2')
        r = self.release()
        r['assets'][0]['browser_download_url'] = 'https://example.invalid/SHA256SUMS'
        with self.assertRaises(ValueError):
            u.release_ready(r, 'v1.0.2')
        with self.assertRaises(ValueError):
            u.render(self.formula('v1.0.3'), 'v1.0.2', {t: 'a' * 64 for t in u.TARGETS})

    def test_corrupt_archive_and_wrong_release_metadata_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.archives(root)
            name = next(iter(u.expected_assets('v1.0.2').values()))
            (root / name).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                u.verified_checksums(root, 'v1.0.2', 'b' * 40)
            self.archives(root, wrong_target=True)
            with self.assertRaisesRegex(ValueError, 'metadata target mismatch'):
                u.verified_checksums(root, 'v1.0.2', 'b' * 40)
            self.archives(root)
            with self.assertRaisesRegex(ValueError, 'metadata commit mismatch'):
                u.verified_checksums(root, 'v1.0.2', 'c' * 40)

    def test_incomplete_formula_or_checksum_manifest_is_rejected(self):
        with self.assertRaises(ValueError):
            u.current_tag(self.formula().replace('x86_64-apple-darwin', 'unknown-target'))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.archives(root)
            sums = root / 'SHA256SUMS'
            sums.write_text(sums.read_text() + sums.read_text().splitlines()[0] + '\n')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                u.verified_checksums(root, 'v1.0.2', 'b' * 40)


if __name__ == '__main__':
    unittest.main()
