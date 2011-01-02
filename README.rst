=========================================================
Proxifer - Easily write application-specific HTTP proxies
=========================================================

:Version: 0.1

Proxifier is a limited, but easy to use, tool for writing
application-specific web proxies.  It makes it very easy to observe an
in-progress HTTP session and to programatically inject new requests
into the stream.  It does not currently support SSL or response
modification.

Proxifier is mostly useful for scripting user sessions on sites that
require a login, make significant use of javascript, and don't provide
an API.


Example
-------

This is a proxy which will automatically download article photos while
you browse the New York Times website.  Note that the download process
doesn't interrupt normal browsing and that requests to download photos
will use the same headers and cookies from the browser session.::

   from gevent import monkey; monkey.patch_all()
   from gevent import wsgi, spawn
   from gevent.queue import JoinableQueue
    
   import re
   from proxifier import WebProxy
    
   image_q = JoinableQueue()
   def downloader(proxy):
       while True:
           proxy, url = image_q.get()
           urllib_res = proxy.inject(url)
    
           f = open(re.sub(r'[^a-zA-Z0-9]', '-', url), 'w')
           f.write(urllib_res.read())
           f.close()
   spawn(image_downloader)
           
   def proxy_handler(proxy, req, res, data):
       for url in re.findall(r'src="(http://[^"]+/20\d\d/[^"]+.jpg)"', data):
           image_q.put((proxy, url))
    
   proxy = WebProxy()
   proxy.proxify(proxy_handler)

   print "Proxying on port 8085"
   wsgi.WSGIServer(('', 8085), proxy).serve_forever()
