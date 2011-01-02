import urllib
import urllib2
import gzip
import urlparse
from cStringIO import StringIO
from cookielib import CookieJar

from webob import Request, Response


def decode_response(url_res, data):
    if url_res.headers.get('content-encoding') == 'gzip':
        return gzip.GzipFile(fileobj=StringIO(data)).read()
    return data


def update_query_params(url, params=None):
    if params is None:
        return url
    
    url_s = urlparse.urlsplit(url)
    url_q = urlparse.parse_qs(url_s.query)
    url_q.update(params)
    url_l = list(url_s)
    url_l[3] = urllib.urlencode(url_q)
    return urlparse.urlunsplit(url_l)


def extract_request_cookies(req):
    jar = CookieJar()
    host = urlparse.urlsplit(req.host_url).hostname
    for k, v in req.str_cookies.iteritems():
        yield jar._cookie_from_cookie_tuple(
            (k, v,
             {"domain": host,
              "path": "/"},
             {}), None)

        
class WebProxy(object):
    def __init__(self, opener=None):
        self.cookie_jar = CookieJar()
        self.proxy_handlers = []
        self.local_handlers = []
        self.header_cache = {}
        self.last_headers = {}

        if opener is None:
            opener = urllib2.build_opener()
        self.opener = opener

    def proxify(self, f):
        """
        Add a handler for proxy requests.

        The provided callable will be invoked with the current WebProxy object,
        a webob Request object corresponding to the original request, a urllib2
        Response object with the server's response,
        """
        self.proxy_handlers.append(f)
        return f

    def add_local_handler(self, f):
        """
        Add a handler for local requests.

        The provided callable will be invoked with a urllib2 Request and
        Response object whenever a request is directed to the proxy server.
        """
        self.local_handlers.append(f)
        return f

    def _make_request(self, url_req):
        try:
            url_res = self.opener.open(url_req)
        except urllib2.HTTPError, ex:
            url_res = ex
        self.cookie_jar.extract_cookies(url_res, url_req)
        return url_res
        
    def __call__(self, env, start_response):
        "WSGI entry point."
        if env["PATH_INFO"].startswith("http://"):
            url = urlparse.urlsplit(env["PATH_INFO"])
            env["PATH_INFO"] = url.path
            req = Request(env)

            return self.proxy_request(req, start_response)
        else:
            req = Request(env)
            return self.local_request(req, start_response)

    def local_request(self, req, start_response):
        res = Response()
        for handler in self.local_handlers:
            res = handler(req, res)
            if res:
                return res(req.environ, start_response)
    
        start_response('501 Not Implemented', [])
        return []
    
    def proxy_request(self, req, start_response):
        for cookie in extract_request_cookies(req):
            self.cookie_jar.set_cookie(cookie)
        
        req.headers.pop("Proxy-Connection", None)
        url_req = urllib2.Request(req.url, headers=req.headers)
        if req.body:
            url_req.add_data(req.body)

        self.last_headers = self.header_cache[req.path] = req.headers

        url_res = self._make_request(url_req)

        drop_headers = ['transfer-encoding', 'content-length']
        headers = [(k, v) for k, v in url_res.headers.items()
                   if k not in drop_headers]
        start_response('%s %s' % (url_res.code, url_res.msg),
                       headers)
        data = url_res.read()
        un_data = decode_response(url_res, data)

        for handler in self.proxy_handlers:
            handler(self, req, url_res, un_data)

        return [data]

    def inject(self, url,
               query_params=None, body_params=None, drop_headers=None):
        """
        Issue a request to a given URL that looks like it was made by the
        client being proxied.  The request will re-use headers from previous
        requests and will store any cookies provided in the response.
        """
        drop_headers = drop_headers if drop_headers is not None else \
            ["Referer", "Cookie", "Host", "Content-Type", "Content-Length"]

        headers = dict((k, v) for k, v in (self.header_cache.get(url) or
                                           self.last_headers).iteritems()
                       if k not in drop_headers)

        url = update_query_params(url, query_params)
        url_req = urllib2.Request(url, headers=headers)
        if body_params:
            url_req.add_data(urllib.urlencode(body_params))
        self.cookie_jar.add_cookie_header(url_req)
        return self._make_request(url_req)
