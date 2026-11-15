"""Local-only combined UI + Supervisor server. Do not expose to the internet."""
import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
UI=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from navigator.supervisor import dialog
from navigator.supervisor.run import load_agents

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(UI),**kwargs)
    def log_message(self,format,*args):
        # Avoid logging URLs with user data; local API paths are fixed.
        if self.path.startswith('/api/'): return
        super().log_message(format,*args)
    def respond(self,code,data):
        raw=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if self.path=='/health':return self.respond(200,{'status':'ok','dialog_version':dialog.DIALOG_VERSION})
        return super().do_GET()
    def do_POST(self):
        if self.path not in ('/api/dialog/start','/api/dialog/answer','/api/dialog/confirm'):
            return self.respond(404,{'status':'failed','user_message':'Unknown API path'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>65536:return self.respond(413,{'status':'failed','user_message':'Invalid request size'})
            data=json.loads(self.rfile.read(size).decode())
            if not isinstance(data,dict):raise ValueError('Expected JSON object')
            common={'agents':load_agents(str(ROOT/'agents.json')),'isolate':False,'kb_path':None,'zips_path':None}
            if self.path.endswith('/start'):
                result=dialog.start(story_text=data.get('story_text',''),ref_date=data.get('ref_date'),locale=data.get('locale'),**common)
            elif self.path.endswith('/answer'):
                result=dialog.answer(case=data.get('case'),answers=data.get('answers'),
                                     keep_pending=data.get('keep_pending') is True,**common)
            else:
                result=dialog.confirm(case=data.get('case'),corrections=data.get('corrections'),rejected_need_ids=data.get('rejected_need_ids'),added_needs=data.get('added_needs'),**common)
            return self.respond(200,result)
        except (ValueError,TypeError,UnicodeDecodeError):return self.respond(400,{'status':'failed','user_message':'Invalid request'})
        except Exception:return self.respond(500,{'status':'failed','user_message':'Supervisor error. Please retry.'})

if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Navigator + Supervisor: http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
