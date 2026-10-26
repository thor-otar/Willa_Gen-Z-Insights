import json, re
ins=[]
for line in open("insights_raw.txt"):
    p=line.rstrip("\n").split("~")
    if len(p)!=7: print("BAD",p[:2]); continue
    i,h,f,n,s,y,t=p
    ins.append(dict(id=f"I{int(i):03d}",headline=h,finding=f.replace("see I103","see I101"),number=n,source=s,year=int(y),theme=t))
A_src=("Pew","Deloitte","Attest","Piper Sandler","ThredUp","GWI","Mastercard","YouGov","TGM Research")
C_ids={15,16,17,38,40,41,48,49,50,51,52,53,56,57,58,59,70,71,75,76,77,98,99,100}
flags={
 5:"All US adults, not Gen Z only.",6:"All US adults, not Gen Z only.",7:"All US adults, not Gen Z only.",9:"All US women, not Gen Z only.",
 8:"Ages 18–29: overlaps Gen Z but isn't the same cohort.",10:"Ages 18–29: overlaps Gen Z but isn't the same cohort.",
 34:"Global sample, includes Gen Alpha.",63:"APAC sample, not US.",91:"Global internet users, all ages.",92:"Global internet users, all ages.",
 94:"All community visitors, not Gen Z only.",95:"All forum visitors, not Gen Z only.",79:"All consumers, not Gen Z only.",
 83:"All TikTok shoppers, not Gen Z only.",84:"All TikTok users, not Gen Z only.",86:"All US TikTok users, not Gen Z only.",90:"All TikTok users, not Gen Z only.",
 43:"Dated (2021).",45:"Dated (2022) and survey details unclear.",46:"Dated (2022). Your reports restate this as 'content must expose the dark side', which the source does not say.",
 47:"Dated (2022). Your reports label this 'primary research'; it is a trade-press figure.",56:"Dated (2022) estimate.",57:"Dated (2022); a taxonomy, not a measurement.",
 54:"Dated (2023).",55:"Dated (2023).",75:"Dated (2022).",76:"Dated (2022); '100% of participants' implies a very small sample.",77:"Dated (2022); sample unclear.",
 87:"Check before use: 81% of TikTok Shop US volume in beauty looks high against other reporting.",
 89:"Often misquoted as '3.2x higher conversion rates' (your formats report does this). The source says Gen Z is 3.2x more likely to buy via TikTok Shop.",
 50:"Your trend report cites 60% for this; the source line says 37%.",
 96:"Your trend report restates this as 'trust anonymous consensus over expert reviews'; the source says 'nearly as much as traditional news'.",
 64:"Your reports attribute the UGG jump to different causes (anti-AI campaign vs. repositioning). Treat the cause as unconfirmed.",
 100:"Circular: sourced to a NotebookLM-generated report, not an original source. Verify before use.",
 15:"Blog source; original survey not identified.",16:"Blog source; original survey not identified.",17:"Blog source; original survey not identified.",
 98:"Blog source; original survey not identified.",99:"Blog source; original survey not identified.",
 12:"Low relevance to a bag brand.",13:"Low relevance to a bag brand.",14:"Low relevance to a bag brand.",
}
for x in ins:
    n=int(x["id"][1:])
    x["quality"]="A" if any(a in x["source"] for a in A_src) else ("C" if n in C_ids else "B")
    if n==100: x["quality"]="C"
    if n in flags: x["flag"]=flags[n]
prop=[
 ("P01","Vera Bradley invisible in college long-form","Across 81 unbranded college-backpack YouTube videos from the past 12 months (~8.4M views), Vera Bradley appeared in 0 titles; college backpack Shorts reach 1–7M views.","0 of 81","COBRA YouTube sampling test (single coder, directional)",2026,"social"),
 ("P02","Mother-daughter is implicit, not searched","Explicit 'mother daughter bag' searches return almost nothing, but inheritance themes are strong in Shorts (one 'once a VB girl, always a VB girl' Short ~1M views).","~1M views","COBRA YouTube sampling test (single coder, directional)",2026,"trends"),
 ("P03","Comments center on inheritance, durability and resale","In ~100 comments on 7 VB Shorts: ~10 inheritance/family, ~9 durability, ~8 thrift/resale, ~7 'it never left / comeback'.","~100 comments","COBRA YouTube sampling test (single coder, directional)",2026,"values"),
 ("P04","Older loyalists criticise rebrand and quality","In 116 comments on 10 VB long-form videos, ~30 were negative on rebrand/quality and ~17 preferred vintage or secondhand.","~30 of 116","COBRA YouTube sampling test (single coder, directional)",2026,"fashion"),
]
for i,h,f,n,s,y,t in prop:
    ins.append(dict(id=i,headline=h,finding=f,number=n,source=s,year=y,theme=t,quality="P",flag="Own small sample: directional only, not representative."))

import os
if os.path.exists("client_raw.txt"):
    for line in open("client_raw.txt"):
        if not line.strip() or line.startswith("#"): continue
        i,h,f,n,method,y,t=line.rstrip("\n").split("~")
        ins.append(dict(id=i,headline=h,finding=f,number=n,source="Vera Bradley first-party: "+method,year=int(y),theme=t,quality="V"))
