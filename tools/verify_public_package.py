"""CI-only Docker smoke: temporary resources, loopback HTTP, inference off.

This checks the HTTPS cookie contract over a private HTTP test connection with a
fixed Host/Origin. It is not a TLS, browser, camera or public-hosting acceptance.
No credential, cookie, raw response, container log or arbitrary exception is printed.
"""
import argparse
from http.client import HTTPConnection
from http.cookies import SimpleCookie
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

ORIGIN = 'https://demo.example'


def docker(*arguments, timeout=60, include_stderr=False):
    result = subprocess.run(['docker', *arguments], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('container_command_failed')
    return result.stdout + (result.stderr if include_stderr else '')


class Visitor:
    def __init__(self, port):
        self.port, self.cookie, self.csrf, self.run = port, '', '', ''

    def request(self, path, body=None, role='commander', headers=None):
        values = {'Host':'demo.example', 'Origin':ORIGIN, 'X-FaultTrace-Demo':'1',
            'X-FaultTrace-Workspace':role, 'X-FaultTrace-Demo-Run':self.run,
            'X-CSRF-Token':self.csrf}
        if self.cookie:
            values['Cookie'] = self.cookie
        if body is not None:
            values.update({'Content-Type':'application/json', 'Idempotency-Key':str(uuid.uuid4())})
        values.update(headers or {})
        connection = HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request('POST' if body is not None else 'GET', path,
                json.dumps(body) if isinstance(body,dict) else body, values)
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def json(self, path, body=None, role='commander', headers=None, status=200):
        code, data, response_headers = self.request(path, body, role, headers)
        if code != status:
            raise RuntimeError('unexpected_http_status')
        return json.loads(data), response_headers

    def start(self):
        value, headers = self.json('/api/demo/session')
        cookies = SimpleCookie(headers['set-cookie'])
        item = cookies['__Host-faulttrace_demo']
        assert item['httponly'] and item['secure'] and item['samesite']=='strict'
        assert item['path']=='/' and not item['domain']
        self.cookie, self.csrf = item.OutputString(attrs=[]), value['csrf_token']
        value, _ = self.json('/api/demo/start', {})
        self.run = value['active_run']
        assert value['inference_enabled'] is False


def ready(visitor):
    deadline = time.monotonic()+45
    while time.monotonic() < deadline:
        try:
            value, _ = visitor.json('/healthz')
            if value == {'status':'ok'}:
                return
        except Exception:
            pass
        time.sleep(0.25)
    raise RuntimeError('package_not_ready')


def verify(image, revision):
    if not re.fullmatch('[0-9a-f]{40}', revision) or image != 'faulttrace-review:'+revision:
        print('public_package_verification_failed: invalid_image_revision')
        return 1
    label = 'faulttrace-ci-'+uuid.uuid4().hex
    container, volume, network = label, label+'-data', label+'-network'
    created_volume = created_network = False
    phase, success = 'image_preflight', False
    try:
        environment = json.loads(docker('image', 'inspect', image, '--format', '{{json .Config.Env}}'))
        values = dict(value.split('=',1) for value in environment)
        assert values['FAULTTRACE_BUILD_REVISION']==revision
        assert not any(values.get(name) for name in ('NEBIUS_API_KEY','TAVILY_API_KEY','LANGSMITH_API_KEY'))
        phase = 'temporary_resources'
        docker('volume','create',volume)
        created_volume = True
        # Internal-only bridge networks do not publish host ports on current
        # Docker Engine. A unique bridge supports the localhost binding; server
        # inference stays hard-disabled, with no provider keys or attempt ledger.
        docker('network','create',network)
        created_network = True
        phase = 'container_launch'
        docker('run','--detach','--name',container,'--network',network,
            '--publish','127.0.0.1::10000','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,size=16m',
            '--mount',f'type=volume,src={volume},dst=/var/lib/faulttrace',
            '--env','FAULTTRACE_DEMO_ROOT=/var/lib/faulttrace/judge',
            '--env','FAULTTRACE_DEMO_ORIGIN='+ORIGIN,
            '--env','FAULTTRACE_PERSISTENT_STORAGE_CONFIRMED=1',
            '--env','FAULTTRACE_DEMO_LIVE=0','--env','FAULTTRACE_ALLOW_INFERENCE=0',
            '--env','NEBIUS_API_KEY=','--env','TAVILY_API_KEY=','--env','LANGSMITH_API_KEY=',image)
        phase = 'published_port'
        ports = json.loads(docker('inspect',container,'--format','{{json .NetworkSettings.Ports}}'))
        bindings = ports['10000/tcp']
        assert len(bindings)==1 and bindings[0]['HostIp']=='127.0.0.1'
        port = int(bindings[0]['HostPort'])
        first = Visitor(port)
        phase = 'http_readiness'
        ready(first)
        html = ''
        for route in ('/','/commander','/operator'):
            status, data, headers = first.request(route)
            assert status==200 and headers['cache-control']=='no-store'
            assert "frame-ancestors 'none'" in headers['content-security-policy']
            html = data.decode()
            assert '<div id="root">' in html
        assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"',html)
        assert len(assets)>=2
        for path in assets+['/favicon.ico','/favicon.svg']:
            status, data, _ = first.request(path)
            assert status==200 and data
        assert first.request('/.env')[0]==404
        phase = 'sessions_and_isolation'
        first.start()
        a, _ = first.json('/api/state')
        operator, _ = first.json('/api/state',role='operator')
        assert a['incident']==operator['incident'] and a['task']['id']==operator['task']['id']
        assert a['inference_enabled'] is False and not a['planning']
        for role in ('commander','operator'):
            identity, _ = first.json('/api/identity',role=role)
            assert identity['profile']=='demo' and identity['role']==role
        second = Visitor(port)
        second.start()
        b, _ = second.json('/api/state')
        assert a['incident']['id']!=b['incident']['id'] and a['task']['id']!=b['task']['id']
        second.json('/api/tasks/'+a['task']['id']+'/reports',
            {'revision':a['task']['revision'],'report':'cannot-access'},role='operator',status=403)
        first.json('/api/demo/restart',{},headers={'X-CSRF-Token':'invalid'},status=403)
        first.json('/api/demo/restart',{},headers={'Origin':'https://invalid.example'},status=403)
        image = (Path(__file__).resolve().parents[1]/'fixtures/image-evidence/panel-a.png').read_bytes()
        uploaded, _ = first.json('/api/tasks/'+a['task']['id']+'/images',image,role='operator',headers={
            'Content-Type':'image/png','X-Task-Revision':str(a['task']['revision']),
            'X-Evidence-Purpose':'reference-photo'})
        image_path = '/api/evidence/'+uploaded['evidence_id']+'/image'
        code, original_image, _ = first.request(image_path)
        assert code==200 and original_image.startswith(b'\x89PNG')
        assert second.request(image_path)[0]==403
        phase = 'restart_persistence'
        docker('restart',container,timeout=60)
        # Docker may allocate a different ephemeral host port on restart. Resume
        # the same visitors/cookies against the new loopback-only binding.
        phase = 'restart_port_binding'
        ports = json.loads(docker('inspect',container,'--format','{{json .NetworkSettings.Ports}}'))
        bindings = ports['10000/tcp']
        assert len(bindings)==1 and bindings[0]['HostIp']=='127.0.0.1'
        first.port = second.port = int(bindings[0]['HostPort'])
        phase = 'restart_readiness'
        ready(first)
        phase = 'restart_persistence'
        resumed, _ = first.json('/api/demo/session')
        assert resumed['active_run']==first.run
        after, _ = first.json('/api/state')
        assert after['incident']==a['incident'] and after['task']['id']==a['task']['id']
        assert after['task']['creation_source']==a['task']['creation_source']
        code, restored_image, _ = first.request(image_path)
        assert code==200 and restored_image==original_image
        assert second.request(image_path)[0]==403
        phase = 'runtime_security_and_no_provider_accounting'
        check = ("from pathlib import Path; import os; "
            "assert Path('/proc/1/status').read_text().split('Uid:')[1].splitlines()[0].split()==['10001']*4; "
            "assert not list(Path('/var/lib/faulttrace/judge').rglob('usage.json')); "
            "assert not Path('/app/.git').exists() and not Path('/app/.env').exists(); "
            "assert not any(os.environ.get(k) for k in ('NEBIUS_API_KEY','TAVILY_API_KEY','LANGSMITH_API_KEY')); "
            "print('runtime_policy_passed')")
        assert docker('exec',container,'python','-c',check).strip()=='runtime_policy_passed'
        logs = docker('logs',container,include_stderr=True)
        for secret in (first.cookie,first.csrf,second.cookie,second.csrf,
                       first.cookie.split('=',1)[1],second.cookie.split('=',1)[1]):
            assert secret not in logs
        success = True
    except Exception:
        # Inspect only bounded status/code and one known launcher marker. Never
        # expose raw Docker/app output, even when startup failed before HTTP.
        detail = ''
        try:
            state = json.loads(docker('inspect',container,'--format','{{json .State}}'))
            status, code = state.get('Status'), state.get('ExitCode')
            if status in ('created','running','paused','restarting','removing','exited','dead') and type(code) is int:
                detail = f' container_{status}_exit_{code}'
            if 'public_startup_failed:' in docker('logs',container,include_stderr=True):
                detail += ' launcher_preflight_failed'
        except Exception:
            pass
        print('public_package_verification_failed: '+phase+detail)
    finally:
        try:
            # Names are unique to this invocation; no unrelated container/volume is touched.
            subprocess.run(['docker','rm','--force',container],capture_output=True,timeout=30)
            if created_volume:
                docker('volume','rm',volume)
            if created_network:
                docker('network','rm',network)
        except Exception:
            print('public_package_verification_failed: temporary_resource_cleanup')
            success = False
    if success:
        print('PASS public Docker package: routes/assets, secure-cookie contract, both roles, isolation, CSRF/Origin, restart persistence; inference off')
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',required=True)
    parser.add_argument('--revision',required=True)
    args = parser.parse_args()
    return verify(args.image,args.revision)


if __name__ == '__main__':
    raise SystemExit(main())
