#!/usr/bin/env python3
import json
import os
import tkinter as tk
from bs4 import BeautifulSoup
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SINGLES = "https://www.cardmarket.com/en/Pokemon/Users/PROFILE/Offers/Singles"

def save_data_to_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

def load_data_from_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    except json.JSONDecodeError:
        return []

def login(driver, username, password):
    driver.get("https://www.cardmarket.com/en/Pokemon")
    login_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "header-login-toggle")))
    login_btn.click()

    username_input = driver.find_element_by_id("form__username")
    password_input = driver.find_element_by_id("form__password")

    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.send_keys(Keys.ENTER)

    try:
        WebDriverWait(driver, 10).until(EC.url_contains("/Pokemon/Account"))
        return True
    except:
        return False
    
def open_url_window(driver):
    url_window = tk.Tk()
    url_window.title("Change price")
    url_window.geometry("400x200")
    check_price_button = tk.Button(url_window, text="Check Price", command=lambda: check_price(driver, overall_price_change_label, change_price_all_button))
    check_price_button.pack(pady=10)
    
    # Label to display overall price change
    overall_price_change_label = tk.Label(url_window, text="", fg="black")
    overall_price_change_label.pack(pady=10)
    overall_price_change_label.pack_forget()
    
   
    change_price_all_button = tk.Button(url_window, text="Change Price for All")
    change_price_all_button.pack(pady=10)
    change_price_all_button.pack_forget()
    
    url_window.mainloop()

def save_login_credentials(username_entry, password_entry):
    username = username_entry.get()
    password = password_entry.get()

    credentials = {
        "username": username,
        "password": password,
    }

    with open('login_credentials.json', 'w') as file:
        json.dump(credentials, file)

def get_login_credentials():
    try:
        with open('login_credentials.json', 'r') as file:
            credentials = json.load(file)
            return credentials.get("username"), credentials.get("password")
    except FileNotFoundError:
        return None, None

def process_link(link, driver):
    base_url = "https://www.cardmarket.com"
    full_url = base_url + link
    driver.get(full_url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    info_list_div = soup.find("div", class_="info-list-container col-12 col-md-8 col-lg-12 mx-auto align-self-start")
    seven_days_average = ''

    if info_list_div:
        seven_days_elem = info_list_div.find("dt", string="7-days average price")
        if seven_days_elem:
            seven_days_average = seven_days_elem.find_next_sibling("dd").span.get_text().strip()
            try:
                seven_days_average = float(seven_days_average.replace(' €', '').replace(',', '').replace('.', '')) / 100
            except ValueError:
                seven_days_average = 0.0


    return {'seven': seven_days_average}

def update_price(driver, article_id, price, name):
    driver.get(SINGLES)
    # Wait for the page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@data-toggle='tooltip' and @data-html='true' and @data-placement='bottom']")))

    # Find the edit button based on the article_id
    edit_div = driver.find_element(By.XPATH, f"//div[@data-original-title='Edit' and contains(@data-modal, '{article_id}')]")
    edit_button = edit_div.find_element(By.TAG_NAME, "a")
    edit_button.click()

     # Wait for the modal to be displayed
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "price")))

    # Find the price input field and update the value
    price_input = driver.find_element(By.NAME, "price")
    price_input.clear()
    price_input.send_keys(str(price))

    # Find the submit button and click it
    submit_button = driver.find_element(By.NAME, "saveOfferButton")
    submit_button.click()

    # Wait for the confirmation message
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "formMessageSuccess")))

    messagebox.showinfo("Success", f"Price for article ID {name} updated successfully!")

def check_price(driver, overall_price_change_label, change_price_all_button):
    page_num = 1
    existing_data = []

    while True:
        target_url = f'{SINGLES}?site={page_num}'
        driver.get(target_url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        sellers_divs = soup.find_all('div', class_='col-seller col-12 col-lg-auto')
        article_row_divs = soup.select('div[id^="articleRow"]')
        article_numbers_list = [div['id'].replace('articleRow', '') for div in article_row_divs]
        price_elements = soup.find_all('div', class_='price-container d-none d-md-flex justify-content-end')
        price_numbers = [float(price_element.text.strip().replace('€', '').replace(',', '.')) for price_element in price_elements]

        for index, div in enumerate(sellers_divs[1:], 1):
            links_and_names = div.find('a')
            name = links_and_names.get_text()
            link = links_and_names['href'] + '?language=1'
            price_index = index - 1
            current_price = price_numbers[price_index]
            article_id = article_numbers_list[index - 1]

            existing_data.append({
                'name': name,
                'link': link,
                'current_price': current_price,
                'article_id': article_id,
                'seven_days_average': ''
            })

        # Check if there is a next page, otherwise break the loop
        next_page_button = driver.find_element_by_link_text('Next ›')
        if not next_page_button.is_enabled():
            break

        next_page_button.click()
        page_num += 1

    for item in existing_data:
        link = item['link']
        result = process_link(link, driver)
        item['seven_days_average'] = result['seven']

    save_data_to_json('current-price.json', existing_data)

    overall_price_change = 0.0
    json_data = load_data_from_json('current-price.json')
    for item in json_data:
        article_id = item["article_id"]
        name = item['name']
        current_price = item["current_price"]
        seven_days_average = item["seven_days_average"]
        if seven_days_average:
            overall_price_change += current_price - seven_days_average
        if change_price_all_button:
            update_price(driver, article_id, seven_days_average, name)

    overall_price_change_label.config(text=f"Overall Price Change: {overall_price_change:.2f} €", fg="green" if overall_price_change >= 0 else "red")
    overall_price_change_label.pack()
    change_price_all_button.pack()

if __name__ == "__main__":
    options = Options()
    options.add_argument("--headless")  
    driver = webdriver.Chrome(options=options)  
    driver.implicitly_wait(10)

    if os.path.exists('login_credentials.json'):
        try:
            credentials = get_login_credentials()
            username = credentials[0]
            password = credentials[1]

            if login(driver, username, password):
                open_url_window(driver)
            else:
                messagebox.showerror("Login Error", "Failed to login. Please check your credentials.")
        except Exception as e:
            print("Error during login:", e)
    else:
        # Create the main window
        main_window = tk.Tk()
        main_window.title("Cardmarket Data Scraper")
        main_window.geometry("400x200")

        username_label = tk.Label(main_window, text="Username:")
        username_label.pack(pady=10)
        username_entry = tk.Entry(main_window, width=30)
        username_entry.pack(pady=5)

        password_label = tk.Label(main_window, text="Password:")
        password_label.pack(pady=10)
        password_entry = tk.Entry(main_window, show="*")
        password_entry.pack(pady=5)

        save_button = tk.Button(main_window, text="Save Credentials", command=lambda: save_login_credentials(username_entry, password_entry))
        save_button.pack(pady=10)
                                                                                                    
        main_window.mainloop()

        driver.quit()