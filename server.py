from http.server import BaseHTTPRequestHandler, HTTPServer #s
import urllib.parse as urlparse
import os #operating system
import mysql.connector #database application 
from oauthlib.oauth2 import WebApplicationClient #google login connaction

# MySQL Configuration
mysql_config = {
    'host': '3306',
    'user': 'root',
    'password': 'root',
    'database': 'listsyncdb'
}

# -------------------command center---------------------
class MyHandler(BaseHTTPRequestHandler):

    # simplify sending HTTP responses
    def _send_response(self, content, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(content)


    #-----GET--sends server the info-------------
    def do_GET(self):

        # main/welcome page 
        if self.path == '/welcome':
            with open('templates/index.html', 'rb') as file:
                self._send_response(file.read())
        
        # login page
        elif self.path == 'templates/login':
            with open('templates/login.html', 'rb') as file:
                self._send_response(file.read())


        # logged in page - shows the user private/public lists.
        # 
        elif self.path == 'templates/loggedinpage':
            with open('loggedinpage.html', 'r') as file:
                content = file.read()
        elif self.path.startswith('/static/'):
            file_path = self.path.lstrip('/')
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    content_type = 'text/html'
                    if file_path.endswith('.png'):
                        content_type = 'image/png'
                    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                        content_type = 'image/jpeg'
                    self._send_response(file.read(), content_type=content_type)
            else:
                self.send_error(404, 'File Not Found')
        else:
            self.send_error(404, 'File Not Found')

                



# ----POST--------inputs info the databases and such --------------
    def do_POST(self):
        # welcome page - just a show case
        if self.path == '/welcome':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = urlparse.parse_qs(post_data.decode('utf-8'))
            email = post_data.get('email', [''])[0]
            password = post_data.get('password', [''])[0]

        # login - log into ur user with an email and password
        if self.path == '/login':
         with open('login.html', 'r') as file:
                content = file.read()

        # register - post name email and password into the database
        if self.path == '/register':
            with open('register.html', 'r') as file:
                content = file.read()

        # logged in page - shows
        if self.path == '/loggedinpage':
            with open('loggedinpage.html', 'r') as file:
                content = file.read()
                
    
#start server and such
def run(server_class=HTTPServer, handler_class=MyHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()
if __name__ == '__main__':
    run()
