import requests
import json
import time
import os
import logging
import re
from typing import Dict, List
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import random

class YahooFinanceScraper:
    def __init__(self, output_dir: str = 'data', timeout: int = 15, max_retries: int = 3):
        self.base_url = "https://finance.yahoo.com/quote"
        self.sp500_futures_symbol = "ES=F"  # E-Mini S&P 500 futures symbol
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        self.timeout = timeout
        self.max_retries = max_retries
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()

    def setup_logging(self):
        log_file = self.output_dir / 'scraper.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def _get_sp500_futures_data(self) -> Dict:
        url = f"{self.base_url}/{self.sp500_futures_symbol}"
        
        for attempt in range(self.max_retries):
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                logging.info(f"Fetching S&P 500 futures data (attempt {attempt + 1}/{self.max_retries})")
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                if 'denied' in response.text.lower() or 'rate limit' in response.text.lower():
                    raise Exception("Possible rate limiting detected")
                
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract price
                price = None
                # Try multiple selectors for price
                price_span = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
                if not price_span:
                    price_span = soup.find('fin-streamer', {'data-symbol': self.sp500_futures_symbol, 'data-field': 'regularMarketPrice'})
                if not price_span:
                    price_span = soup.find('div', {'class': 'D(ib) Mend(20px)'})
                    if price_span:
                        price_span = price_span.find('fin-streamer', {'data-field': 'regularMarketPrice'})
                
                if price_span:
                    try:
                        # Try getting price from 'value' attribute first
                        price_str = price_span.get('value')
                        if not price_str:
                            # If 'value' is not available, try getting from text content
                            price_str = price_span.text.strip().replace(',', '')
                        price = float(price_str) if price_str else None
                    except (ValueError, AttributeError) as e:
                        logging.error(f"Error parsing price: {str(e)}")
                        price = None

                # Extract volume
                volume = None
                # Try multiple selectors for volume
                volume_td = soup.find('td', {'data-test': 'TD_VOLUME-value'})
                if not volume_td:
                    volume_span = soup.find('fin-streamer', {'data-field': 'regularMarketVolume'})
                    if volume_span:
                        try:
                            volume_str = volume_span.get('value')
                            if not volume_str:
                                volume_str = volume_span.text.strip().replace(',', '')
                            # Handle volume with 'k' suffix
                            if volume_str:
                                if 'k' in volume_str.lower():
                                    volume_str = volume_str.lower().replace('k', '')
                                    volume = int(float(volume_str) * 1000)
                                else:
                                    volume = int(volume_str)
                        except (ValueError, AttributeError) as e:
                            logging.error(f"Error parsing volume from fin-streamer: {str(e)}")
                else:
                    try:
                        volume_text = volume_td.text.strip().replace(',', '')
                        volume = int(volume_text)
                    except (ValueError, AttributeError) as e:
                        logging.error(f"Error parsing volume from td: {str(e)}")

                # Extract previous close
                prev_close = None
                # Try multiple selectors for previous close
                prev_close_td = soup.find('td', {'data-test': 'PREV_CLOSE-value'})
                if not prev_close_td:
                    prev_close_span = soup.find('fin-streamer', {'data-field': 'regularMarketPreviousClose'})
                    if prev_close_span:
                        try:
                            prev_close_str = prev_close_span.get('value')
                            if not prev_close_str:
                                prev_close_str = prev_close_span.text.strip().replace(',', '')
                            prev_close = float(prev_close_str) if prev_close_str else None
                        except (ValueError, AttributeError) as e:
                            logging.error(f"Error parsing previous close from fin-streamer: {str(e)}")
                else:
                    try:
                        prev_close_text = prev_close_td.text.strip().replace(',', '')
                        prev_close = float(prev_close_text)
                    except (ValueError, AttributeError) as e:
                        logging.error(f"Error parsing previous close from td: {str(e)}")

                # Verify data integrity
                if price is None:
                    raise ValueError("Could not extract price data")

                data = {
                    'symbol': self.sp500_futures_symbol,
                    'price': price,
                    'volume': volume,
                    'prev_close': prev_close,
                    'timestamp': datetime.now().isoformat()
                }
                logging.info("Successfully scraped S&P 500 futures data")
                return data

            except requests.Timeout:
                logging.warning(f"Timeout while fetching data (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(5 + (5 * attempt))  # Linear backoff

            except Exception as e:
                logging.error(f"Error scraping data: {str(e)}")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(5 + (5 * attempt))  # Linear backoff

        return {
            'symbol': self.sp500_futures_symbol,
            'error': f"Failed after {self.max_retries} attempts",
            'timestamp': datetime.now().isoformat()
        }

    def scrape_sp500_futures(self) -> Dict:
        logging.info("Starting to scrape S&P 500 futures data")
        start_time = time.time()
        
        # Get current futures data
        current_data = self._get_sp500_futures_data()
        
        # Get historical data
        historical_data = self._get_historical_data()
        
        elapsed_time = time.time() - start_time
        if 'error' not in current_data and len(historical_data) > 0 and 'error' not in historical_data[0]:
            logging.info(f"Scraping completed successfully in {elapsed_time:.2f} seconds")
            # Save both current and historical data
            combined_data = [current_data] + historical_data
            self.save_to_json(combined_data, is_intermediate=False)
            return current_data
        else:
            logging.error(f"Scraping failed in {elapsed_time:.2f} seconds")
            self.save_to_json([current_data], is_intermediate=False)
            return current_data

    def save_to_json(self, data: List[Dict], is_intermediate: bool = False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sp500_futures_{timestamp}_intermediate.json" if is_intermediate else f"sp500_futures_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logging.info(f"Data saved to {filepath}")

    def _get_historical_data(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        if not start_date:
            # Default to 6 months of historical data
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Convert dates to UNIX timestamps for Yahoo Finance API
        start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        
        # Construct URL with query parameters
        params = {
            'period1': start_timestamp,
            'period2': end_timestamp,
            'interval': '1d',
            'filter': 'history',
            'frequency': '1d',
            'includeAdjustedClose': 'true'
        }
        url = f"{self.base_url}/{self.sp500_futures_symbol}/history?{urlencode(params)}"
        historical_data = []

        for attempt in range(self.max_retries):
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                logging.info(f"Fetching historical data from {start_date} to {end_date} (attempt {attempt + 1}/{self.max_retries})")
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()

                if 'denied' in response.text.lower() or 'rate limit' in response.text.lower():
                    raise Exception("Possible rate limiting detected")

                # Extract data from the response
                if 'CrumbStore' not in response.text:
                    raise ValueError("Could not find required data in the page")
                
                # Use API endpoint for historical data
                crumb_regex = r'"CrumbStore":{"crumb":"(.+?)"}'                
                crumb_match = re.search(crumb_regex, response.text)
                
                if not crumb_match:
                    raise ValueError("Could not extract authentication crumb")
                
                crumb = crumb_match.group(1)
                api_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.sp500_futures_symbol}?period1={start_timestamp}&period2={end_timestamp}&interval=1d&events=history&crumb={crumb}"
                
                api_response = requests.get(api_url, headers=headers, cookies=response.cookies, timeout=self.timeout)
                api_response.raise_for_status()
                
                data = api_response.json()
                if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
                    raise ValueError("No historical data available in API response")
                
                result = data['chart']['result'][0]
                timestamps = result.get('timestamp', [])
                quote = result.get('indicators', {}).get('quote', [{}])[0]
                
                opens = quote.get('open', [])
                highs = quote.get('high', [])
                lows = quote.get('low', [])
                closes = quote.get('close', [])
                volumes = quote.get('volume', [])
                
                for i in range(len(timestamps)):
                    if all(x is not None for x in [opens[i], highs[i], lows[i], closes[i], volumes[i]]):
                        date = datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
                        historical_data.append({
                            'symbol': self.sp500_futures_symbol,
                            'date': date,
                            'open': opens[i],
                            'high': highs[i],
                            'low': lows[i],
                            'close': closes[i],
                            'volume': volumes[i]
                        })

                rows = table.find_all('tr')[1:]  # Skip header row
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:  # Ensure we have all required columns
                        try:
                            date_str = cols[0].text.strip()
                            date_obj = datetime.strptime(date_str, '%b %d, %Y')
                            formatted_date = date_obj.strftime('%Y-%m-%d')

                            # Parse numeric values
                            open_price = float(cols[1].text.strip().replace(',', ''))
                            high_price = float(cols[2].text.strip().replace(',', ''))
                            low_price = float(cols[3].text.strip().replace(',', ''))
                            close_price = float(cols[4].text.strip().replace(',', ''))
                            volume = int(cols[5].text.strip().replace(',', ''))

                            historical_data.append({
                                'symbol': self.sp500_futures_symbol,
                                'date': formatted_date,
                                'open': open_price,
                                'high': high_price,
                                'low': low_price,
                                'close': close_price,
                                'volume': volume
                            })
                        except (ValueError, AttributeError) as e:
                            logging.error(f"Error parsing row data: {str(e)}")
                            continue

                logging.info(f"Successfully scraped {len(historical_data)} historical data points")
                return historical_data

            except requests.Timeout:
                logging.warning(f"Timeout while fetching historical data (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(5 + (5 * attempt))  # Linear backoff

            except Exception as e:
                logging.error(f"Error scraping historical data: {str(e)}")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(5 + (5 * attempt))  # Linear backoff

        return [{
            'symbol': self.sp500_futures_symbol,
            'error': f"Failed to fetch historical data after {self.max_retries} attempts",
            'timestamp': datetime.now().isoformat()
        }]

    def scrape_historical_data(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        logging.info("Starting to scrape historical S&P 500 futures data")
        start_time = time.time()

        data = self._get_historical_data(start_date, end_date)

        elapsed_time = time.time() - start_time
        if not any('error' in d for d in data):
            logging.info(f"Historical data scraping completed successfully in {elapsed_time:.2f} seconds")
        else:
            logging.error(f"Historical data scraping failed in {elapsed_time:.2f} seconds")

        filename = f"sp500_futures_historical_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logging.info(f"Historical data saved to {filepath}")
        return data

def main():
    try:
        scraper = YahooFinanceScraper(output_dir='sp500_futures_data', timeout=15, max_retries=3)
        data = scraper.scrape_sp500_futures()
        logging.info("Data collection completed. Exiting program.")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()