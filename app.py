import os
import logging
from flask import Flask, jsonify
from flask_restful import Resource, Api
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import time

app = Flask(__name__)
api = Api(app)

logging.basicConfig(level=logging.INFO)

class PublicationsAPI(Resource):
    def get(self, year):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        
        login_url = os.environ.get('login_url')
        logging.info(f"Login URL: {login_url}")
        username = os.environ.get('QALAM_username')
        logging.info(f"Username: {username}")
        password = os.environ.get('QALAM_password')
        logging.info(f"Password: {password}")
        publications_url = os.environ.get('nrp_pubs_url')
        logging.info(f"Publications URL: {publications_url}")
        
        try:
            logging.info("Navigating to login page")
            driver.get(login_url)
            
            # Wait until the CSRF token is present
            csrf_token_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'csrf_token'))
            )
            csrf_token = csrf_token_element.get_attribute('value')
            logging.info(f"CSRF token obtained: {csrf_token}")
            
            # Enter the login credentials
            logging.info("Entering login credentials")
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'login'))
            )
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'password'))
            )
            csrf_field = csrf_token_element
            
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit the form
            login_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
            )
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(login_button))
            driver.execute_script("arguments[0].click();", login_button)
            
            logging.info("Waiting for login to complete")
            WebDriverWait(driver, 20).until(EC.url_changes(login_url))
            logging.info("Login successful, URL changed")

            logging.info("Navigating to publications page")
            # publications_url = 'https://qalam.nust.edu.pk/web#action=1754&model=odoocms.nrp.publications.journal&view_type=list&cids=1&menu_id=1382'
            driver.get(publications_url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'o_filters_menu_button')))
            logging.info("Publications page loaded")

            logging.info("Looking for filters button")
            filters_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'o_filters_menu_button'))
            )
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(filters_button))
            driver.execute_script("arguments[0].click();", filters_button)
            logging.info("Filters button clicked")

            logging.info("Waiting for 'Approved' filter option to appear")
            approved_filter = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='dropdown-menu o_dropdown_menu o_filters_menu show']//div[@data-id='__filter__42' and @class='o_menu_item']"))
            )
            approved_filter.click()
            logging.info("Approved filter applied")

            # Wait for 2 seconds to allow the page to update with the new data
            time.sleep(2)

            # Wait for o_pager_limit to update after applying filter
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "o_pager_limit"))
            )
            logging.info("o_pager_limit updated")

            # Get the value of o_pager_limit
            pager_limit_element = driver.find_element(By.CLASS_NAME, "o_pager_limit")
            pager_limit_value = pager_limit_element.text.strip()
            logging.info(f"o_pager_limit value: {pager_limit_value}")

            logging.info("Adding custom filter for publication date")
            custom_filter_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'o_add_custom_filter'))
            )
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'o_add_custom_filter')))
            driver.execute_script("arguments[0].click();", custom_filter_button)
            logging.info("Custom filter button clicked")

            logging.info("Selecting 'Print Publication Date' in the first select dropdown")
            field_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'o_searchview_extended_prop_field'))
            )
            field_dropdown.click()
            logging.info("Print pubs div found and Field dropdown clicked")
            field_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select.o_searchview_extended_prop_field option[value='publication_date']"))
            )
            field_option.click()
            logging.info("Selected 'Print Publication Date'")

            logging.info("Selecting 'is between' in the operator dropdown")
            operator_dropdown = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'o_searchview_extended_prop_op'))
            )
            operator_dropdown.click()
            logging.info("Is between div found and Field dropdown clicked")
            operator_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "select.o_searchview_extended_prop_op option[value='between']"))
            )
            operator_option.click()
            logging.info("Selected 'is between'")

            logging.info(f"Setting date range from 1st January to 31st December {year}")
            # Locate all date picker inputs within the specified span
            datepickers = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.o_searchview_extended_prop_value div.o_datepicker input.o_datepicker_input"))
            )
            
            # Ensure there are at least two date picker inputs found
            if len(datepickers) >= 2:
                # Click and set the start date (1st January)
                datepickers[0].click()
                datepickers[0].send_keys(f"0101{year}")
                logging.info(f"Start date set: 0101{year}")

                # Click and set the end date (31st December)
                datepickers[1].click()
                datepickers[1].send_keys(f"1231{year}")
                logging.info(f"End date set: 1231{year}")

                # Confirming accurate date input (optional)
                start_value = datepickers[0].get_attribute('value')
                end_value = datepickers[1].get_attribute('value')
                if start_value == f"01/01/{year}" and end_value == f"12/31/{year}":
                    logging.info("Confirmed accurate date input")
                else:
                    logging.warning("Date input might not be accurate")

                logging.info("Date range set successfully")
            else:
                logging.error("Could not find date pickers")

            logging.info("Applying the custom filter")
            apply_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.o_generator_menu.o_add_filter_menu button.o_apply_filter"))
            )
            apply_button.click()
            logging.info("Clicked 'Apply' button")

            # Wait for 3 seconds to allow the page to update with the new data
            time.sleep(3)

            logging.info("Waiting for the publication count to be visible")
            # Wait for the o_pager_limit to update
            count_span = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, "o_pager_limit"))
            )
            logging.info("o_pager_limit updated")
            publication_count = int(count_span.text)
            logging.info(f"Publication count obtained: {publication_count}")
            driver.quit()
            return jsonify({'count': publication_count})

        except TimeoutException as e:
            logging.error(f"TimeoutException occurred: {e}")
            driver.quit()
            return jsonify({'error': 'Timeout while loading page elements'})
        except NoSuchElementException as e:
            logging.error(f"NoSuchElementException occurred: {e}")
            driver.quit()
            return jsonify({'error': 'Element not found during the process'})
        except ElementNotInteractableException as e:
            logging.error(f"ElementNotInteractableException occurred: {e}")
            driver.quit()
            return jsonify({'error': 'Element not interactable during the process'})
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            driver.quit()
            return jsonify({'error': 'An error occurred during the process'})
        raise
        
# Add the PublicationsAPI resource
api.add_resource(PublicationsAPI, '/publications/<string:year>')

if __name__ == '__main__':
    app.run(debug=True)
