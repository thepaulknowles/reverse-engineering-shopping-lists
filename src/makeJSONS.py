import re
import json
import os

def pos_float(s):
    #print (s)
    if s[-1]=="-":
        return -float(s[:-1])
    elif s[-1]=='+':
        return float(s[:-1])
    else:
        return float(s)

def parse_entry(entry):
    header_re = r"\s+DATE\s+TIME\s+TERM\s+TRANS\s+OPER\s+GROSS\+\s+GROSS-\s+NET\s+TRAN TYPE\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
    match = re.search(header_re, entry)
    if match is None:
        return None
    transinfo = match.groups()
    if transinfo[8]!='Checkout':
        return None
    item_re = r"^ (\w+)?\s+([\w \-,\+.'\"\\\/%&]+?)\s+(\d+\.\d+-?)\s+\w?\s+Dept\s+(\d+)"
    items = re.findall( item_re, entry, flags=re.MULTILINE )
    
    account_re = r"\s[Account]+\s+\d+$"
    account = re.findall(account_re,entry,flags=re.MULTILINE )
    
    ret = {'date':transinfo[0],
           'time':transinfo[1],
           'term':int(transinfo[2]),
           'trans':int(transinfo[3]),
           'oper':int(transinfo[4]),
           'gross+':pos_float(transinfo[5]),
           'gross-':pos_float(transinfo[6]),
           'net':pos_float(transinfo[7]),
           'type':transinfo[8],
          'account':account}
    #[[d[-4:] for d in account]]
    items = [(x[0].strip(), x[1].strip(), pos_float(x[2]), int(x[3])) for x in items]
    
    ret['items'] = items
    
    return ret

def parse_transaction_file(fn):
    raw = open(fn, encoding="latin1").read()
    
    
    # remove page headers
    headerre = re.compile( r" +Auto Report: (\b.*)\s+Entry: (\b.*)\s+TRANSACTION SUMMARY LOG REPORT  - STORE\s+(.+)\s+PREVIOUS PERIOD - (\S+)\s+Reported at:\s+(\S+ \S+)\s+",
                     flags=re.MULTILINE)
    headerless, ct = re.subn(headerre, "", raw)
    
    # remove page footers
    pageless, ct = re.subn(r'\n +Page \d+.*\n', "\n", headerless)
    
    # split at ======
    entries = re.split(r"\n=+\n", pageless)
    
    trans = []
    for i, entry in enumerate( entries ):
        x = parse_entry(entry)
        if x is not None: trans.append(x)
            
    return trans

def pos_to_json(fn_in, fn_out):
    trns = parse_transaction_file(fn_in)
    
    fpout = open(fn_out,"w")
    for trn in trns:
        fpout.write( json.dumps(trn) )
        fpout.write("\n")
    fpout.close()



for subdir, dirs, files in os.walk('./tlogs'):
    for file in files:
        #print os.path.join(subdir, file)
        filepath = subdir + os.sep + file

        if filepath.endswith("*log.txt"):
            pass
            #print (filepath)


#if __name__ == '__main__':
year=input('What year data would you like to process?')
json_path ='./data/jsons/%s'% year
tlog_path='./data/tlogs/%s'% year

if not os.path.exists(tlog_path):
    print("Directory " , tlog_path ,  "Does not exist")
if not os.path.exists(json_path):
    os.makedirs(json_path)
    print("Directory " , json_path ,  " Created ")
else:    
    print("Directory " , json_path ,  " already exists")    


for i,f in enumerate(os.walk(tlog_path)):
    #print (i,f)
    for ff in f:
        
        #print("ff:",ff)
        if type(ff)!='list':
            if str(ff).startswith(tlog_path):
                path = ff
        for fff in ff:
            #print("fff:",fff)
            if fff=="transactionlog.txt":
                #print(path+'/'+fff)
                #print (json_path+'/'+'%d.json'%i)
                pos_to_json(path+'/'+fff,json_path+'/'+'%d.json'%i)