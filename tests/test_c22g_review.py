"""New review packaging privacy/byte checks, no live model calls."""
import json
import zipfile
import pytest
from scripts import c22g_review as r

def test_review_manifest_preserves_raw_json_and_citations(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'OUT',tmp_path)
    raw=b'{"citations":[{"ref":"source","value":123}],"note":"original bytes"}\n'
    receipt=r.seal('roundtrip.zip',{'CASES/MU/BLIND/RESPONSE_RAW.json':raw})
    with zipfile.ZipFile(tmp_path/'roundtrip.zip') as z:
        assert z.read('CASES/MU/BLIND/RESPONSE_RAW.json')==raw
        m=json.loads(z.read('MANIFEST.json'))['files']
        assert m['CASES/MU/BLIND/RESPONSE_RAW.json']['sha256']==r.digest(raw)
    assert receipt['CRC']==receipt['memberSHA']=='PASS'

def test_private_prompt_and_credential_payload_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'OUT',tmp_path)
    with pytest.raises(AssertionError):r.seal('bad1.zip',{'prompt.private.txt':b'prompt'})
    with pytest.raises(AssertionError):r.seal('bad2.zip',{'payload.json':b'{"x":"-----BEGIN '+b'PRIVATE KEY-----"}'})
    assert not list(tmp_path.glob('*.zip'))
