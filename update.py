#!/usr/bin/env python3
import concurrent.futures, json, os, pathlib, plistlib, re, sys, tempfile, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent
REPOS = [
 ('GestaltX','huamidev/GestaltX',None), ('3106','QuinnTang74/3106',None),
 ('WQManager','hseons/WQManager',None), ('iPadn','mengangs/ipadn',r'(?i)^(?!.*lite).*\.ipa$'),
 ('HGhubX','zxsos/HGhubX',None), ('AniCh','Sle2p/AniCh',None),
 ('Beans Music','XIaodou0416/Beans-Music',None), ('Cloudn','mengangs/Cloudn',None),
 ('Erosion-CN','Kianuni/Erosion-CN',None), ('Kazumi','Predidit/Kazumi',None),
 ('Regitela','ichitaso/Regitela',None),
 ('Henge','Leviidev/Henge',None),
 ('placard','frs0n/placard',None),
 ('Camlo','Kianuni/Camlo',None),
]
SOURCES = [
 ('One','https://raw.githubusercontent.com/ios151/One-releases/main/altsource.json'),
 ('WQ Files','https://raw.githubusercontent.com/kolbicz/WQFiles/main/source.json'),
]

def get(url):
 headers={'User-Agent':'Personal-LiveContainer-Source','Accept':'application/vnd.github+json'}
 if url.startswith('https://api.github.com/') and os.getenv('GH_TOKEN'):
  headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120) as r: return r.read()

def release_app(item, previous):
 name, repo, pattern = item
 releases=json.loads(get('https://api.github.com/repos/'+repo+'/releases?per_page=20'))
 release = asset = None
 for candidate in releases:
  if candidate.get('draft') or candidate.get('prerelease'): continue
  matches=[a for a in candidate.get('assets',[]) if a['name'].lower().endswith('.ipa') and (not pattern or re.search(pattern,a['name']))]
  if matches:
   if len(matches)!=1: raise ValueError('多个 IPA，需要指定选择规则: '+', '.join(a['name'] for a in matches))
   release,asset=candidate,matches[0]; break
 if not asset: raise ValueError('没有公开的正式版 IPA')
 url=asset['browser_download_url']
 old=previous.get(repo)
 if old and old.get('versions',[{}])[0].get('downloadURL')==url:
  return old
 data=get(url)
 with tempfile.TemporaryFile() as f:
  f.write(data); f.seek(0)
  with zipfile.ZipFile(f) as z:
   paths=[n for n in z.namelist() if re.fullmatch(r'Payload/[^/]+\.app/Info\.plist',n)]
   if len(paths)!=1: raise ValueError('IPA 内找不到唯一主应用 Info.plist')
   info=plistlib.loads(z.read(paths[0]))
 version=str(info.get('CFBundleShortVersionString') or release['tag_name'].lstrip('v'))
 entry={'name':name,'bundleIdentifier':info['CFBundleIdentifier'],'developerName':repo.split('/')[0],
        'localizedDescription':'来自 GitHub 官方项目 '+repo+'。',
        'iconURL':'https://github.com/'+repo.split('/')[0]+'.png',
        'versions':[{'version':version,'date':release['published_at'],'downloadURL':url,'size':asset['size']}],
        'xGithubRepository':repo}
 if info.get('MinimumOSVersion'): entry['versions'][0]['minOSVersion']=str(info['MinimumOSVersion'])
 return entry

def source_app(item):
 name,url=item
 data=json.loads(get(url)); apps=data['apps']
 if len(apps)!=1: raise ValueError('源包含多个应用，需核对选择')
 return apps[0]

def main():
 out=ROOT/'source.json'
 old=json.loads(out.read_text()) if out.exists() else {}
 previous={a.get('xGithubRepository'):a for a in old.get('apps',[]) if a.get('xGithubRepository')}
 previous_source={a.get('xSourceURL'):a for a in old.get('apps',[]) if a.get('xSourceURL')}
 apps=[None]*(len(REPOS)+len(SOURCES)); errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  jobs={pool.submit(release_app,item,previous):(i,item[0],item[1],False) for i,item in enumerate(REPOS)}
  jobs.update({pool.submit(source_app,item):(len(REPOS)+i,item[0],item[1],True) for i,item in enumerate(SOURCES)})
  for future in concurrent.futures.as_completed(jobs):
   i,name,key,is_source=jobs[future]
   try:
    app=future.result()
    if is_source: app['xSourceURL']=key
    apps[i]=app; print('OK',name, app.get('versions',[{}])[0].get('version'),flush=True)
   except Exception as e:
    apps[i]=(previous_source if is_source else previous).get(key)
    errors.append(name+': '+str(e)); print('ERROR',errors[-1],flush=True)
 apps=[a for a in apps if a]
 ids=[a['bundleIdentifier'] for a in apps]
 if len(ids)!=len(set(ids)): raise ValueError('应用 bundleIdentifier 重复')
 if not apps: raise ValueError('没有可用应用，拒绝覆盖原有源')
 result={'name':'个人 LiveContainer 应用源','identifier':'personal.livecontainer.source','subtitle':'GitHub 项目更新聚合','apps':apps,'news':[]}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if errors:
  print('更新不完整；已有条目已保留。',file=sys.stderr)
  return 1
 return 0
if __name__=='__main__': sys.exit(main())
