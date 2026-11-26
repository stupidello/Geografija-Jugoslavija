import json,numpy as np
from matplotlib.path import Path as MP
from collections import Counter
g=json.load(open('/mnt/user-data/uploads/export.geojson'))
geo=json.load(open('/home/claude/geo_out.json'))
CP={ft['id']:[MP(p[0]) for p in ft['geometry']['coordinates']] for ft in geo['features'] if ft['id'] in('RS','XK','ME')}
def rings(f):return f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
def area(ps):return sum(abs(0.5*float(np.dot(np.array(p[0])[:,0],np.roll(np.array(p[0])[:,1],-1))-np.dot(np.array(p[0])[:,1],np.roll(np.array(p[0])[:,0],-1)))) for p in ps)*111*111*0.72
def inside_pt(ps):  # tačka unutar najvećeg prstena
    p=max(ps,key=lambda q:len(q[0]))[0];a=np.array(p)
    # centroid pa ako ne valja, prva tačka pomerena
    c=a.mean(0)
    if MP(a).contains_point(c):return c
    for i in range(0,len(a),max(1,len(a)//50)):
        q=(a[i]+a[(i+len(a)//2)%len(a)])/2
        if MP(a).contains_point(q):return q
    return c
def country(pt):
    for k,ps in CP.items():
        if any(m.contains_point(pt) for m in ps):return k
    return '?'
U=[]
for f in g['features']:
    if f['geometry']['type'] not in('Polygon','MultiPolygon'):continue
    p=f['properties'];ps=rings(f);pt=inside_pt(ps)
    U.append(dict(name=p.get('name:sr-Latn') or p.get('name'),cyr=p.get('name'),lvl=p.get('admin_level'),ps=ps,a=area(ps),pt=pt,cc=country(pt)))
print(Counter((u['cc'],u['lvl']) for u in U))
gr=[u for u in U if u['lvl']=='7']
print([u['name'] for u in gr])
lvl6=[u for u in U if u['lvl']=='6'];print([ (u['name'],u['cc']) for u in lvl6][:100])
import pickle;pickle.dump(U,open('/home/claude/geo/units.pkl','wb'))
