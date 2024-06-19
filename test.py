# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager

# def scrape_product_info_with_selenium(url):
#     # Set up the WebDriver (make sure to have Chrome installed or use another driver)
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service)

#     try:
#         # Open the URL
#         driver.get(url)

#         # Adjust the selectors based on your inspection
#         product_name = driver.find_element(By.CSS_SELECTOR, 'h1.product-title').text
#         product_image_url = driver.find_element(By.CSS_SELECTOR, 'img.product-image').get_attribute('src')
#         product_info = driver.find_element(By.CSS_SELECTOR, 'div.product-info').text

#         # Return the extracted information
#         return {
#             'name': product_name,
#             'image_url': product_image_url,
#             'info': product_info
#         }

#     finally:
#         # Close the WebDriver
#         driver.quit()

# # Example usage
# url = 'https://uzi-toys.com/product/electronic-guitar/?gad_source=1&gclid=CjwKCAjwvIWzBhAlEiwAHHWgvaMKTilJs8yNOchZMSxkv5FwQ2JWj0_WSt54h5pWbZtZsPU8ngZdsBoC-wIQAvD_BwE'
# product_info = scrape_product_info_with_selenium(url)
# if product_info:
#     print("Product Name:", product_info['name'])
#     print("Product Image URL:", product_info['image_url'])
#     print("Product Info:", product_info['info'])
# else:
#     print("Failed to retrieve product information.")


# ------------------------------------------------

        # elif self.path == 'google_callback':
        #     content_length = int(self.headers['Content-Length'])
        #     post_data = self.rfile.read(content_length)
        #     post_data = urlparse.parse_qs(post_data.decode('utf-8'))
        #     token = post_data.get('id_token', [''])[0]

        #     try:
        #         idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        #         if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        #             raise ValueError('Wrong issuer.')

        #         # ID token is valid. Get user info.
        #         userid = idinfo['sub']
        #         email = idinfo['email']

        #         self._redirect('/loggedinpage')

        #     except ValueError:
        #         # Invalid token
        #         self._send_response("Invalid token")



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