import utils, os, sys, time, re, random
time.clock()
import api_utils as api
import jieba
jieba.add_word('出生', 909999)


def GetDetails(ent):
	avp = api.GetAVP(ent)
	desc = ([x[1] for x in avp if x[0] == 'DESC']+[''])[0]
	avps = [x for x in avp if not x[0] in ['DESC', 'CATEGORY_ZH']]
	desc = '#' + desc + '#'
	return avps, desc

def CutSentence(s):
	st = jieba.lcut(s)
	ret = []
	for x in st:
		if len(ret) > 0 and ret[-1].isdigit() and x in '年月日':
			ret[-1] += x
		else: ret.append(x)
	xpos = []; ii = 0
	for x in ret:
		ii += len(x); xpos.append(ii)
	return set(xpos)

def MatchAVP(avps, desc):
	for z in avps:
		p, o = z[:2]; ii = 0; z = '[%s]'%p[-3:]
		if o[0].isdigit() or o[-1].isdigit(): 
			try: desc = re.sub('([^0-9]%s[^0-9])'%o, lambda x:x.group(1)[0]+z+x.group(1)[-1], desc)
			except: pass
		else: desc = desc.replace(o, z)
	return desc


def MakePattern(avps, ds):
	patts = {}; preds = {x[0] for x in avps}
	for p in preds: # For every relations
		z = '[%s]'%p[-3:] # the Z equals the [p[-3:]] (IDENTIFIER of P)
		if not z in ds: continue # if no continue
		ii = 0 # sles 
		while z in ds[ii:]: # if z in from ii to next.
			ind = ds[ii:].index(z) + ii # get the index of Z inside inside it 
			indn = ind + len(z)	 # get the identifier tail
			pprev, pnext = ds[:ind][-10:], ds[indn:][:10] # get the context in the +- 10
			if '\n' in pprev: pprev = '\n' + pprev.split('\n')[-1] # if there is return do delete the prev of it 
			for c in '\n。':
				if c in pnext: pnext = pnext.split(c)[0] + c # let the pnext
			patts.setdefault(p, []).append( (pprev, pnext, 1) )
			ii = indn # next from the indn
		sm = sum(x[-1] for x in patts[p]) # the sum of the patterns of p
		patts[p] = [(x[0], x[1], x[2]/sm) for x in patts[p]] # normalize the score of a pattern
	return patts

def Hamming(a,b):
	l = max(len(a), len(b), 1)
	return sum(x!=y for x,y in zip(a,b)) / l

def Match(p1, p2, rev=0):
	if rev: 
		p1, p2 = p1[::-1], p2[::-1]
	l = min(len(p1), len(p2))
	z = 0
	for ix in range(l):
		if p1[ix] != p2[ix]: break
		if p1[ix] == '[': z -= 1
		z += 1
	if z < 1: return 0
	return z

	

def Extract(ds, patts):
	n = len(ds) # here is how to do the extract
	ret = []
	xpos = CutSentence(ds) # the xpos of the whole sentence
	for p, ps in patts.items(): # the p and ps for all items
		sm = sum(x[-1] for x in ps) + pattnum * 0.2 #
		pmx = ps[0][-1]
		for pp in ps:
			if pmx > 1 and pp[-1] <= 1: break # error break
			for i in range(1, n): # from the 1 to the length of ds
				if not i in xpos: continue # if the length not in xpos continue
				pprev = ds[:i][-10:]; # if the i is in the xpos, get the prev
				plen = Match(pp[0], pprev, 1); # the matched length
				if plen <= 0: continue # if less then delete
				for j in range(i,min(i+30,n-1)): # for the next phase
					if not (j+1) in xpos: continue # for the pnext
					z = ds[i:j+1]; pnext = ds[j+1:j+1+10] # get Z from pnext from the left of the sentence
					bad = re.search('[\[\]，、；。“”《》由的为而和及（）]', z) is not None
					if bad: continue # there comes some bad patterns
					nlen = Match(pp[1], pnext);  # the matched length
					if plen + nlen > 5 and nlen > 0: # if the len is long
						#sc = (plen+nlen)/(len(pp[0])+len(pp[1]))
						sc = plen / len(pp[0]) * nlen / len(pp[1])
						se = (pp[-1] + 0.2) / sm
						ret.append( (p, z, plen, nlen, pp, se*sc, i) )
	return ret

