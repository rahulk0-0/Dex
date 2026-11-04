#!/usr/bin/env python3
"""Loopback-only DEX bridge. Python 3.10+ and Java 11+. No Python dependencies."""
import base64, hashlib, json, os, pathlib, re, struct, subprocess, tempfile, threading, zlib
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ROOT = pathlib.Path(__file__).resolve().parent
LIMIT = 150 * 1024 * 1024
GATE = threading.BoundedSemaphore(int(os.environ.get('DEX_CONCURRENCY','2')))
ALLOWED = {'https://dex-editor-lite-rahul.nutmegatlas.chatgpt.site'}
API = {35:23,37:25,38:27,39:28}
def run(tool, args):
    result = subprocess.run(['java','-Xmx'+str(int(os.environ.get('DEX_MAX_HEAP_MB','768')))+'m','-cp',str(ROOT/'lib'/'*'),'org.jf.'+tool+'.Main',*args],capture_output=True,text=True,timeout=180)
    if result.returncode or 'error' in result.stderr.lower() or 'exception' in result.stderr.lower():
        raise ValueError((result.stderr or result.stdout or 'Smali operation failed')[:16000])
    return result

def validate(data):
    if len(data)<112 or not re.fullmatch(b'dex\n0[0-9]{2}\x00',data[:8]):raise ValueError('Invalid DEX header. Compact DEX and ODEX are not supported.')
    version=int(data[4:7])
    if version not in API:raise ValueError(f'DEX {version:03d} is unsupported by the bundled Smali 2.5.2 toolchain (supported: 035, 037–039).')
    if struct.unpack_from('<I',data,32)[0]!=len(data):raise ValueError('DEX file size does not match its header.')
    if struct.unpack_from('<I',data,36)[0]!=112 or struct.unpack_from('<I',data,40)[0]!=0x12345678:raise ValueError('Unsupported DEX header size or byte order.')
    if hashlib.sha1(data[32:]).digest()!=data[12:32]:raise ValueError('DEX SHA-1 signature is invalid.')
    if zlib.adler32(data[12:])&0xffffffff!=struct.unpack_from('<I',data,8)[0]:raise ValueError('DEX checksum is invalid.')
    return API[version]

def disassemble(payload):
    data=base64.b64decode(payload['data'],validate=True);api=validate(data)
    with tempfile.TemporaryDirectory(prefix='dex-lite-') as tmp:
        p=pathlib.Path(tmp);(p/'in.dex').write_bytes(data)
        run('baksmali',['d','-a',str(api),'-j','2',str(p/'in.dex'),'-o',str(p/'out')])
        files=[{'name':str(f.relative_to(p/'out')).replace(os.sep,'/'),'text':f.read_text('utf-8')} for f in sorted((p/'out').rglob('*.smali'))]
        if len(files)!=struct.unpack_from('<I',data,96)[0]:raise ValueError('Disassembly was incomplete. No files were imported.')
        return {'files':files,'api':api}

def assemble(payload):
    files=payload['files'];api=int(payload.get('api',28))
    if api not in range(15,31):raise ValueError('API must be between 15 and 30.')
    if not files or len(files)>100000:raise ValueError('No Smali classes or too many classes.')
    with tempfile.TemporaryDirectory(prefix='dex-lite-') as tmp:
        p=pathlib.Path(tmp);src=p/'src';src.mkdir();seen=set()
        for i,f in enumerate(files):
            text=f['text'];match=re.search(r'^\.class\s+.*?\s+(L[^;]+;)',text,re.M)
            if not match:raise ValueError(f'{f["name"]}: missing or invalid .class declaration')
            if match[1] in seen:raise ValueError('Duplicate class: '+match[1])
            seen.add(match[1]);(src/f'{i:06d}.smali').write_text(text,encoding='utf-8')
        result=run('smali',['a','-a',str(api),'-j','2',str(src),'-o',str(p/'out.dex')])
        if result.stderr.strip() or not (p/'out.dex').exists():
            message=result.stderr or result.stdout or 'Assembly failed; no DEX produced.'
            for i,f in enumerate(files):message=message.replace(str(src/f'{i:06d}.smali'),f['name'])
            raise ValueError(message[:16000])
        data=(p/'out.dex').read_bytes();validate(data)
        run('baksmali',['d','-a',str(api),'-j','2',str(p/'out.dex'),'-o',str(p/'verify')])
        if len(list((p/'verify').rglob('*.smali')))!=len(files):raise ValueError('Assembled class count does not match input.')
        return {'data':base64.b64encode(data).decode(),'classes':len(files)}
class Handler(BaseHTTPRequestHandler):
    def origin_ok(self):
        origin=self.headers.get('Origin','')
        return not origin or origin in ALLOWED or bool(re.fullmatch(r'http://(localhost|127\.0\.0\.1)(:\d+)?',origin))
    def cors(self):
        origin=self.headers.get('Origin')
        if origin and self.origin_ok():self.send_header('Access-Control-Allow-Origin',origin)
        self.send_header('Vary','Origin');self.send_header('Access-Control-Allow-Private-Network','true')
    def send_json(self,code,value):
        b=json.dumps(value).encode();self.send_response(code);self.cors();self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_OPTIONS(self):
        if not self.origin_ok():return self.send_json(403,{'error':'Origin not allowed'})
        self.send_response(204);self.cors();self.send_header('Access-Control-Allow-Methods','POST, GET, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type');self.end_headers()
    def do_GET(self):
        if not self.origin_ok():return self.send_json(403,{'error':'Origin not allowed'})
        if self.path=='/health':return self.send_json(200,{'ok':True,'toolchain':'smali/baksmali 2.5.2'})
        from urllib.parse import unquote
        path=(ROOT/'web'/unquote(self.path.split('?')[0]).lstrip('/')).resolve()
        if self.path=='/':path=ROOT/'web'/'index.html'
        if not path.is_relative_to((ROOT/'web').resolve()) or not path.is_file():return self.send_json(404,{'error':'Not found'})
        import mimetypes
        b=path.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(path))[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_POST(self):
        if not self.origin_ok():return self.send_json(403,{'error':'Origin not allowed'})
        if self.headers.get('Content-Type')!='application/json':return self.send_json(415,{'error':'Expected application/json'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<LIMIT:return self.send_json(413,{'error':'Request is empty or exceeds 150 MiB'})
            if self.path not in ('/disassemble','/assemble'):return self.send_json(404,{'error':'Unknown endpoint'})
            if not GATE.acquire(blocking=False):return self.send_json(429,{'error':'Companion is busy. Retry shortly.'})
            try:
                payload=json.loads(self.rfile.read(size));result=(disassemble if self.path=='/disassemble' else assemble)(payload)
            finally:GATE.release()
            self.send_json(200,result)
        except subprocess.TimeoutExpired:self.send_json(422,{'error':'Smali processing exceeded the 180-second limit.'})
        except Exception as e:self.send_json(422,{'error':str(e)[:16000]})
    def log_message(self,*args):pass
if __name__=='__main__':
    if not list((ROOT/'lib').glob('smali-*.jar')):raise SystemExit('Missing bundled toolchain. Run setup.py first.')
    print('DEX Editor Lite companion: http://127.0.0.1:8787\nOpen this URL for the complete local application. Ctrl+C to stop.',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8787),Handler).serve_forever()
