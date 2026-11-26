import pickle,json,numpy as np,re
from matplotlib.path import Path as MP
U=pickle.load(open('/home/claude/geo/units.pkl','rb'))
grads=[u for u in U if u['lvl']=='7' and u['cc']=='RS']
gpaths=[[MP(p[0]) for p in g['ps']] for g in grads]
ops=[u for u in U if u['lvl']=='8' and (u['cc']=='RS' or u['name']=='Opština Bajina Bašta') and not any(any(m.contains_point(u['pt']) for m in gp) for gp in gpaths)]
xk=[u for u in U if u['lvl']=='6' and u['cc']=='XK']
me=[u for u in U if u['lvl']=='6' and u['cc'] in('ME','?') and not u['name'].endswith('okrug')]
def clean(n):
    n=n.split(' / ')[0] if not n.startswith('Komuna') else n.split(' / ')[1]
    n=re.sub(r'^(Grad|Opština|Opšrina|Optšina|Općina|Glavni grad|Prijestolnica)\s+','',n);return n
RSX=[dict(name=clean(u['name']),ps=u['ps'],a=u['a'],kind='grad' if u in grads else 'opština') for u in grads+ops+xk]
ME=[dict(name=clean(u['name']),ps=u['ps'],a=u['a']) for u in me]
print(len(grads),len(ops),len(xk),len(RSX),len(ME))
print(sorted(x['name'] for x in RSX))
tot=sum(x['a'] for x in RSX);print('ukupno km2',int(tot))
pickle.dump((RSX,ME),open('/home/claude/geo/ops.pkl','wb'))
