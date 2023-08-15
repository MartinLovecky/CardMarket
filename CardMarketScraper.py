#!/usr/bin/env python3
import requests
import json
import concurrent.futures
import threading
from tkinter import messagebox
from bs4 import BeautifulSoup

class CardMarketScraper:
    
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"}
    SINGLES = "https://www.cardmarket.com/en/Pokemon/Users/{username}/Offers/Singles"
    
    def __init__(self):
        self.session = requests.Session()
        self.cmtkn_value = self.get_cmtkn_value()
        self.existing_data_lock = threading.Lock()
    
    def get_cmtkn_value(self):
        response = requests.get("https://www.cardmarket.com/en/Pokemon", headers=self.HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        login_form = soup.find("form", {"id": "header-login"})
        cmtkn_input = login_form.find("input", {"name": "__cmtkn"})
        return cmtkn_input.get("value")
    
    def perform_login(self):
        try:
            credentials = self.load_data_from_json('login_credentials.json')
            username = credentials['username']
            password = credentials['password']
            login_response = self.login_request(username, password)
            if login_response.status_code == 200:
                return True
            else:
                messagebox.showerror("Login Error", "Failed to login. Please check your credentials.")
                return False
        except FileNotFoundError:
            messagebox.showwarning("Login Error", "Please save login credentials first.")
            return False
    
    def login_request(self, username, password):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "__cmtkn": self.cmtkn_value
        }
       
        login_data = {
            'username': username,
            'password': password,
        }
        
        response = self.session.post("https://www.cardmarket.com/en/Pokemon/PostGetAction/User_Login", headers=headers, method="POST", data = login_data)
        return response
    
    def scrape_singles_page(self, target_url):
        response = self.session.get(target_url, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        sellers_divs = soup.find_all('div', class_='col-seller col-12 col-lg-auto')
        article_row_divs = soup.select('div[id^="articleRow"]')
        article_numbers_list = [div['id'].replace('articleRow', '') for div in article_row_divs]
        price_elements = soup.find_all('div', class_='price-container d-none d-md-flex justify-content-end')
        price_numbers = [float(price_element.text.strip().replace('€', '').replace(',', '.')) for price_element in price_elements]

        data_to_save = []
        for index, div in enumerate(sellers_divs[1:], 1):
            links_and_names = div.find('a')
            name = links_and_names.get_text()
            link = links_and_names['href'] + '?language=1'
            price_index = index - 1
            current_price = price_numbers[price_index]
            article_id = article_numbers_list[index - 1]

        data_to_save.append({
            'name': name,
            'link': link,
            'current_price': current_price,
            'article_id': article_id,
            'seven_days_average': '',
            'cmtk': ''
        })
        
        return data_to_save
    
    def seven_days_average(self, link):
        base_url = "https://www.cardmarket.com"
        full_url = base_url + link
        response = self.session.get(full_url, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        info_list_div = soup.find("div", class_="info-list-container col-12 col-md-8 col-lg-12 mx-auto align-self-start")
        div_element = soup.find('div', {'id': 'tabContent-sell'})
        cmtkn_input = div_element.find('input', {'name': '__cmtkn'})
        seven_days_average = ''

        if info_list_div:
            seven_days_elem = info_list_div.find("dt", string="7-days average price")
            if seven_days_elem:
                seven_days_average = seven_days_elem.find_next_sibling("dd").span.get_text().strip()
                seven_days_average = float(seven_days_average.replace(' €', '').replace(',', '').replace('.', '')) / 100

            return {'seven': seven_days_average, 'cmtk': cmtkn_input['value']}
    
    def save_data_to_json(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
    
    def load_data_from_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as json_file:
                return json.load(json_file)
        except json.JSONDecodeError:
            return []
    
    def update_price(self, article_id, price, cmtkn_value, name):
        request_target = f'https://www.cardmarket.com/en/Pokemon/Modal/Article_EditArticleModal?idArticle={article_id}'
        payload = {
            'id_article': article_id,
            'cmtkn': cmtkn_value,
            'autoAdjustment': 'true',
            'price': str(price),
            'minCondition': '2',
        }

        response = self.session.post(request_target, headers=self.HEADERS, data=payload)

        if response.status_code == 200:
            messagebox.showinfo(f"Price for article ID {name} updated successfully!")
    
    def check_price(self, overall_price_change_label, change_price_all_button, progress_callback=None):
        credentials = self.load_data_from_json('login_credentials.json')
        username = credentials['username']
        existing_data = self.scrape_all_pages(username)
        self.update_seven_days_average(existing_data)
        self.save_data_to_json('current-price.json', existing_data)
    
        overall_price_change = self.calculate_overall_price_change(existing_data)
        self.display_price_change(overall_price_change, overall_price_change_label, change_price_all_button)
        
        total_items = len(existing_data)
        
        for index, item in enumerate(existing_data):
            article_id = item["article_id"]
            name = item['name']
            seven_days_average = item["seven_days_average"]
            cmtkn_value = item['cmtk']
            
        if change_price_all_button:
            self.update_price_with_progress(article_id, seven_days_average, cmtkn_value, name)
            
        if progress_callback:
            progress_callback(index + 1, total_items)

    def scrape_all_pages(self, username):
        page_num = 1
        existing_data = []
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while True:
                target_url = f'{self.SINGLES.format(username=username)}?site={page_num}'
                scraped_data =  executor.submit(self.scrape_singles_page, target_url)
        
                if not scraped_data:
                    break
                
                with self.existing_data_lock:
                    existing_data.extend(scraped_data)
                page_num += 1

        return existing_data
    
    def update_seven_days_average(self, data):
        for item in data:
            link = item['link']
            result = self.seven_days_average(link)
            item['seven_days_average'] = result['seven']
            item['cmtk'] = result['cmtk']
    
    def calculate_overall_price_change(self, data):
        overall_price_change = 0.0
        for item in data:
            current_price = item["current_price"]
            seven_days_average = item["seven_days_average"]
            if seven_days_average:
                overall_price_change += current_price - seven_days_average
        return overall_price_change
    
    def display_price_change(self, overall_price_change, overall_price_change_label, change_price_all_button):
        overall_price_change_label.config(text=f"Overall Price Change: {overall_price_change:.2f} €", fg="green" if overall_price_change >= 0 else "red")        
        overall_price_change_label.pack()
        change_price_all_button.pack()