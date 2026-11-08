"""No-auth/no-network app-server help and initialize/clean shutdown only."""
from pathlib import Path
import hashlib
import json
import os
import select
import signal
import subprocess
import sys
import time

H=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
B=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else H.parents[1]/'private-runtime/c21l-guarded-host-0167-20261108'
binary=B/'target/dev-small/codex-app-server'
root=Path('/private/tmp/c21l-rpc-smoke-20261108')
root.mkdir(mode=0o700)
for n in ('home','codex-home','tmp'):(root/n).mkdir()
sb='(version 1)\n(allow default)\n(deny network*)\n(deny file-read-data (require-all (subpath "/Users/sskim") (require-not (literal '+json.dumps(str(binary))+'))))\n(deny file-write* (subpath "/Users/sskim"))\n'
with (root/'host.sb').open('x') as f:f.write(sb)
env=dict(PATH='/usr/bin:/bin',HOME=str(root/'home'),CODEX_HOME=str(root/'codex-home'),TMPDIR=str(root/'tmp'),
    RUST_LOG='off',CODEX_DISABLE_REMOTE_CONTROL='1')
command=['/usr/bin/sandbox-exec','-f',str(root/'host.sb'),str(binary)]
help_=subprocess.run(command+['--help'],env=env,cwd=root,capture_output=True,timeout=20)
with (root/'help.txt').open('xb') as f:f.write(help_.stdout+help_.stderr)
assert help_.returncode==0 and b'--listen' in help_.stdout
initialized=False;forced=False
with (root/'stderr.txt').open('xb') as err:
    p=subprocess.Popen(command+['--listen','stdio://'],env=env,cwd=root,
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,start_new_session=True)
    init=dict(id=1,method='initialize',params=dict(clientInfo=dict(name='c21l_offline_smoke',version='1'),
        capabilities=dict(experimentalApi=True)))
    p.stdin.write((json.dumps(init)+'\n').encode());p.stdin.flush()
    deadline=time.monotonic()+30
    raw=b''
    while time.monotonic()<deadline and p.poll() is None:
        if select.select([p.stdout],[],[],1)[0]:
            part=os.read(p.stdout.fileno(),65536)
            if not part:break
            raw+=part
            assert len(raw)<256*1024
            for line in raw.splitlines():
                try:e=json.loads(line)
                except ValueError:continue
                if e.get('id')==1 and 'result' in e:initialized=True
            if initialized:break
    if initialized:
        p.stdin.write(b'{"method":"initialized"}\n');p.stdin.flush()
    p.stdin.close()
    try:p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        forced=True;os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
with (root/'stdout.jsonl').open('xb') as f:f.write(raw)
receipt=dict(real_binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),help_pass=help_.returncode==0,
    initialized=initialized,exit=p.returncode,forced=forced,clean_shutdown=not forced and p.returncode==0,
    OS_network='DENIED_INCLUDING_LOOPBACK',auth_material='NONE',turn_start_requests=0,model_HTTP=0,
    pass_=initialized and not forced and p.returncode==0)
with (H/'RPC_SMOKE.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
