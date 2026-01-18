import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List
from stock_scanner.config import config
from stock_scanner.models import StockResult
from stock_scanner.utils.logger import get_logger

logger = get_logger(__name__)

class EmailClient:
    def __init__(self):
        self.sender_email = config.EMAIL_ADDRESS
        self.sender_password = config.EMAIL_PASSWORD
        self.recipient_email = config.EMAIL_RECIPIENT

    def send_report(self, results: List[StockResult], csv_filename: str):
        """Sends an HTML report of the scan results."""
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            logger.warning("Email credentials or recipient not set. Skipping email.")
            return

        if not results:
            logger.info("No results to email.")
            return

        # Prepare HTML table
        table_rows = ""
        for r in results:
            sentiment = "Negative" if r.news_sentiment.is_negative else "Neutral/Positive"
            table_rows += f"""
            <tr>
                <td>{r.candidate.symbol}</td>
                <td>{r.candidate.price}</td>
                <td>{r.volume_analysis.ratio:.2f}x</td>
                <td>{r.analyst_rating.upside_percent:.1f}%</td>
                <td>{sentiment}</td>
            </tr>
            """

        subject = f"🚀 Stock Scan Results (v2) - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
        <html>
          <head>
            <style>
              table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
              th, td {{ text-align: left; padding: 8px; border: 1px solid #ddd; }}
              th {{ background-color: #007bff; color: white; }}
              tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
          </head>
          <body>
            <h2>High Potential Candidates (LangGraph)</h2>
            <p>Found {len(results)} stocks matching criteria.</p>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>Vol Ratio</th>
                        <th>Upside</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            <p><em>Detailed reports for each stock are attached to the GitHub Run artifacts.</em></p>
          </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            # Using SMTP_SSL for Gmail
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            logger.info(f"Report email sent successfully to {self.recipient_email}!")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
