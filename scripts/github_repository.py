"""Use Git's configured credential helper; never print or save credentials."""
import argparse, json, os, subprocess, urllib.request, urllib.error
parser=argparse.ArgumentParser()
parser.add_argument('--create',action='store_true')
args=parser.parse_args()
owner='Ayushnot41'
name='satquery-ai-pro'
env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'}
result=subprocess.run(['git','credential','fill'],input=f'protocol=https\nhost=github.com\nusername={owner}\n\n',text=True,capture_output=True,env=env,timeout=30)
if result.returncode:
    print('SIGN_IN_REQUIRED: No GitHub credential is available for Ayushnot41.')
    raise SystemExit(2)
values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
if values.get('username','').lower() != owner.lower():
    print('SIGN_IN_REQUIRED: Credential does not match the requested owner. No account used.')
    raise SystemExit(2)
token=values.get('password','')
def api(path, payload=None):
    request=urllib.request.Request('https://api.github.com'+path, data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Satquery-Pro-Repository-Setup','X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(request,timeout=25) as response:
        return json.load(response)
try:
    account=api('/user')
    if account['login'].lower() != owner.lower():
        print('SIGN_IN_REQUIRED: Authenticated account does not match Ayushnot41. No repository created.')
        raise SystemExit(2)
    print('Verified GitHub owner: '+owner)
    if args.create:
        try:
            api(f'/repos/{owner}/{name}')
            print('REPOSITORY_EXISTS: Refusing to overwrite an existing repository.')
            raise SystemExit(3)
        except urllib.error.HTTPError as error:
            if error.code != 404: raise
        repo=api('/user/repos',{'name':name,'private':True,'description':'Enhanced Satquery AI / BHUVISION workspace. Original features and assets preserved. See PRO_README.md for current setup and validation status.','auto_init':False})
        print('Created '+repo['html_url'])
except urllib.error.HTTPError as error:
    print(f'GitHub returned HTTP {error.code}. No credentials were displayed.')
    raise SystemExit(2)
