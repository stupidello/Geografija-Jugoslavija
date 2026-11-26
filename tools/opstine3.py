import json,pickle,numpy as np,re,cv2
from matplotlib.path import Path as MP
geo=json.load(open('/home/claude/geo_out.json'))
CPOLY={ft['id']:ft['geometry']['coordinates'] for ft in geo['features'] if ft['id'] in('BA','MK')}
def rings(f):return f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
def area(ps):return sum(abs(0.5*float(np.dot(np.array(p[0])[:,0],np.roll(np.array(p[0])[:,1],-1))-np.dot(np.array(p[0])[:,1],np.roll(np.array(p[0])[:,0],-1)))) for p in ps)*111*111*0.72
# zemlja preko rasterske maske (tolerantno na razlike u granici)
K=60;x0,y1=12,48;from PIL import Image,ImageDraw
M={}
for k,cp in CPOLY.items():
    im=Image.new('L',(13*K,8*K),0);d=ImageDraw.Draw(im)
    for p in cp:d.polygon([((x-x0)*K,(y1-y)*K) for x,y in p[0]],fill=1)
    M[k]=np.array(im)
def cc(ps):
    a=np.array(max(ps,key=lambda q:len(q[0]))[0]);best=None
    cnt={k:0 for k in M}
    for x,y in a[::max(1,len(a)//200)]:
        for k in M:
            r,c=int((y1-y)*K),int((x-x0)*K)
            if 0<=r<M[k].shape[0] and 0<=c<M[k].shape[1] and M[k][r,c]:cnt[k]+=1
    k=max(cnt,key=cnt.get);return k if cnt[k]>0 else '?'
g=json.load(open('/mnt/user-data/uploads/export__2_.geojson'))
U=[]
for f in g['features']:
    if f['geometry']['type'] not in('Polygon','MultiPolygon'):continue
    p=f['properties']
    if p.get('admin_level') not in('6','7'):continue
    ps=rings(f);U.append(dict(name=p.get('name:sr-Latn') or p.get('name:hr') or p.get('name:bs') or p.get('name'),cyr=p.get('name'),nlat=p.get('name:sr-Latn') or p.get('name:mk-Latn') or p.get('name:en'),lvl=p.get('admin_level'),ps=ps,a=area(ps),cc=cc(ps)))
from collections import Counter
print(Counter((u['cc'],u['lvl']) for u in U))
l6=[u for u in U if u['lvl']=='6']
P6=[[MP(q[0]) for q in u['ps']] for u in l6]
def inside6(u):
    a=np.array(max(u['ps'],key=lambda q:len(q[0]))[0]);c=a.mean(0)
    return any(any(m.contains_point(c) for m in ps) for ps in P6)
l7=[u for u in U if u['lvl']=='7' and not inside6(u)]
for k in('BA','MK'):
    L=[u for u in l6+l7 if u['cc']==k];print(k,len(L),int(sum(u['a'] for u in L)))
pickle.dump([u for u in l6+l7 if u['cc'] in('BA','MK')],open('/home/claude/geo/ops2.pkl','wb'))
print([ (u['name'],u['nlat']) for u in l6+l7 if u['cc']=='MK'][:12])
print([u['name'] for u in l6+l7 if u['cc']=='BA'][:200])
