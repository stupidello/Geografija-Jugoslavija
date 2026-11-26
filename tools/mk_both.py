import json,numpy as np,cv2
cad=json.load(open('cad.json'));bu=json.load(open('shapes.json'))
u=np.load('/home/claude/geo/urban.npy')>110
def ar(R):
    t=0
    for r in R:r=np.array(r);y,x=r[:,0],r[:,1];t+=abs(0.5*float(np.dot(x,np.roll(y,-1))-np.dot(y,np.roll(x,-1))))*111*111*0.72
    return t
def dp(r,eps):
    a=np.array(r,np.float32)[:,None,::-1];s=cv2.approxPolyDP(a,eps,True)[:,0,::-1]
    return [[round(float(y),4),round(float(x),4)] for y,x in s]
SKIP={'Beograd','Niš'}
out={};nb=0
for n in set(cad)|set(bu):
    c=cad.get(n)
    if c and n not in SKIP and ar(c)>=0.3:
        rings=[dp(r,0.0002) for r in c if len(r)>3]
        allp=np.concatenate([np.array(r) for r in c]);la0,lo0=allp.min(0);la1,lo1=allp.max(0)
        r0=int((48-la1)*1200)-2;c0=int((lo0-12)*1200)-2;r1=int((48-la0)*1200)+3;c1=int((lo1-12)*1200)+3
        m=np.zeros((r1-r0,c1-c0),np.uint8)
        for r in c:
            r=np.array(r);cv2.fillPoly(m,[np.round(np.c_[(r[:,1]-12)*1200-c0,(48-r[:,0])*1200-r0]).astype(np.int32)],1)
        b=(m>0)&u[r0:r1,c0:c1]
        b=cv2.morphologyEx(b.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        cs,_=cv2.findContours(b,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        br=[[[round(48-(y+r0+0.5)/1200,4),round(12+(x+c0+0.5)/1200,4)] for x,y in cv2.approxPolyDP(cn,0.9,True)[:,0,:]] for cn in cs if cv2.contourArea(cn)>=3]
        if not br and n in bu:br=bu[n]
        out[n]={'c':rings,'b':br};nb+=1
        if n in bu:out[n]['h']=bu[n]   # šire izgrađeno područje (preko granice naselja) — računa se kao pogodak
    elif n in bu:out[n]={'b':bu[n]}
s=json.dumps(out,separators=(',',':'),ensure_ascii=False);open('/home/claude/mapa/shapes.json','w').write(s);print(nb,len(out),len(s))
