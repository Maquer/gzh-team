import io
s=io.open('split.py',encoding='utf-8').read().split('\n')
i=[k for k,l in enumerate(s) if l.startswith('MAP = [')][0]
j=[k for k,l in enumerate(s[i+1:],i+1) if l.strip()==']'][0]
d={'N':1019};exec('\n'.join(s[i:j+1]),d);M=sorted(d['MAP'])
st=io.open('src/TEAM-v1.5.frozen.md',encoding='utf-8').read().split('\n')

files={}
for a,b,p in M:
    if p!='IDX': files.setdefault(p,[]).append((a,b))
F={};G={}
for p,segs in files.items():
    r=io.open(p,encoding='utf-8').read();k=r.index('\n---\n\n')
    body=r[k+6:].rstrip('\n').split('\n')
    exp=sum(b-a+1 for a,b in segs)+len(segs)-1
    F[p]=body;G[p]=exp-len(body)
    assert len(body)>0 and any(x.strip() for x in body),(p,body[:2])
O={};L=[];t=0
for a,b,p in M:
    n=b-a+1
    if p=='IDX':
        L+=st[a-1:b];t+=1
        continue
    segs=files[p];li=segs.index((a,b))
    if li==len(segs)-1: n-=G[p]
    cur=O.get(p,0);assert len(F[p][cur:cur+n])==n,(p,cur,n)
    L+=F[p][cur:cur+n];O[p]=cur+n+(1 if li<len(segs)-1 else 0)
    if li==len(segs)-1: L+=['']*G[p]
assert len(L)==1019,len(L)
if L and L[-1]=='' and len(L)>1: pass  # 已有尾部空行
elif not L or L[-1]!='':
    L.append('')  # frozen 末尾有空行，重建时补上
assert len(L)==1020 or (L and L[-1]=='' and len(L)==1019),len(L)
io.open('TEAM.md.bak-pre-split','w',encoding='utf-8').write('\n'.join(L))
print('lines',len(L),'bytes',len('\n'.join(L).encode()),'idx',t)
