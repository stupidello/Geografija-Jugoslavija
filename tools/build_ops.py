import pickle,json,re,numpy as np,cv2
from matplotlib.path import Path as MP
RSX,ME=pickle.load(open('/home/claude/geo/ops.pkl','rb'))
O2=pickle.load(open('/home/claude/geo/ops2.pkl','rb'))
CY=dict(zip("абвгдѓежзѕијклљмнњопрстќуфхцчџшђћ",["a","b","v","g","d","đ","e","ž","z","dz","i","j","k","l","lj","m","n","nj","o","p","r","s","t","ć","u","f","h","c","č","dž","š","đ","ć"]))
def lat(s):
    o=""
    for ch in s:
        l=CY.get(ch.lower())
        if l is None:o+=ch
        else:o+=(l[0].upper()+l[1:]) if ch.isupper() else l
    return o
def clean(n):
    n=re.sub(r'^(Grad|Opština|Općina|Opčina|Općina)\s+','',n);return n
REN={'Demir Hisar/Murgaševo':'Demir Hisar','Banjaluka':'Banja Luka','Foča (FBiH)':'Foča-Ustikolina','Foča (RS)':'Foča','Trnovo (FBiH)':'Trnovo','Skender Vakuf (Kneževo)':'Kneževo','Kupres (RS)':'Kupres (RS)','Skopje':'Skoplje','Bitola':'Bitolj'}
units=[]
import sys
def dp(r,eps=0.0006):
    a=np.array(r,np.float32)[:,None,:];s=cv2.approxPolyDP(a,eps,True)[:,0,:]
    return [[round(float(y),4),round(float(x),4)] for x,y in s]
def lp(ps):
    a=np.array(max(ps,key=lambda p:len(p[0]))[0]);x0,y0=a.min(0);x1,y1=a.max(0);K=300
    m=np.zeros((int((y1-y0)*K)+3,int((x1-x0)*K*0.72)+3),np.uint8)
    cv2.fillPoly(m,[np.round(np.c_[(a[:,0]-x0)*K*0.72+1,(y1-a[:,1])*K+1]).astype(np.int32)],1)
    dt=cv2.distanceTransform(m,cv2.DIST_L2,3);r,c=np.unravel_index(dt.argmax(),dt.shape)
    return [round(y1-(r-1)/K,4),round(x0+(c-1)/(K*0.72),4)]
def add(name,grp,ps):units.append(dict(n=name,g=grp,r=[dp(p[0]) for p in ps if len(p[0])>3],c=lp(ps)))
for u in RSX:add(u['name'],'RS',u['ps'])
for u in ME:add(u['name'],'ME',u['ps'])
for u in O2:
    if u['cc']=='MK':n=re.sub(r'^(Општина|Град)\s+','',u['cyr']);n=lat(n)
    else:n=clean(u['name'])
    add(REN.get(n,n),u['cc'],u['ps'])
# Hrvatska
from PIL import Image,ImageDraw
geo=json.load(open('/home/claude/geo_out.json'));K=60
im=Image.new('L',(13*K,8*K),0);d=ImageDraw.Draw(im)
for ft in geo['features']:
    if ft['id']=='HR':
        for p in ft['geometry']['coordinates']:d.polygon([((x-12)*K,(48-y)*K) for x,y in p[0]],fill=1)
HRM=np.array(im)
for f in json.load(open('/mnt/user-data/uploads/export_1.geojson'))['features']:
    if f['geometry']['type'] not in('Polygon','MultiPolygon'):continue
    ps=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
    a=np.array(max(ps,key=lambda q:len(q[0]))[0]);hits=sum(HRM[int((48-y)*K),int((x-12)*K)] for x,y in a[::max(1,len(a)//100)] if 0<=int((48-y)*K)<480 and 0<=int((x-12)*K)<780)
    if hits==0:continue
    nm=f['properties'].get('name')
    if not re.match(r'^(Grad|Općina) ',nm):continue
    n=re.sub(r'^(Grad|Općina)\s+','',nm)
    add(n,'HR',ps)
# Grad Zagreb nije u fajlu (viši nivo): rupa okružena opštinama oko njega
K2=1000;x0,y1=15.6,46.05;W,H=int(0.8*K2*0.72),int(0.5*K2)
m=np.zeros((H,W),np.uint8)
for u in units:
    if u['g']!='HR':continue
    for r in u['r']:
        a=np.array(r);cv2.fillPoly(m,[np.round(np.c_[(a[:,1]-x0)*K2*0.72,(y1-a[:,0])*K2]).astype(np.int32)],1)
from scipy import ndimage
L,_=ndimage.label(m==0);zr,zc=int((y1-45.813)*K2),int((15.978-x0)*K2*0.72);hole=(L==L[zr,zc]).astype(np.uint8)
if hole[0].any() or hole[-1].any() or hole[:,0].any() or hole[:,-1].any():print('Zagreb rupa nije zatvorena!')
else:
    cs,_=cv2.findContours(hole,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cn=max(cs,key=cv2.contourArea)
    ring=[[x0+x/(K2*0.72),y1-y/K2] for x,y in cn[:,0,:]];add('Zagreb','HR',[[ring]]);print('Zagreb km2',int(cv2.contourArea(cn)*111*111*0.72/(K2*K2*0.72)))
s=open('/home/claude/mapa/index.html').read();t=s[s.index('const CITIES=['):s.index('const COAST=')]
P=[(f[0],float(f[1]),float(f[2])) for f in re.findall(r'\["([^"]+)",\s*(\d+\.\d+),\s*(\d+\.\d+)',t)]
paths=[[MP([(x,y) for y,x in r]) for r in u['r']] for u in units]
p2u={}
for n,la,lo in P:
    for i,ps in enumerate(paths):
        if any(m.contains_point((lo,la)) for m in ps):p2u[n]=i;break
import os
for g in sorted({u['g'] for u in units}):
    idx=[i for i,u in enumerate(units) if u['g']==g];loc={i:k for k,i in enumerate(idx)}
    o=json.dumps({'u':[units[i] for i in idx],'p':{n:loc[i] for n,i in p2u.items() if i in loc}},separators=(',',':'),ensure_ascii=False)
    open(f'/home/claude/mapa/opstine_{g}.json','w').write(o);print(g,len(o))
out=''
from collections import Counter
print(Counter(u['g'] for u in units),len(p2u),len(out))
vc=s[s.index('const VCLIPS={'):];vc=vc[:vc.index('};')]
for g in('HR',):
    miss=[u['n'] for u in units if u['g']==g and '"'+u['n']+'"' not in vc];print(g,len(miss),miss)
