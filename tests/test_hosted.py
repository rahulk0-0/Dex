import unittest
from backend.app import app, ALLOWED
from test_bridge import sample
class Hosted(unittest.TestCase):
 def setUp(self):self.client=app.test_client();self.origin=next(iter(ALLOWED))
 def test_config_uses_same_origin_not_localhost(self):
  self.assertEqual(self.client.get('/dex-config.json').json,{'apiBase':''})
 def test_mobile_and_pc_roundtrip(self):
  assembled=self.client.post('/assemble',json={'files':[{'name':'Phone.smali','text':sample('Phone','Mobile original')}]},headers={'Origin':self.origin,'User-Agent':'Mobile Safari'})
  self.assertEqual(assembled.status_code,200,assembled.json)
  smali=self.client.post('/disassemble',json={'data':assembled.json['data']},headers={'Origin':self.origin,'User-Agent':'Chrome desktop'})
  self.assertEqual(smali.status_code,200,smali.json)
  files=smali.json['files'];files[0]['text']=files[0]['text'].replace('Mobile original','Edited on phone')
  exported=self.client.post('/assemble',json={'files':files},headers={'Origin':self.origin})
  self.assertEqual(exported.status_code,200,exported.json)
  verified=self.client.post('/disassemble',json={'data':exported.json['data']})
  self.assertIn('Edited on phone',verified.json['files'][0]['text'])
 def test_cors_and_invalid_payload(self):
  self.assertEqual(self.client.post('/assemble',json={},headers={'Origin':'https://wrong.example'}).status_code,403)
  self.assertEqual(self.client.post('/assemble',json={}).status_code,422)
  self.assertEqual(self.client.post('/assemble',data='{}',content_type='text/plain').status_code,415)
  preflight=self.client.options('/assemble',headers={'Origin':self.origin,'Access-Control-Request-Headers':'content-type'})
  self.assertEqual(preflight.status_code,204)
  self.assertEqual(preflight.headers['Access-Control-Allow-Origin'],self.origin)
 def test_upload_limit(self):
  original=app.config['MAX_CONTENT_LENGTH'];app.config['MAX_CONTENT_LENGTH']=100
  try:
   response=self.client.post('/assemble',data='{"files":'+(' '*200)+'[]}',content_type='application/json')
   self.assertEqual(response.status_code,413)
  finally:app.config['MAX_CONTENT_LENGTH']=original
 def test_no_file_response_caching(self):
  response=self.client.post('/disassemble',json={'data':'not-base64'})
  self.assertEqual(response.status_code,422)
  self.assertEqual(response.headers['Cache-Control'],'no-store')
if __name__=='__main__':unittest.main()
