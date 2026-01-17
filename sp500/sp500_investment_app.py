import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QLineEdit
from PyQt5.QtCore import QTimer
import requests
from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup

class SP500InvestmentApp(QMainWindow):
    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        
        # Create widgets for displaying S&P 500 data
        current_value_layout = QHBoxLayout()
        current_value_label = QLabel("当前值:")
        self.sp500_current_value = QLabel("加载中...")
        current_value_layout.addWidget(current_value_label)
        current_value_layout.addWidget(self.sp500_current_value)
        current_value_layout.addStretch()
        
        monthly_change_layout = QHBoxLayout()
        monthly_change_label = QLabel("月度变化:")
        self.monthly_change_value = QLabel("加载中...")
        monthly_change_layout.addWidget(monthly_change_label)
        monthly_change_layout.addWidget(self.monthly_change_value)
        monthly_change_layout.addStretch()
        
        ytd_layout = QHBoxLayout()
        ytd_label = QLabel("年度至今表现:")
        self.ytd_value = QLabel("加载中...")
        ytd_layout.addWidget(ytd_label)
        ytd_layout.addWidget(self.ytd_value)
        ytd_layout.addStretch()
        
        recommended_layout = QHBoxLayout()
        recommended_label = QLabel("建议投资额度:")
        self.recommended_value = QLabel(str(self.base_investment))
        recommended_layout.addWidget(recommended_label)
        recommended_layout.addWidget(self.recommended_value)
        recommended_layout.addStretch()
        
        strategy_layout = QHBoxLayout()
        strategy_label = QLabel("投资策略:")
        self.strategy_value = QLabel("等待数据更新...")
        strategy_layout.addWidget(strategy_label)
        strategy_layout.addWidget(self.strategy_value)
        strategy_layout.addStretch()
        
        # Create figure for chart
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        # Add all widgets to main layout
        layout.addLayout(current_value_layout)
        layout.addLayout(monthly_change_layout)
        layout.addLayout(ytd_layout)
        layout.addLayout(recommended_layout)
        layout.addLayout(strategy_layout)
        layout.addWidget(self.canvas)
        layout.addStretch()

    def setup_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        info_label = QLabel("历史数据分析功能开发中...")
        layout.addWidget(info_label)
        layout.addStretch()

    def setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        base_investment_layout = QHBoxLayout()
        base_investment_label = QLabel("基础投资额度:")
        self.base_investment_input = QLineEdit(str(self.base_investment))
        base_investment_layout.addWidget(base_investment_label)
        base_investment_layout.addWidget(self.base_investment_input)
        base_investment_layout.addStretch()
        
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        
        layout.addLayout(base_investment_layout)
        layout.addWidget(save_button)
        layout.addStretch()

    def update_chart(self):
        if self.sp500_data is not None and not self.sp500_data.empty:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(self.sp500_data.index, self.sp500_data['Close'])
            ax.set_title('S&P 500 历史走势')
            ax.set_xlabel('日期')
            ax.set_ylabel('价格')
            self.figure.autofmt_xdate()
            self.canvas.draw()

    def save_settings(self):
        try:
            new_base_investment = float(self.base_investment_input.text())
            if new_base_investment > 0:
                self.base_investment = new_base_investment
                self.calculate_recommended_investment()
        except ValueError:
            pass

    def load_api_key(self):
        # Placeholder for future API key loading functionality
        pass

    def fetch_sp500_data(self):
        try:
            print("Fetching S&P 500 data...")
            # Set up headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Fetch current S&P 500 data from Google Finance
            url = 'https://www.google.com/finance/quote/.INX:INDEXSP'
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract current value
            current_value_element = soup.select_one('div.YMlKec.fxKbKc')
            if not current_value_element:
                raise Exception("Failed to fetch current S&P 500 value")
            current_value = float(current_value_element.text.replace(',', ''))
            
            # Create a DataFrame to store historical data
            dates = []
            prices = []
            
            # Fetch historical data
            historical_url = 'https://www.google.com/finance/quote/.INX:INDEXSP/history?window=6M'
            response = requests.get(historical_url, headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract historical data from the table
            rows = soup.select('div[role="row"]')
            for row in rows:
                cols = row.select('div[role="cell"]')
                if len(cols) >= 2:
                    date_str = cols[0].text.strip()
                    try:
                        date = datetime.datetime.strptime(date_str, '%b %d, %Y')
                        price = float(cols[1].text.strip().replace(',', ''))
                        dates.append(date)
                        prices.append(price)
                    except (ValueError, IndexError):
                        continue
            
            # Create DataFrame with historical data
            self.sp500_data = pd.DataFrame({'Close': prices}, index=dates)
            self.sp500_data.sort_index(inplace=True)
            
            # Calculate monthly change
            today = datetime.datetime.now()
            one_month_ago = today - datetime.timedelta(days=30)
            monthly_data = self.sp500_data[self.sp500_data.index >= one_month_ago]
            if not monthly_data.empty:
                one_month_ago_close = monthly_data['Close'].iloc[0]
                self.last_month_change_pct = ((current_value - one_month_ago_close) / one_month_ago_close) * 100
            else:
                self.last_month_change_pct = 0
            
            # Calculate YTD change
            start_of_year = datetime.datetime(today.year, 1, 1)
            ytd_data = self.sp500_data[self.sp500_data.index >= start_of_year]
            if not ytd_data.empty:
                ytd_start_value = ytd_data['Close'].iloc[0]
                ytd_change_pct = ((current_value - ytd_start_value) / ytd_start_value) * 100
            else:
                ytd_change_pct = 0
            
            # Update UI elements
            self.sp500_current_value.setText(f"{current_value:.2f}")
            self.monthly_change_value.setText(f"{self.last_month_change_pct:.2f}%")
            self.ytd_value.setText(f"{ytd_change_pct:.2f}%")
            
            # Update recommended investment
            self.calculate_recommended_investment()
            
            # Update chart
            self.update_chart()
            
            print("UI updated successfully")
            
        except Exception as e:
            print(f"Error fetching S&P 500 data: {e}")
            self.sp500_current_value.setText("Error")
            self.monthly_change_value.setText("Error")
            self.ytd_value.setText("Error")

    def calculate_recommended_investment(self):
        if self.sp500_data is None or self.sp500_data.empty:
            self.recommended_investment = self.base_investment
            self.strategy_value.setText("无法获取市场数据，使用基础投资额度")
            return
        
        # Calculate recommended investment based on monthly change
        if self.last_month_change_pct <= -7:
            self.recommended_investment = self.base_investment * 2.0  # 10万日元
            self.strategy_value.setText("市场大幅下跌(>7%)，建议顶格追加至10万日元")
        elif self.last_month_change_pct <= -4:
            self.recommended_investment = self.base_investment * 1.6  # 8万日元
            self.strategy_value.setText("市场中等下跌(4-7%)，建议追加至8万日元")
        elif self.last_month_change_pct <= -1:
            self.recommended_investment = self.base_investment * 1.3  # 6.5万日元
            self.strategy_value.setText("市场小幅下跌(1-4%)，建议追加至6.5万日元")
        elif self.last_month_change_pct >= 8:
            self.recommended_investment = self.base_investment * 0.8  # 4万日元
            self.strategy_value.setText("市场大幅上涨(>8%)，建议减少至4万日元")
        else:
            self.recommended_investment = self.base_investment  # 5万日元
            self.strategy_value.setText("市场相对稳定(-1%~+8%)，维持基准投资额度")
        
        self.recommended_value.setText(f"{self.recommended_investment:,.0f}")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("S&P 500 动态投资策略")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize data
        self.sp500_data = None
        self.base_investment = 50000  # Default base investment (in JPY)
        self.last_month_change_pct = 0
        self.recommended_investment = self.base_investment
        self.api_key = ""
        
        # Create the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Create the dashboard tab
        self.dashboard_tab = QWidget()
        self.tabs.addTab(self.dashboard_tab, "仪表盘")
        
        # Create the history tab
        self.history_tab = QWidget()
        self.tabs.addTab(self.history_tab, "历史分析")
        
        # Create the settings tab
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "设置")
        
        # Setup each tab
        self.setup_dashboard_tab()
        self.setup_history_tab()
        self.setup_settings_tab()
        
        # Load saved API key if exists
        self.load_api_key()
        
        # Initialize data
        self.fetch_sp500_data()
        
        # Setup timer for auto-refresh (every 30 minutes)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_sp500_data)
        self.refresh_timer.start(30 * 60 * 1000)  # 30 minutes in milliseconds

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SP500InvestmentApp()
    window.show()
    sys.exit(app.exec_())