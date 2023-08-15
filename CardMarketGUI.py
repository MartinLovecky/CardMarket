#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from CardMarketScraper import CardMarketScraper

class CardMarketGUI:
    def __init__(self, scraper):
        self.scraper = scraper
        self.main_window = tk.Tk()
        self.main_window.title("Cardmarket Data Scraper")
        self.main_window.geometry("400x200")

        self.username_label = tk.Label(self.main_window, text="Username:")
        self.username_label.pack(pady=10)
        self.username_entry = tk.Entry(self.main_window, width=30)
        self.username_entry.pack(pady=5)

        self.password_label = tk.Label(self.main_window, text="Password:")
        self.password_label.pack(pady=10)
        self.password_entry = tk.Entry(self.main_window, show="*")
        self.password_entry.pack(pady=5)

        self.save_button = tk.Button(self.main_window, text="Save Credentials", command=self.save_login_credentials)
        self.save_button.pack(pady=10)
        
        self.obtain_progress = ttk.Progressbar(self.main_window, orient="horizontal", mode="indeterminate")
        self.obtain_progress.pack(pady=10)
        self.update_price_progress = ttk.Progressbar(self.main_window, orient="horizontal", mode="indeterminate")
        self.update_price_progress.pack(pady=10)

        self.main_window.mainloop()

    def open_url_window(self):
        url_window = tk.Tk()
        url_window.title("Change price")
        url_window.geometry("400x200")
        check_price_button = tk.Button(url_window, text="Check Price", command=self.check_price_with_progress)
        check_price_button.pack(pady=10)
    
        # Label to display overall price change
        self.overall_price_change_label = tk.Label(url_window, text="", fg="black")
        self.overall_price_change_label.pack(pady=10)
        self.overall_price_change_label.pack_forget()
    
        # Button to perform price changes for all items
        self.change_price_all_button = tk.Button(url_window, text="Change Price for All")
        self.change_price_all_button.pack(pady=10)
        self.change_price_all_button.pack_forget()
    
    def update_progress(self,current_step, total_steps):
        progress = (current_step / total_steps) * 100
        self.obtain_progress['value'] = progress
        self.main_window.update_idletasks()  # Update the GUI
    
    def check_price_with_progress(self):
        self.show_obtain_progress()  # Show obtain progress bar
        
        def update_progress(current_step, total_steps):
            self.main_window.after(0, self.update_progress, current_step, total_steps)
        
        self.scraper.check_price(self.update_price_change_label, self.change_price_all_button, progress_callback=update_progress)
        self.hide_obtain_progress()  # Hide 
    
    def update_price_with_progress(self, article_id, price, cmtkn_value, name):
        self.show_update_price_progress()  # Show the progress bar
        def update_progress(current_step, total_steps):
            self.main_window.after(0, lambda: self.update_progress(current_step, total_steps))

        # Call the update_price method with the progress_callback parameter
        self.scraper.update_price(article_id, price, cmtkn_value, name, progress_callback=update_progress)

        self.hide_update_price_progress()  
    
    def save_login_credentials(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        credentials = {
            "username": username,
            "password": password,
        }   
        
        self.scraper.save_data_to_json('login_credentials.json', credentials)
        if self.scraper.perform_login():
            self.open_url_window()
    
    def show_obtain_progress(self):
        self.obtain_progress.start()

    def hide_obtain_progress(self):
        self.obtain_progress.stop()

    def show_update_price_progress(self):
        self.update_price_progress.start()

    def hide_update_price_progress(self):
        self.update_price_progress.stop()

if __name__ == "__main__":
    scraper = CardMarketScraper()
    gui = CardMarketGUI(scraper)