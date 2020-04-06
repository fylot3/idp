# apiserver.py - wrappers over HTTPServer implementing JSON based queries
#   updated to handle binary content also

# Community code (with some updates):
# https://gist.github.com/earonesty/ab07b4c0fea2c226e75b3d538cc0dc55

import sys, json
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import threading
import logging
log = logging.getLogger(__name__)

class ApiError(Exception):
    def __init__(self, code, msg=None, desc=None):
        self.code = code
        self.msg = msg
        self.desc = desc

    def __str__(self):
        return f"ApiError({self.code}, {self.msg})"

def ApiRoute(path):
    def outer(func):
        if not hasattr(func, "_routes"):
            setattr(func, "_routes", [])
        func._routes += [path]
        return func
    return outer

class ApiServer(HTTPServer):
    def __init__(self, addr, port):
        """
        Create a new server on address, port.  Port can be zero.

        from apiserver import ApiServer, ApiError, ApiRoute

        Create your handlers by inheriting from ApiServer and tagging them with @ApiRoute("/path").

        Alternately you can use the ApiServer() directly, and call add_handler("path", function)

        Raise errors by raising ApiError(code, message, description=None)

        Return responses by simply returning a dict() or str() object

        Parameter to handlers is a dict()

        Query arguments are shoved into the dict via urllib.parse_qs

        """
        server_address = (addr, port)
        self.__addr = addr

        # instead of attempting multiple inheritence

        # shim class that is an ApiHandler
        class handler_class(ApiHandler):
            pass

        self.handler_class = handler_class

        # routed methods map into handler
        for meth in type(self).__dict__.values():
            if hasattr(meth, "_routes"):
                for route in meth._routes:
                    self.add_route(route, meth)

        super().__init__(server_address, handler_class)

    def add_route(self, path, meth):
        self.handler_class._routes[path] = meth
        
    def port(self):
        "Get my port"
        sa = self.socket.getsockname()
        return sa[1]

    def address(self):
        "Get my ip address"
        sa = self.socket.getsockname()
        return sa[0]

    def uri(self, path):
        "Make a URI pointing at myself"
        if path[0] == "/":
            path = path[1:]
        return "http://"+self.__addr + ":"+ str(self.port()) + "/" + path

    def shutdown(self):
        super().shutdown()
        self.socket.close()

class ApiHandler(BaseHTTPRequestHandler):
    _routes={}

    def parse_binary_params(self, content):
        params = content.decode("utf-8").split('&')
        params_dict = {}
        for p in params:
            ps = p.split('=')
            params_dict[ps[0]] = ps[1]
        return params_dict

    def do_GET(self):
        self.do_XXX()

    def do_POST(self):
        content="{}"
        if self.headers["Content-Length"]:
            length = int(self.headers["Content-Length"])
            content=self.rfile.read(length)

        info=None
        if content:
            try:
                # JSON api
                info = json.loads(content)
            except:
                # Raw binary
                info = self.parse_binary_params(content)
                #raise ApiError(400, "Invalid JSON", content)
        self.do_XXX(info)

    def do_XXX(self, info={}):
        try:
            url=urlparse.urlparse(self.path)

            handler = self._routes.get(url.path)

            if url.query:
                params = urlparse.parse_qs(url.query)
            else:
                params = {}

            info.update(params)

            if handler:
                try:
                    response=handler(info)
                    self.send_response(200)
                    if response is None:
                        response = ""
                    if type(response) is dict:
                        response = json.dumps(response)
                    response = bytes(str(response),"utf-8")
                    self.send_header("Content-Length", len(response))
                    self.end_headers()
                    self.wfile.write(response)
                except ApiError:
                    raise
                except ConnectionAbortedError as e:
                    log.error(f"GET {self.path} : {e}")
                except Exception as e:
                    raise ApiError(500, str(e))
            else:
                raise ApiError(404)
        except ApiError as e:
            try:
                self.send_error(e.code, e.msg, e.desc)
            except ConnectionAbortedError as e:
                log.error(f"GET {self.path} : {e}")
