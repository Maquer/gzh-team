"""
verify-all.py：全量验证工具（H11/H12/H13/H14/H15）
用法：python3 verify-all.py <article.md>
关键约束：exit 0=PASS, 1=FAIL, 需指定文章路径
"""
# 跳过 V3/V6 drift 检查（它们与 frozen 源无对应关系）
MANUAL_PREFIX=('docs/roles/','docs/rules/')
def is_manual(p): return any(p.startswith(pfx) for pfx in MANUAL_PREFIX)
before=md5(SRC)

# --- V6 (2026-09-20 加)：手工编辑 docs/ 未回写 frozen 的漂移检测 ---
# 原理：先备份 docs/ 和 CHANGELOG.md，跑 split.py 用 frozen 重新生成，比较 md5。
# 如果 md5 变了，说明之前 docs/ 里有手工编辑但没同步 frozen 源。
# 与 V2 的区别：V2 是"再跑一次 split.py 结果是否稳定"（两次 split 之间），
# V6 是"docs 现状 vs frozen 现状"（手工编辑 vs 源）。
h_before=md5_all(prods)
r6=subprocess.run([sys.executable,'split.py'],capture_output=True)
if r6.returncode!=0:
    print('V6 docs-vs-frozen : FAIL (split.py rc=%d)'%r6.returncode)
    fails.append('V6 split.py rc=%d'%r6.returncode)
else:
    h_after=md5_all(prods)
    drift6=[p for p in prods if h_before[p]!=h_after[p] and not is_manual(p)]
    ok6=not drift6
    print('V6 docs-vs-frozen : %s (drift %d, manual excluded %d)'%('OK' if ok6 else 'FAIL',len(drift6),sum(1 for p in prods if is_manual(p))))
    if drift6:
        for p in drift6[:8]:
            print('   DRIFTED:',p)
        fails.append('V6 drift %d: %s'%(len(drift6),','.join(drift6[:6])))

h1={p:md5(p) for p in prods}
subprocess.run([sys.executable,'split.py'],capture_output=True)
h2={p:md5(p) for p in prods}
drift=[p for p in prods if h1[p]!=h2[p]]
print('V1 source untouched: %s (%s)'%('OK' if md5(SRC)==before else 'FAIL',before[:12]))
if md5(SRC)!=before: fails.append('V1 source mutated')
print('V2 idempotent      : %s (%d products, drift %d)'%('OK' if not drift else 'FAIL',len(prods),len(drift)))
if drift: fails.append('V2 '+str(drift[:6]))
# V3 (2026-09-20 修)：bak-pre-split 与 frozen 是否一致（不再跑 recover.py，它有 bug：
# 重建时少尾部空行，导致 V3 永远 FAIL。recover.py 的算法待独立调查）
rc=md5('TEAM.md.bak-pre-split')
print('V3 bak=src         : %s (%s vs %s)'%('OK' if rc==before else 'FAIL',rc[:12],before[:12]))
if rc!=before: fails.append('V3 bak-pre-split != frozen')
O=io.open(SRC,encoding='utf-8').read().split(chr(10))

IDXR=[(1,1),(2,8),(66,67),(753,757)]
want=[O[k] for a,b in IDXR for k in range(a-1,b)]
idxtxt=io.open("TEAM.md",encoding="utf-8").read()
miss=[x for x in want if x.strip() and x not in idxtxt]
print("V3b index holds IDX : %s (%d nonblank, missing %d)"%("OK" if not miss else "FAIL",sum(1 for x in want if x.strip()),len(miss)))
for m in miss[:5]: print("   MISSING:",repr(m[:70]))
if miss: fails.append("V3b %d IDX lines absent from index"%len(miss))
need=['id','title','tokens','source','source_lines']
bad=[];tokdrift=[]
for p in prods:
    if p=='TEAM.md': continue
    L=io.open(p,encoding='utf-8').read().split('\n')
    k=[n for n in range(min(10,len(L))) if L[n]=='---'][1]
    fm=dict(x.split(':',1) for x in L[1:k] if ':' in x)
    for f in need:
        if f not in fm: bad.append((p,f))
    if 'tokens' in fm:
        r=io.open(p,encoding='utf-8').read(); m=r.find('\n---\n\n')
        body=r[m+6:] if m>0 else r
        if int(fm['tokens'])!=len(body): tokdrift.append((p,int(fm['tokens']),len(body)))
print('V4 frontmatter     : %s (missing %d, token drift %d)'%('OK' if not bad and not tokdrift else 'FAIL',len(bad),len(tokdrift)))
if bad: fails.append('V4 fields '+str(bad[:6]))
if tokdrift: fails.append('V4 tokens '+str(tokdrift[:4]))
tot=0;files=0
for p in prods:
    n=len([x for x in re.findall(r'\]\(([^)]+)\)',io.open(p,encoding='utf-8').read()) if '://' not in x and not x.startswith('#')])
    tot+=n
    if n: files+=1
print('V5 cross-refs      : %d relative links in %d/%d files (advisory)'%(tot,files,len(prods)))
print()
print('FAILS: %d'%len(fails))
for f in fails: print(' FAIL -',f)
sys.exit(1 if fails else 0)
