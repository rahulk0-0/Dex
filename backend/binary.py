"""Bounded-memory binary import: disk-backed input/output, compressed Smali transfer."""
import mmap, pathlib, struct, tempfile, zipfile
from flask import request, jsonify, send_file
from companion.server import validate, run, GATE

def disassemble_binary():
    if request.method=='OPTIONS':
        response=jsonify();response.status_code=204
        response.headers['Access-Control-Allow-Methods']='POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers']='Content-Type'
        return response
    if request.mimetype!='application/octet-stream':return jsonify(error='Expected application/octet-stream'),415
    if not GATE.acquire(blocking=False):return jsonify(error='The DEX server is busy. Try again shortly.'),429
    temp=tempfile.TemporaryDirectory(prefix='dex-binary-');path=pathlib.Path(temp.name)
    try:
        source=path/'input.dex'
        with source.open('wb') as out:
            while True:
                chunk=request.stream.read(256*1024)
                if not chunk:break
                out.write(chunk)
        if source.stat().st_size<112:raise ValueError('Invalid or empty DEX file.')
        with source.open('rb') as file, mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
            api=validate(data);expected=struct.unpack_from('<I',data,96)[0]
        output=path/'classes'
        run('baksmali',['d','-a',str(api),'-j','1',str(source),'-o',str(output)])
        archive=path/'classes.zip';count=0
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as zipped:
            for file in output.rglob('*.smali'):
                zipped.write(file,file.relative_to(output).as_posix());count+=1
            if count!=expected:raise ValueError('Disassembly was incomplete. No files were imported.')
            zipped.writestr('_dex_api.txt',str(api))
        response=send_file(archive,mimetype='application/zip',as_attachment=True,download_name='classes.zip')
        response.direct_passthrough=False
        response.call_on_close(temp.cleanup)
        response.headers['Cache-Control']='no-store'
        return response
    except BaseException:
        temp.cleanup();raise
    finally:GATE.release()
