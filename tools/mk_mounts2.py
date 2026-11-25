import numpy as np,re,json,cv2,math
from PIL import Image
from scipy import ndimage
from skimage.segmentation import watershed
Image.MAX_IMAGE_PIXELS=None
exec(open('tiles.py').read().split("sea=dem==-32768")[0])
F=4;RR=R//F
z=dem[:dem.shape[0]//F*F,:dem.shape[1]//F*F].reshape(dem.shape[0]//F,F,dem.shape[1]//F,F).astype(np.float32)
z[z<-1000]=np.nan;z=np.nanmean(z,axis=(1,3));sea=np.isnan(z);z=np.nan_to_num(z,nan=0);del dem
zs=ndimage.gaussian_filter(z,1.0)
s=open('/home/claude/mapa/index.html').read();t=s[s.index('const MOUNTS=['):];t=t[:t.index('];')]
M=[(n,float(a),float(b)) for n,a,b in re.findall(r'\["([^"]+)",\s*([\d.]+),\s*([\d.]+)',t)]
kx=math.cos(math.radians(44));px=0.37  # km po pikselu (visina)
markers=np.zeros(z.shape,np.int32);info={}
for i,(n,la,lo) in enumerate(M):
    r=int((LAT1-la)*RR);c=int((lo-LON0)*RR);W=int(5/px)
    w=zs[r-W:r+W+1,c-int(W/kx):c+int(W/kx)+1]
    yy,xx=np.mgrid[0:w.shape[0],0:w.shape[1]];d=np.hypot((yy-W)*px,(xx-int(W/kx))*px*kx)
    pr,pc=np.unravel_index(np.argmax(np.where(d<=(1.5 if n=="Igman" else 5),w,-1)),w.shape);pr+=r-W;pc+=c-int(W/kx)
    markers[pr,pc]=i+1
    B=int(30/px);bw=z[max(0,pr-B):pr+B,max(0,pc-int(B/kx)):pc+int(B/kx)]
    base=float(np.percentile(bw[bw>0],10)) if (bw>0).any() else 0
    info[i]=(pr,pc,float(zs[pr,pc]),base)
exec(open('/home/claude/scripts/mthr.py').read())
lab=watershed(-zs,markers,mask=~sea)
out={};rep=[]
for i,(n,la,lo) in enumerate(M):
    pr,pc,pk,base=info[i];thr,cap=T[n]
    B=int(cap/px)+2;r0,c0=max(0,pr-B),max(0,pc-int(B/kx))
    sl=(slice(r0,pr+B),slice(c0,pc+int(B/kx)))
    yy,xx=np.mgrid[0:lab[sl].shape[0],0:lab[sl].shape[1]];dm=np.hypot((yy-(pr-r0))*px,(xx-(pc-c0))*px*kx)<cap
    while True:   # mala brda: spuštaj izohipsu dok površina ne bude bar ~20 km²
        m=(lab[sl]==i+1)&(zs[sl]>=thr)&dm
        L,k=ndimage.label(m)
        if L[pr-r0,pc-c0]:
            m=L==L[pr-r0,pc-c0]
            if m.sum()*px*px*kx>=20 or thr<=base+60:break
        elif thr<=base+60:break
        thr-=25
    if not m.any() or not L[pr-r0,pc-c0]:continue;m=ndimage.binary_fill_holes(ndimage.binary_closing(m,iterations=2))
    sm=cv2.GaussianBlur(m.astype(np.float32),(0,0),1.5)>0.5
    cs,_=cv2.findContours(sm.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    cn=max(cs,key=cv2.contourArea);a=cv2.approxPolyDP(cn,0.9,True)[:,0,:]
    out[n]=[[round(LAT1-(y+r0+0.5)/RR,3),round(LON0+(x+c0+0.5)/RR,3)] for x,y in a]
    rep.append((n,int(pk),int(base),int(thr),int(cv2.contourArea(cn)*px*px*kx)))
json.dump(out,open('/home/claude/mounts.json','w'),separators=(',',':'),ensure_ascii=False)
for x in rep:
    if True or x[0] in('Kopaonik','Goč','Durmitor','Lovćen','Prokletije','Stara planina','Zlatibor','Tara','Fruška gora','Avala','Rtanj','Šar planina','Velebit','Bjelašnica','Jahorina','Golija','Ovčar i Kablar','Vršačke planine'):print(x)
print(len(out),len(M))
