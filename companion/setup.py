"""Download pinned open-source runtime jars once. No user files are transmitted."""
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib
ROOT=Path(__file__).resolve().parent/'lib';ROOT.mkdir(exist_ok=True)
ARTIFACTS=[('org.smali','smali','2.5.2'),('org.smali','baksmali','2.5.2'),('org.smali','dexlib2','2.5.2'),('org.smali','util','2.5.2'),('org.antlr','antlr','3.5.2'),('org.antlr','antlr-runtime','3.5.2'),('org.antlr','stringtemplate','3.2.1'),('antlr','antlr','2.7.7'),('com.beust','jcommander','1.64'),('com.google.guava','guava','27.1-android'),('com.google.guava','failureaccess','1.0.1'),('com.google.code.findbugs','jsr305','3.0.2')]
def fetch(a):
    group,name,version=a;file=f'{name}-{version}.jar';p=ROOT/file
    if p.exists():return
    url=f'https://repo.maven.apache.org/maven2/{group.replace(".","/")}/{name}/{version}/{file}'
    with urlopen(url,timeout=60) as r:data=r.read()
    with urlopen(url+'.sha1',timeout=60) as r:expected=r.read().decode().strip().split()[0]
    if hashlib.sha1(data).hexdigest()!=expected:raise ValueError('Download checksum mismatch: '+file)
    p.write_bytes(data);print('Downloaded',file,flush=True)
if __name__=='__main__':
    list(ThreadPoolExecutor(max_workers=6).map(fetch,ARTIFACTS))
    print('Toolchain ready.')
