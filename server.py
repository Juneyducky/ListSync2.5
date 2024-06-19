from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie

import datetime
import os
import urllib.parse as urlparse

import bcrypt

import mysql.connector 
from mysql.connector import errorcode

from jinja2 import FileSystemLoader, Environment
from multipart import MultipartParser
from werkzeug.http import parse_options_header



# MySQL Configuration
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'listsyncdb'
}


def get_user_id_from_cookies(headers):
    if "Cookie" in headers:
        cookie = SimpleCookie(headers["Cookie"])
        if "user_id" in cookie:
            return cookie["user_id"].value
    return None

# -------------------command center---------------------
class MyHandler(BaseHTTPRequestHandler):
    global env
    env = Environment(loader=FileSystemLoader('templates'))
    
    # Simplify sending HTTP responses
    def _send_response(self, content, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(content.encode() if isinstance(content, str) else content)

    # to change the url path
    def _redirect(self, path):
        self.send_response(302)
        self.send_header('Location', path)
        self.end_headers()

    def _set_logged_user_cookie(self, user_id):
        user_id_cookie = SimpleCookie()
        user_id_cookie['user_id'] = user_id

        self.send_header('Set-Cookie', user_id_cookie.output(header=''))
        self.end_headers()

    #-----GET--sends the server the info-------------
    def do_GET(self):
            if self.path == '/':
                with open('templates/index.html', 'rb') as file:
                    self._send_response(file.read())
            elif self.path == '/login.html':
                with open('templates/login.html', 'rb') as file:
                    self._send_response(file.read())
            elif self.path == '/register.html':
                with open('templates/register.html', 'rb') as file:
                    self._send_response(file.read())          
            elif self.path == '/loggedinpage':
                current_user_id = get_user_id_from_cookies(self.headers)
                if not current_user_id:
                    self._send_response("Unauthorized - User not logged in", content_type='text/html')
                    return

                try:
                    conn = mysql.connector.connect(**mysql_config)
                    cursor = conn.cursor()
                    query = "SELECT list_name, type FROM lists WHERE user_id = %s"
                    cursor.execute(query, (current_user_id,))
                    result = cursor.fetchall()
                    private_list = [item[0] for item in result if item[1] == "private"]
                    public_list = [item[0] for item in result if item[1] == "public"]
                    print(private_list, public_list)
                except mysql.connector.Error as err:
                    self._send_response(f"Error: {err}")
                finally:
                    cursor.close()
                    conn.close()

                template = env.get_template('loggedinpage.html')
                rendered_template = template.render(private_list=private_list, public_list = public_list)
                self._send_response(rendered_template.encode())

# ///////////////////////////////////////////////////////////////////

            elif self.path.startswith("/list"):
                list_name = self.path.split("_")[1]
                
                template = env.get_template("list.html")
                rendered_template = template.render(list_name=list_name)
                self._send_response(rendered_template.encode())

            elif self.path == '/additem.html':
                if not current_user_id:
                    self._send_response("Unauthorized - User not logged in", content_type='text/html')
                    return

                try:
                    conn = mysql.connector.connect(**mysql_config)
                    cursor = conn.cursor()
                    query = "SELECT list_name, type FROM lists WHERE user_id = %s"
                    cursor.execute(query, (current_user_id,))
                    result = cursor.fetchall()
                    private_list = [item[0] for item in result if item[1] == "private"]
                    public_list = [item[0] for item in result if item[1] == "public"]
                    print(private_list, public_list)
                except mysql.connector.Error as err:
                    self._send_response(f"Error: {err}")
                finally:
                    cursor.close()
                    conn.close()

                template = env.get_template('loggedinpage.html')
                rendered_template = template.render(private_list=private_list, public_list = public_list)
                self._send_response(rendered_template.encode())

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
        if self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = urlparse.parse_qs(post_data.decode('utf-8'))
            email = post_data.get('email', [''])[0]
            password = post_data.get('password', [''])[0]


            try:
                conn = mysql.connector.connect(**mysql_config)
                cursor = conn.cursor()

                query = "SELECT user_id, password_hash FROM users WHERE email = %s"
                cursor.execute(query, (email,))
                user_id, password_hash = cursor.fetchone()

                if password_hash and bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    update_query = "UPDATE users SET last_login = %s WHERE email = %s"
                    cursor.execute(update_query, (datetime.datetime.now(), email))
                    conn.commit()
                    
                    # Create a cookie
                    cookie = SimpleCookie()
                    cookie['user_id'] = str(user_id)

                    # Set the cookie in the response
                    self.send_response(302)  # Redirect response
                    self.send_header('Location', '/loggedinpage')
                    self.send_header('Set-Cookie', cookie.output(header=''))
                    self.end_headers()
                else:
                    self._send_response("Invalid email or password")

            except mysql.connector.Error as err:
                self._send_response(f"Error: {err}")
            finally:
                cursor.close()
                conn.close()
  
        elif self.path == '/register':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = urlparse.parse_qs(post_data.decode('utf-8'))
            name = post_data.get('name', [''])[0]
            email = post_data.get('email', [''])[0]
            password = post_data.get('password', [''])[0]

            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            try:
                conn = mysql.connector.connect(**mysql_config)
                cursor = conn.cursor()

                query = "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, password_hash, email))
                conn.commit()
                self._redirect('/loggedinpage')

            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    self._send_response("Something is wrong with your user name or password")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    self._send_response("Database does not exist")
                else:
                    self._send_response(err)
            finally:
                cursor.close()
                conn.close()

        elif self.path == '/addlist':
            current_user_id = get_user_id_from_cookies(self.headers)
            if not current_user_id:
                self._send_response("Unauthorized - User not logged in", content_type='text/html')
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = urlparse.parse_qs(post_data.decode('utf-8'))
            list_name = post_data.get('list_name', [''])[0]
            description = post_data.get('description', [''])[0]
            list_type = post_data.get('type', [''])[0]

            try:
                conn = mysql.connector.connect(**mysql_config)
                cursor = conn.cursor()
                query = "INSERT INTO lists (list_name, description, type, user_id) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (list_name, description, list_type, current_user_id))
                conn.commit()
                self._redirect(f'/list_{list_name}')
            except mysql.connector.Error as err:
                self._send_response(f"Error: {err}")
            finally:
                cursor.close()
                conn.close()
# ------------------------

        elif self.path == '/additem':
            current_user_id = get_user_id_from_cookies(self.headers)
            if not current_user_id:
                self._send_response("Unauthorized - User not logged in")
                return

            content_type, pdict = parse_options_header(self.headers['Content-Type'])
            if content_type == 'multipart/form-data':
                boundary = pdict['boundary'].encode('utf-8')
                content_length = int(self.headers['Content-Length'])
                parser = MultipartParser(self.rfile, boundary, content_length)
                
                form_data = {}
                file_data = None
                
                for part in parser:
                    if part.name == 'item_name':
                        form_data['item_name'] = part.value.decode('utf-8')
                    elif part.name == 'description':
                        form_data['description'] = part.value.decode('utf-8')
                    elif part.name == 'photo' and part.filename:
                        file_data = part

                item_name = form_data.get('item_name')
                description = form_data.get('description')

                if file_data:
                    photo_name = os.path.basename(file_data.filename)
                    photo_path = os.path.join('uploads', photo_name)
                    with open(photo_path, 'wb') as f:
                        f.write(file_data.file.read())
                else:
                    photo_path = None

                list_id = urlparse.parse_qs(urlparse.urlparse(self.path).query).get('list_id', [''])[0]

                try:
                    conn = mysql.connector.connect(**mysql_config)
                    cursor = conn.cursor()
                    query = "INSERT INTO items (item_name, description, photo_path, list_id) VALUES (%s, %s, %s, %s)"
                    cursor.execute(query, (item_name, description, photo_path, list_id))
                    conn.commit()
                    self._redirect(f'/list.html?list_id={list_id}')
                except mysql.connector.Error as err:
                    self._send_response(f"Error: {err}")
                finally:
                    cursor.close()
                    conn.close()


        else:
                         self.send_error(404, 'File Not Found')




# ----------start server and such---------------
def run(server_class=HTTPServer, handler_class=MyHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
