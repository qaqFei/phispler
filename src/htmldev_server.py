import fix_workpath as _

from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try: content, code = open(index_page if self.path == "/" else self.path[1:], "rb").read(), 200
        except FileNotFoundError: content, code = b"404 Not Found", 404
        self.send_response(code)
        self.send_header("content-type", "text/html;charset=utf-8")
        self.end_headers()
        self.wfile.write(content)

httpd = HTTPServer(("", 8000), SimpleHTTPRequestHandler)
index_page = input("Enter the name of the index page: ")
print("Serving at port 8000...")
httpd.serve_forever()