md=open("formats-touchpoints-report.md").read()
s1=md.split("# SECTION 1")[1].split("# SECTION 2")[0]; s2=md.split("# SECTION 2")[1].split("# SECTION 3")[0]
def parse(sec,prefix):
    out=[];cat=""
    for line in sec.splitlines():
        m=re.match(r"### [A-E]\. (.+?) \(",line)
        if m: cat=m.group(1)
        m=re.match(r"(\d+)\. \*\*(.+?)\*\*: (.+)",line)
        if m: out.append(dict(id=f"{prefix}{int(m.group(1)):02d}",name=m.group(2),desc=m.group(3).strip(),category=cat))
    return out
F=parse(s1,"F"); T=parse(s2,"T")
assert len(F)==50 and len(T)==50, (len(F),len(T))
low={17,18,21,23,24,25,26,27,28,29,30}
for t in T:
    if int(t["id"][1:]) in low: t["vb_fit"]="low"
metrics={2:("Watch time & shares"),1:("Watch time & shares"),8:"In-app conversions",4:"Saves & instant buys",9:"Creator trust & comment volume",11:"Sticker tap rate",17:"Filter usage & shares",20:"Claim rate & play time",22:"Average duration",23:"User video creations",19:"Peak live listeners",31:"Save rate & reposts",32:"Upvote ratio & comment depth",37:"Saves",14:"GMV",42:"Viewer retention",43:"Loyalty & community sentiment",45:"Engagement-to-impression ratio"}
for f in F:
    n=int(f["id"][1:])
    if n in metrics: f["metric"]=metrics[n]
fit_src="""1:1,2,3,8|4,6,9,10
2:1,2,3|4,6,8,31,34
3:5,6|7,10,20,44,9,12
4:1,2,31|3,4,34,8
5:1,2,3|5,7,4,8
6:1,2,3,8|12,15,16,19,20,44
7:1,2,3|5,7,32,4,31,34,37
8:1,3,31|2,4,14
9:1,3|2,4,14,20
10:1,2,3|8
11:6,9|13,11,5,40
12:1|2,3
13:1,2|3,8,46,47,48
14:31|34,21,6
15:6,40|45,11,50,14
16:1,2|3,14,20
17:9|1,6,40,49,50
18:6,9|10,13
19:11,24|21
20:22|23,29,28,30
21:41,42|3,13,43
22:4,41|42,3,2
23:1,2|3,8
24:4,25|41,21
25:1,2,3|4,8,13
26:13|11,16,17,12
27:4,41|1
28:1,2|4,41,44
29:41,4|1,42,14
30:11,24|20,21
31:5|1,7,20,44,45
32:14|11,20
33:1,3|5,44,14
34:1,3|4,2
35:43|44,45,11,46
36:5,7|20,43
37:1,4|3,14
38:1,2|5,7,44,3
39:1,2,7|3,5
40:1,4|3,14
41:1,2|3,8
42:4|43,41
43:4,1|2,3,43,13
44:4|2,3,41
45:1,2|3,8,20
46:1,2,3|7,44,5
47:4|1,22
48:1,2|14,44,13
49:1,2,3|4,49
50:5,1|44,11,7,39,2"""
fit={}
for line in fit_src.splitlines():
    k,v=line.split(":");a,b=v.split("|")
    fit[f"F{int(k):02d}"]={"native":[f"T{int(x):02d}" for x in a.split(",")],"workable":[f"T{int(x):02d}" for x in b.split(",")]}
nn=sum(len(v["native"]) for v in fit.values()); nw=sum(len(v["workable"]) for v in fit.values())
print("insights",len(ins),"native",nn,"workable",nw)
lib=dict(insights=ins,formats=F,touchpoints=T,fit=fit,meta=dict(compiled="2026-10-26",note="Library v0. Insights from NotebookLM extraction of 36 sources plus 3 verified ThredUp additions and 4 COBRA proprietary sample points. Fit matrix is a draft by Claude for Thor's review."))
json.dump(lib,open("library.json","w"),ensure_ascii=False,indent=1)
# compact knowledge text for the model
L=[]
L.append("=== INSIGHT LIBRARY ===\nQuality: A = primary research org; B = trade press, agency or case study; C = blog, unclear origin or circular; P = COBRA's own small sample (directional); V = Vera Bradley first-party data (confidential).")
for x in ins:
    L.append(f"{x['id']} [{x['quality']}] ({x['year']}, {x['theme']}) {x['headline']}: {x['finding']} | {x['number']} | {x['source']}"+(f" | FLAG: {x['flag']}" if x.get('flag') else ""))
L.append("\n=== CONTENT FORMATS ===")
for f in F: L.append(f"{f['id']} {f['name']} ({f['category']}): {f['desc']}"+(f" | metric: {f['metric']}" if f.get('metric') else ""))
L.append("\n=== TOUCHPOINTS ===")
for t in T: L.append(f"{t['id']} {t['name']} ({t['category']}): {t['desc']}"+(" | LOW FIT FOR VERA BRADLEY (Claude's judgement)" if t.get('vb_fit') else ""))
L.append("\n=== CARRIER FIT MATRIX (draft, pending Thor's review) ===\nnative = the format's home; workable = can work with adaptation. Any pair not listed is not a recommended carrier.")
for k,v in fit.items(): L.append(f"{k}: native {','.join(v['native'])}; workable {','.join(v['workable'])}")
open("knowledge_data.txt","w").write("\n".join(L))
print(len("\n".join(L)))