def ExtractEntity(ent, patts):
	avps, desc = GetDetails(ent)
	ds = MatchAVP(avps, desc)
	#ds = desc;  print(ds)
	rr = []; 
	while True:
		ret = Extract(ds, patts)
		if len(ret) == 0: break
		rr.extend(ret)
        # sort the idx from max to min
		for r in sorted(ret, key=lambda x:-x[-1]):
			ii = r[-1] # the ii is the idx
			ds = ds[:ii] + '[%s]'%r[0] + ds[ii+len(r[1]):] # the new ds is comes to be the 
	#for r in rr: print(r)
	rz = {}
	for x in rr: 
		z = tuple([ent] + list(x[:2]))
		rz[z] = max(rz.get(z, (0,)), (x[-2], x[-3])) # do the if 0 then append
	rr = [tuple(list(x)+[y]) for x,y in ljqpy.FreqDict2List(rz)]
	rr = [x for x in rr if x[-1][0] > 0.01]
	return rr


def GetPatts(ent, newps=[]):
	avps, desc = GetDetails(ent)
	avps += newps
	ds = MatchAVP(avps, desc)
	#print(ds)
	#if '站]个一级学科博士' in ds: print(ent, ds)
	patts = MakePattern(avps, ds)
	return patts


def FindTopK(ent):
	cons = api.GetConcepts(ent)
	rlist = {}
	for c, sc in cons:
		ents = api.GetEntities(c)
		sm = sum([x[1] for x in ents])
		for e, sc1 in ents:
			rlist[e] = rlist.get(e, 0) + sc * sc1 / sm
	rlist.pop(ent)
	rlist = ljqpy.FreqDict2List(rlist)
	#print(rlist)
	return rlist

def GetCommonP(p1, p2):
	plen = Match(p1[0], p2[0], 1)
	nlen = Match(p1[1], p2[1], 0)
	return plen, nlen

def MergePatts(pa1, pa2):
	pret = {p:ps.copy() for p,ps in pa1.items()}
	for p, ps in pa2.items():
		if not p in pret: 
			pret[p] = ps; continue
		newp = {}; vset = {}
		for p1 in pa1[p]: newp[ (p1[0], p1[1]) ] = p1[-1] 
		for p2 in ps:
			vset[ (p2[0], p2[1]) ] = p2[-1]
			for p1 in pa1[p]:
				plen, nlen = GetCommonP(p1, p2)
				if plen >= 1 and nlen >= 1 and plen+nlen > 4:
					z = (p1[0][-plen:], p1[1][:nlen])
					if not z in newp: vset[z] = max(vset.get(z,0), p1[-1]+p2[-1])
					else: vset[z] = p2[-1]
		for z in vset: newp[z] = newp.get(z, 0) + vset[z]
		pret[p] = sorted([(z[0],z[1],sc)for z, sc in newp.items()], key=lambda x:-x[-1]) 	
	#print(pret)
	return pret
		

def Run(ent):
	global pattnum, rlist
	pattnum = 0
	rlist = FindTopK(ent)
	patts = GetPatts(ent)
	#random.shuffle(rlist)
	with open('data/new_triples_%s.txt'%ent, 'w', encoding='utf-8') as fret:
		for e, sc in rlist[:300]:
			rr = ExtractEntity(e, patts)
			for x in rr: 
				print('\t'.join(str(z) for z in x))
				print('\t'.join(str(z) for z in x), file=fret)
            # then output the patterns and refresh it
			newps = [(x[1],x[2]) for x in rr if x[-1][0] > 0.2]
			patts1 = GetPatts(e, newps); pattnum += 1
			patts = MergePatts(patts, patts1)
			with open('data/patterns.txt', 'w', encoding='utf-8') as fout:
				for p, ps in patts.items():
					print(p, file=fout)
					for z in ps: print(z, file=fout) 
		#for e, sc in rlist[:50]:
        #
if __name__ == '__main__':
	#patts = GetPatts('清华大学')
	#ExtractEntity('复旦大学', patts)
	Run('海康威视')
	print('completed %.3f' % time.clock())


