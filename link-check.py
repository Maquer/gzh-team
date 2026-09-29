import io,os,json,glob,re,sys
SRC='/tmp/src.md'
N=1016
fails=[]; warns=[]
O=io.open(SRC,encoding='utf-8').read().split('\n')
s=io.open('split.py',encoding='utf-8').read().split('\n')
i=[k for k,l in enumerate(s) if l.startswith('MAP = [')][0]
j=[k for k,l in enumerate(s[i+1:],i+1) if l.strip()==']'][0]
d={'N':N};exec('\n'.join(s[i:j+1]),d);M=sorted(d['MAP'])
# A1 ranges: in-bounds / no overlap / full coverage
cov=set()
for a,b,p in M:
    if not (1<=a<=b<=N): fails.append('A1 range %s-%s %s'%(a,b,p)); continue
    if len(cov & set(range(a,b+1))): fails.append('A1 overlap at %s-%s %s'%(a,b,p))
    cov.update(range(a,b+1))
miss=[k for k in range(1,N+1) if k not in cov]
if miss: fails.append('A1 uncovered %d lines e.g. %s'%(len(miss),miss[:8]))
print('A1 ranges/coverage : %s (covered %d/%d)'%('OK' if not miss and len(cov)==N else 'FAIL',len(cov),N))
# A2 per-segment verbatim
files={}
for a,b,p in M:
    if p!='IDX': files.setdefault(p,[]).append((a,b))
bad=0
for p,segs in sorted(files.items()):
    r=io.open(p,encoding='utf-8').read(); body=r[r.index('\n---\n\n')+6:].split('\n'); cur=0
    for (a,b) in segs:
        if body[cur:cur+b-a+1]!=O[a-1:b]: bad+=1
        cur+=b-a+1+1
if bad: fails.append('A2 %d segment mismatch'%bad)
print('A2 verbatim        : %s (%d segs)'%('OK' if not bad else 'FAIL',sum(len(v) for v in files.values())))
# A3 frontmatter id unique
prods=glob.glob('docs/**/*.md',recursive=True)+['CHANGELOG.md']
ids=[]; badfm=0
for p in prods:
    L=io.open(p,encoding='utf-8').read().split('\n')
    if L[0]!='---': badfm+=1; continue
    k=[n for n in range(0,min(10,len(L))) if L[n]=='---'][1]
    fm=dict(x.split(':',1) for x in L[1:k] if ':' in x)
    ids.append(fm['id'].strip())
dup=[x for x in set(ids) if ids.count(x)>1]
if dup or badfm: fails.append('A3 dup=%s missing_fm=%d'%(dup,badfm))
print('A3 id unique       : %s (%d ids)'%('OK' if not dup and not badfm else 'FAIL',len(ids)))
# A4 no dangling relative links
dang=0; checked=0
for p in prods+['TEAM.md']:
    base=os.path.dirname(p) or '.'
    for t in re.findall(r'\]\(([^)]+)\)',io.open(p,encoding='utf-8').read()):
        if '://' in t or t.startswith('#') or t.startswith('http'): continue
        checked+=1
        if not (os.path.exists(os.path.join(base,t.split('#')[0])) or os.path.exists(t.split('#')[0])):
            dang+=1; print('   DANGLING',p,'->',t)
if dang: fails.append('A4 %d dangling'%dang)
print('A4 links           : %s (%d rel checked)'%('OK' if not dang else 'FAIL',checked))
def tok(f):
    r=io.open(f,encoding='utf-8').read(); m=r.find('\n---\n\n')
    return len(r[m+6:]) if m>0 else len(r)
# A5 no orphans vs manifest
prods2=prods+['TEAM.md']
man=json.load(io.open('docs/manifest.json',encoding='utf-8')).get('files',[])
mpath=set(x['path'] for x in man)
pset=set(prods2)
extra=sorted(pset-mpath); ghost=sorted(mpath-pset)
miss=[g for g in sorted(mpath) if not os.path.exists(g)]
if extra or ghost or miss: fails.append('A5 drift extra=%s ghost=%s missing=%s'%(extra,ghost,miss))
print('A5 manifest/actual : %s (actual %d, manifest %d)'%('OK' if not extra and not ghost and not miss else 'FAIL',len(prods2),len(mpath)))
# A6 token budget (advisory) -- estimator = len(body), same as split.py
over=[]; drift=[]
for f in prods2:
    v=tok(f); r=io.open(f,encoding='utf-8').read()
    m=re.search(r'^tokens:\s*(\d+)',r,re.M)
    if m and int(m.group(1))!=v: drift.append((f,int(m.group(1)),v))
    if v>2048: over.append((f,v))
if drift: fails.append('A6 frontmatter token drift %s'%drift[:4])
print('A6 token budget    : ADVISORY %d files >2048 (frontmatter drift %d)'%(len(over),len(drift)))
for f,v in sorted(over,key=lambda x:-x[1]): print('   OVER %-38s %d'%(f,v))
warns.append('A6 %d over wall'%len(over))
print()
print('FAILS: %d   WARNS: %d'%(len(fails),len(warns)))
for f in fails: print(' FAIL -',f)
sys.exit(1 if fails else 0)
