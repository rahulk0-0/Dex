"""Production HTTP adapter for the shared, tested Smali conversion functions."""
import os, pathlib, subprocess
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from companion.server import assemble, disassemble, GATE
ROOT=pathlib.Path(__file__).resolve().parents[1]
WEB=pathlib.Path(os.environ.get('DEX_WEB_ROOT',str(ROOT/'companion'/'web')))
ALLOWED={x.strip().rstrip('/') for x in os.environ.get('ALLOWED_ORIGINS','https://dex-editor-lite-rahul.nutmegatlas.chatgpt.site').split(',') if x.strip()}
if os.environ.get('RENDER_EXTERNAL_URL'):ALLOWED.add(os.environ['RENDER_EXTERNAL_URL'].rstrip('/'))
app=Flask(__name__,static_folder=None)
app.config['MAX_CONTENT_LENGTH']=int(os.environ.get('MAX_REQUEST_MB','32'))*1024*1024
@app.before_request
def check_origin():
    origin=request.headers.get('Origin','').rstrip('/')
    if origin and origin not in ALLOWED:return jsonify(error='Origin not allowed'),403
@app.after_request
def headers(response):
    origin=request.headers.get('Origin','').rstrip('/')
    if origin in ALLOWED:
        response.headers['Access-Control-Allow-Origin']=origin
        response.headers['Vary']='Origin'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    if request.path in ('/assemble','/disassemble','/health','/dex-config.json'):
        response.headers['Cache-Control']='no-store'
    return response
@app.route('/health')
def health():return jsonify(ok=True,toolchain='smali/baksmali 2.5.2',mode='hosted',maxRequestMiB=app.config['MAX_CONTENT_LENGTH']//(1024*1024))
@app.route('/dex-config.json')
def config():return jsonify(apiBase='')
@app.route('/<operation>',methods=['POST','OPTIONS'])
def convert(operation):
    if operation not in ('assemble','disassemble'):return jsonify(error='Unknown endpoint'),404
    if request.method=='OPTIONS':
        response=app.make_response(('',204));response.headers['Access-Control-Allow-Methods']='POST, OPTIONS';response.headers['Access-Control-Allow-Headers']='Content-Type';return response
    if not request.is_json:return jsonify(error='Expected application/json'),415
    if not GATE.acquire(blocking=False):
        response=jsonify(error='The DEX server is busy. Try again shortly.');response.headers['Retry-After']='5';return response,429
    try:
        payload=request.get_json()
        if not isinstance(payload,dict):return jsonify(error='Expected a JSON object'),400
        return jsonify((assemble if operation=='assemble' else disassemble)(payload))
    except subprocess.TimeoutExpired:return jsonify(error='Smali processing exceeded the 180-second limit.'),422
    except HTTPException:raise
    except (ValueError,KeyError,TypeError,UnicodeError) as error:return jsonify(error=str(error)[:16000]),422
    except Exception:return jsonify(error='DEX conversion failed on the server. No output was exported.'),500
    finally:GATE.release()
@app.errorhandler(HTTPException)
def http_error(error):return jsonify(error=error.description),error.code
@app.route('/')
def index():return send_from_directory(WEB,'index.html')
@app.route('/<path:asset>')
def assets(asset):return send_from_directory(WEB,asset)
