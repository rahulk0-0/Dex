import base64, importlib.util, pathlib, unittest
spec=importlib.util.spec_from_file_location('bridge',pathlib.Path(__file__).parents[1]/'companion'/'server.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
def sample(name,value):
 return f'.class public Ltest/{name};\n.super Ljava/lang/Object;\n.field public static final NAME:Ljava/lang/String; = "{value}"\n.method public static message()Ljava/lang/String;\n .locals 1\n const-string v0, "{value}"\n return-object v0\n.end method\n'
class Roundtrip(unittest.TestCase):
 def test_preserve_classes_and_modify_string(self):
  first=[{'name':n+'.smali','text':sample(n,n)} for n in ['First','Untouched']]
  a=bridge.assemble({'files':first,'api':28});d=bridge.disassemble({'data':a['data']})
  unchanged=next(f['text'] for f in d['files'] if 'Untouched;' in f['text'])
  for f in d['files']:
   if 'First;' in f['text']:f['text']=f['text'].replace('"First"','"Longer replacement string"')
  b=bridge.assemble({'files':d['files'],'api':28});out=bridge.disassemble({'data':b['data']})
  self.assertEqual(len(out['files']),2)
  self.assertEqual(next(f['text'] for f in out['files'] if 'Untouched;' in f['text']),unchanged)
  self.assertIn('Longer replacement string',''.join(f['text'] for f in out['files']))
 def test_invalid_instruction_has_line_error(self):
  with self.assertRaisesRegex(ValueError,r'broken.smali.*\['):bridge.assemble({'files':[{'name':'broken.smali','text':sample('Broken','x').replace('return-object v0','bad-instruction v0')}],'api':28})
 def test_duplicate_class_rejected(self):
  with self.assertRaisesRegex(ValueError,'Duplicate class'):bridge.assemble({'files':[{'name':'a.smali','text':sample('Same','x')}]*2})
 def test_corrupted_dex_rejected(self):
  a=bridge.assemble({'files':[{'name':'x.smali','text':sample('X','x')}]});data=bytearray(base64.b64decode(a['data']));data[-1]^=1
  with self.assertRaisesRegex(ValueError,'signature'):bridge.disassemble({'data':base64.b64encode(data).decode()})
if __name__=='__main__':unittest.main()
