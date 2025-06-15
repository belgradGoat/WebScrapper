import requests # For making HTTP requests to fetch website content
from bs4 import BeautifulSoup # For parsing HTML and extracting data
import os # For interacting with the operating system (e.g., file paths, creating directories)
import json # For working with JSON data (configuration file)
import hashlib # For generating hash values (to detect content changes)
import difflib # For comparing text and finding differences
from datetime import datetime # For working with dates and times (timestamps)
import time # For adding delays or scheduling tasks (not heavily used in current run_checks)
import logging # For logging events, errors, and information
import re # For regular expressions (e.g., creating safe filenames)
import glob # For finding files matching a pattern (e.g., finding the latest archive)
import pyttsx3 # For text-to-speech alerts (optional)
from transformers import pipeline # For NLP tasks like sentiment analysis (optional)
from deep_translator import GoogleTranslator # For translating text (optional)
import schedule # For scheduling periodic checks

# --- Logging Configuration ---
# Set up basic logging to output messages to both a file and the console.
# - level: The minimum severity level of messages to log (INFO and above).
# - format: The format of log messages (timestamp, level, message).
# - handlers:
#   - FileHandler: Writes logs to "webscraper.log".
#   - StreamHandler: Writes logs to the console (standard output).
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webscraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger() # Get the root logger instance.

class WebScraper:
    """
    A class to scrape websites, detect changes, translate content, 
    analyze sentiment, and log differences.
    """
    def __init__(self, config_file="config.json"):
        """
        Initialize the WebScraper.
        - Loads configuration.
        - Initializes optional components like sentiment analyzer, TTS engine, and translator.

        Args:
            config_file (str): Path to the JSON configuration file.
        """
        self.config_file = config_file
        self.load_config() # Load settings from the config file
        
        # --- Initialize Optional NLP and TTS Components ---
        # These are initialized in try-except blocks to allow the scraper
        # to function even if these components fail to load (e.g., missing models).

        # Initialize sentiment analysis pipeline (Hugging Face Transformers)
        try:
            # Uses a pre-trained model for sentiment analysis.
            self.sentiment_analyzer = pipeline("sentiment-analysis")
            logger.info("Sentiment analysis pipeline initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analysis pipeline: {e}")
            self.sentiment_analyzer = None # Set to None if initialization fails
        
        # Initialize text-to-speech engine (pyttsx3)
        try:
            self.tts_engine = pyttsx3.init()
            logger.info("Text-to-speech engine initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize text-to-speech engine: {e}")
            self.tts_engine = None # Set to None if initialization fails

        # Initialize translator (GoogleTranslator from deep_translator)
        try:
            # Configured to auto-detect source language and translate to English ('en').
            self.translator = GoogleTranslator(source='auto', target='en')
            logger.info("Translator initialized (auto-detect to English).")
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            self.translator = None # Set to None if initialization fails
            
    def load_config(self):
        """
        Load configuration from the JSON file specified in `self.config_file`.
        If the file doesn't exist, a default configuration is created and saved.
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
        else:
            # Define a default configuration structure if the file is not found.
            self.config = {
                "websites": [
                    {
                        "name": "Example News", # Descriptive name for the website
                        "url": "https://example.com/news", # URL to scrape
                        "selector": "div.content", # CSS selector for the main content area
                        "check_interval_minutes": 60, # How often to check (for future scheduling)
                        "importance": "high", # User-defined importance level
                        "translate_changes_to_en": True # Flag to enable/disable translation of changes
                    }
                ],
                "alert_thresholds": { # Thresholds for triggering alerts based on sentiment
                    "negative": 0.7, # Min score for negative sentiment to be notable
                    "positive": 0.8  # Min score for positive sentiment to be notable
                },
                "alert_settings": { # General alert settings
                    "speech_enabled": True, # Enable/disable text-to-speech alerts
                    "min_change_percent": 5 # Minimum percentage change to trigger an alert
                },
                "todays_changes_file": "website_archives/TodaysChanges.txt" # File to log all detected changes for the day
            }
            self.save_config() # Save the newly created default configuration
            logger.info(f"Default configuration created and saved to {self.config_file}")
            
    def save_config(self):
        """Save the current configuration (self.config) to the JSON file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4) # Save with pretty printing (indent=4)
        logger.info(f"Configuration saved to {self.config_file}")

    def _get_site_filename(self, website_name):
        """
        Generate a unique, timestamped filename for storing fetched website content.
        This helps in archiving versions of the website content.

        Args:
            website_name (str): The name of the website (used to create a safe filename).

        Returns:
            str: The full path to the new archive file.
        """
        archive_dir = "website_archives" # Directory to store content archives
        os.makedirs(archive_dir, exist_ok=True) # Create the directory if it doesn't exist
        
        # Sanitize the website name to make it suitable for a filename
        # Replaces characters that are not alphanumeric, underscore, or hyphen with an underscore.
        safe_name = re.sub(r'[^\w\-_]', '_', website_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # Current timestamp for uniqueness
        return os.path.join(archive_dir, f"{safe_name}_{timestamp}.txt")

    def _get_latest_saved_file(self, website_name):
        """
        Find the most recently saved content archive file for a given website.

        Args:
            website_name (str): The name of the website.

        Returns:
            str or None: The path to the latest file, or None if no files are found.
        """
        archive_dir = "website_archives"
        safe_name = re.sub(r'[^\w\-_]', '_', website_name)
        
        # Use glob to find all files matching the pattern for this website's archives.
        # The pattern includes the sanitized name and a wildcard for the timestamp.
        files = glob.glob(os.path.join(archive_dir, f"{safe_name}_*.txt"))
        
        if not files:
            return None # No archive files found
            
        # Return the file with the most recent creation/modification time.
        return max(files, key=os.path.getctime)

    def fetch_website_content(self, website_config):
        """Fetch content from a website, save it, and return the content."""
        url = website_config["url"]
        website_name = website_config["name"]
        logger.info(f"Fetching content for {website_name} from {url}")
        
        # Add debug info
        logger.info(f"Current working directory: {os.getcwd()}")
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            content_text = ""
            if "selector" in website_config and website_config["selector"]:
                elements = soup.select(website_config["selector"])
                if elements:
                    content_text = "\n".join([el.get_text(separator='\n', strip=True) for el in elements])
                else:
                    logger.warning(f"Selector '{website_config['selector']}' not found for {website_name}. Fetching all text.")
                    content_text = soup.get_text(separator='\n', strip=True)
            else:
                content_text = soup.get_text(separator='\n', strip=True)
            
            # Add debug info about content
            logger.info(f"Content fetched for {website_name}. Length: {len(content_text)} characters")
            
            # Save the fetched content to a new timestamped file
            site_filename = self._get_site_filename(website_name)
            logger.info(f"Attempting to save to: {site_filename}")
            
            try:
                with open(site_filename, "w", encoding="utf-8") as f:
                    f.write(content_text)
                logger.info(f"Successfully saved content for {website_name} to {site_filename}")
                
                # Verify file was created
                if os.path.exists(site_filename):
                    file_size = os.path.getsize(site_filename)
                    logger.info(f"File created successfully. Size: {file_size} bytes")
                else:
                    logger.error(f"File was not created: {site_filename}")
                    
            except Exception as e:
                logger.error(f"Failed to write file {site_filename}: {e}")
                return None
            
            return content_text

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching content for {website_name}: {e}")
            return None
            
    def calculate_hash(self, content):
        """
        Calculate the MD5 hash of the given text content.
        Used for a quick check if content has changed.

        Args:
            content (str): The text content to hash.

        Returns:
            str or None: The hex digest of the MD5 hash, or None if content is None.
        """
        if content is None:
            return None
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def calculate_content_change(self, old_content, new_content):
        """
        Compare old and new content to calculate the percentage of change
        and generate a textual description of the differences (a "diff").

        Args:
            old_content (str): The previous version of the content.
            new_content (str): The current version of the content.

        Returns:
            tuple: (float: change_percentage, str: change_description)
        """
        if old_content is None or new_content is None:
            return 0.0, "One of the contents is missing for comparison."

        # Split content into lines for difflib.
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        d = difflib.Differ() # Initialize the Differ object.
        # Compare the lines and generate a list of diff lines.
        # Lines will be prefixed with:
        #   '- ': line unique to sequence 1 (old_content)
        #   '+ ': line unique to sequence 2 (new_content)
        #   '  ': line common to both sequences
        #   '? ': line not present in either input sequence (used for highlighting differences within lines)
        diff_lines = list(d.compare(old_lines, new_lines))
        
        # Join the diff lines into a single string for the description.
        # Using the full diff provides more context.
        change_description = "".join(diff_lines)

        # Calculate a similarity ratio using SequenceMatcher.
        # ratio() returns a float in [0, 1], where 1 means identical.
        s = difflib.SequenceMatcher(None, old_content, new_content)
        # Percentage change is (1 - similarity_ratio) * 100.
        change_percentage = (1 - s.ratio()) * 100
        
        return change_percentage, change_description

    def translate_text(self, text, target_language='en'):
        """
        Translate the given text to the target language (default English)
        using the initialized translator.
        
        If the text is detected as Chinese, filters out non-Chinese characters before translation.

        Args:
            text (str): The text to translate.
            target_language (str): The target language code (e.g., 'en').

        Returns:
            str: The translated text, or an error message/original text if translation fails.
        """
        if not self.translator: # Check if the translator was successfully initialized
            logger.warning("Translator not initialized. Skipping translation.")
            return "Translation unavailable (translator not initialized)."
        if not text or text.strip() == "": # No need to translate empty strings
            return "" 
        try:
            # Check if text contains Chinese characters
            contains_chinese = bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))
            
            if contains_chinese:
                logger.info("Chinese text detected, filtering out non-Chinese characters")
                # Keep only Chinese characters and basic punctuation
                chinese_only = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\s.,!?;:]', '', text)
                # If significant content remains after filtering
                if len(chinese_only.strip()) > 0:
                    text = chinese_only
                    logger.info(f"Filtered Chinese text length: {len(text)} characters")
                else:
                    logger.warning("After filtering, insufficient Chinese content remains")
            
            # Google Translate API (and others) often have character limits for a single request.
            # Truncate very long texts to avoid errors.
            max_len = 4500 
            if len(text) > max_len:
                logger.warning(f"Text too long for translation ({len(text)} chars), truncating to {max_len}.")
                text = text[:max_len] + "\n[...truncated...]" # Append a truncation notice

            translated_text = self.translator.translate(text)
            return translated_text
        except Exception as e: # Handle errors during the translation API call
            logger.error(f"Error during translation: {e}")
            return f"Translation failed: {str(e)}" # Return an error message

    def _log_change_to_todays_file(self, website_name, original_changes, translated_changes):
        """
        Append the detected changes (original and translated) for a website
        to the daily consolidated changes file (e.g., "TodaysChanges.txt").
        Removes HTML/CSS markup from the content before logging.

        Args:
            website_name (str): Name of the website where changes were detected.
            original_changes (str): The diff description in its original language.
            translated_changes (str): The translated diff description (if available).
        """
        filename = self.config.get("todays_changes_file", "TodaysChanges.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Clean the changes to remove HTML/CSS markup
        def clean_markup(text):
            if not text:
                return ""
            # Use BeautifulSoup to remove HTML tags
            try:
                soup = BeautifulSoup(text, "html.parser")
                # Remove script and style elements completely
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()
                text = soup.get_text()
                
                # Remove CSS selectors and other common markup patterns
                text = re.sub(r'<[^>]*>', '', text)  # Remove any remaining HTML tags
                text = re.sub(r'\{[^\}]*\}', '', text)  # Remove CSS blocks
                text = re.sub(r'@\w+\s*[^;]*;', '', text)  # Remove CSS at-rules
                
                return text.strip()
            except Exception as e:
                logger.error(f"Error cleaning markup: {e}")
                return text  # Return original if cleaning fails
        
        # Clean both original and translated changes
        cleaned_original = clean_markup(original_changes)
        cleaned_translated = clean_markup(translated_changes) if translated_changes else ""
        
        # Construct the log entry with clear sections for original and translated changes.
        log_entry = f"--- Website: {website_name} ---\n"
        log_entry += f"Timestamp: {timestamp}\n\n"
        log_entry += "Original Changes:\n"
        log_entry += "--------------------------------------\n"
        log_entry += f"{cleaned_original}\n"
        log_entry += "--------------------------------------\n\n"
        
        if cleaned_translated:
            log_entry += f"Translated Changes (to {self.translator.target if self.translator else 'en'}):\n"
            log_entry += "--------------------------------------\n"
            log_entry += f"{cleaned_translated}\n"
            log_entry += "--------------------------------------\n"
        log_entry += "---\n\n"  # Separator for the next entry
        
        try:
            # Append the entry to the file. 'a' mode for appending.
            with open(filename, "a", encoding="utf-8") as f:
                f.write(log_entry)
            logger.info(f"Changes for {website_name} logged to {filename}")
        except Exception as e:
            logger.error(f"Failed to write changes to {filename}: {e}")

    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text using the initialized sentiment analyzer.

        Args:
            text (str): The text to analyze.

        Returns:
            dict: A dictionary containing 'label' (e.g., 'POSITIVE', 'NEGATIVE') 
                  and 'score' (confidence), or default/error values.
        """
        if not self.sentiment_analyzer: # Check if analyzer is available
            logger.warning("Sentiment analyzer not initialized.")
            return {"label": "NEUTRAL", "score": 0.0} # Default neutral sentiment
        if not text or text.isspace(): # No sentiment for empty text
            return {"label": "NEUTRAL", "score": 0.0}
        try:
            # Many NLP models have input length limits. Truncate if necessary.
            # This is a simple truncation based on word count. More sophisticated methods exist.
            max_length = 512 
            if len(text.split()) > max_length: 
                 text = " ".join(text.split()[:max_length])

            result = self.sentiment_analyzer(text)
            # The pipeline might return a list of results; we usually want the first one.
            return result[0] if isinstance(result, list) and result else {"label": "UNKNOWN", "score": 0.0}
        except Exception as e: # Handle errors from the sentiment analysis model
            logger.error(f"Sentiment analysis failed: {e}")
            return {"label": "ERROR", "score": 0.0} # Return an error state

    def categorize_content(self, text):
        """
        Placeholder for content categorization.
        In a real application, this could involve more complex NLP techniques
        like topic modeling, keyword extraction, or classification models.

        Args:
            text (str): The text to categorize.

        Returns:
            list: A list of category labels (e.g., ["news", "sports"]).
        """
        logger.debug("categorize_content is a placeholder.")
        return ["general"] # Default to a single "general" category

    def check_alert_conditions(self, website_config, change_percentage, sentiment_result, categories, change_description):
        """
        Check if the detected changes meet any predefined alert conditions
        (e.g., change percentage exceeds threshold).

        Args:
            website_config (dict): Configuration for the website.
            change_percentage (float): The percentage of content that changed.
            sentiment_result (dict): The sentiment analysis result.
            categories (list): List of categories for the content.
            change_description (str): The textual diff of changes.
        """
        website_name = website_config["name"]
        alert_settings = self.config.get("alert_settings", {}) # Get alert settings from config
        min_change_percent = alert_settings.get("min_change_percent", 5) # Default to 5% if not set

        alert_triggered = False
        reason = "" # Store the reason(s) for the alert

        # Primary alert condition: change percentage
        if change_percentage >= min_change_percent:
            alert_triggered = True
            reason = f"Change percentage ({change_percentage:.2f}%) met/exceeded threshold ({min_change_percent}%)."
            logger.info(f"Alert condition met for {website_name}: {reason}")
        
        # --- Example of adding more conditions (currently commented out) ---
        # You could extend this to check for specific sentiment scores, keywords, or categories.
        # sentiment_thresholds = self.config.get("alert_thresholds", {})
        # if sentiment_result["label"] == "NEGATIVE" and sentiment_result["score"] >= sentiment_thresholds.get("negative", 0.7):
        #     if not alert_triggered: # If not already triggered by percentage
        #         reason = f"Negative sentiment ({sentiment_result['score']:.2f}) met/exceeded threshold."
        #     else: # Append to existing reason
        #         reason += f" Also, negative sentiment ({sentiment_result['score']:.2f}) met/exceeded threshold."
        #     alert_triggered = True
        #     logger.info(f"Alert condition met for {website_name}: Negative sentiment.")

        if alert_triggered:
            # If any condition is met, trigger the alert mechanism.
            self.trigger_alert(website_config, change_percentage, sentiment_result, categories, change_description, reason)
        else:
            logger.info(f"No alert conditions met for {website_name}.")

    def trigger_alert(self, website_config, change_percentage, sentiment_result, categories, change_description, reason):
        """
        Trigger an alert. Currently, this logs a warning and can use text-to-speech.
        This could be extended to send emails, push notifications, etc.

        Args:
            website_config (dict): Configuration for the website.
            change_percentage (float): The percentage of content that changed.
            sentiment_result (dict): The sentiment analysis result.
            categories (list): List of categories for the content.
            change_description (str): The textual diff of changes.
            reason (str): The reason why the alert was triggered.
        """
        website_name = website_config["name"]
        # Construct a detailed alert message.
        alert_message = (
            f"ALERT for {website_name}: {reason}\n"
            f"Change: {change_percentage:.2f}%\n"
            f"Sentiment: {sentiment_result['label']} (Score: {sentiment_result['score']:.2f})\n"
            f"Categories: {', '.join(categories)}\n"
            # Optionally include a snippet of the change description (can be very long).
            # f"Change Details:\n{change_description[:500]}..." 
        )
        logger.warning(f"--- ALERT --- \n{alert_message}\n------------") # Log as a warning

        # If speech alerts are enabled in config and TTS engine is available.
        if self.config.get("alert_settings", {}).get("speech_enabled", False) and self.tts_engine:
            try:
                # Create a concise message for speech.
                speech_text = f"Alert for {website_name}. {reason}"
                self.tts_engine.say(speech_text)
                self.tts_engine.runAndWait() # Wait for speech to complete
            except Exception as e: # Handle errors from the TTS engine
                logger.error(f"Text-to-speech alert failed for {website_name}: {e}")
        
    def check_website(self, website_config):
        """
        Perform the full check for a single website:
        1. Load its last known content.
        2. Fetch its current content.
        3. Compare for changes.
        4. If changes are found:
           - Calculate diff and percentage.
           - Translate changes (if configured).
           - Log changes to the daily file.
           - Analyze sentiment and categorize.
           - Check and trigger alerts.

        Args:
            website_config (dict): Configuration for the website to check.
        """
        website_name = website_config["name"]
        logger.info(f"Starting check for website: {website_name}")

        # 1. Load the last known content from its archive file.
        last_content_path = self._get_latest_saved_file(website_name)
        last_content = None
        if last_content_path:
            try:
                with open(last_content_path, "r", encoding="utf-8") as f:
                    last_content = f.read()
                logger.info(f"Loaded last content for {website_name} from {last_content_path}")
            except Exception as e:
                logger.error(f"Error reading last content file {last_content_path} for {website_name}: {e}")
        
        # 2. Fetch the current content. This also saves it to a new archive file.
        current_content = self.fetch_website_content(website_config)
        if current_content is None: # If fetching failed
            logger.error(f"Failed to fetch current content for {website_name}. Skipping further checks.")
            return

        # If this is the first time checking (no last_content), save current as baseline and exit.
        if last_content is None:
            logger.info(f"No previous content found for {website_name}. Current content saved as baseline.")
            # The fetch_website_content method already saved the current_content.
            return

        # 3. Compare content using hashes for a quick check.
        last_hash = self.calculate_hash(last_content)
        current_hash = self.calculate_hash(current_content)

        if last_hash == current_hash:
            logger.info(f"No changes detected for {website_name} (hash match).")
            return # Exit if hashes are the same (content likely identical)
        
        # 4. If hashes differ, perform a detailed comparison.
        logger.info(f"Content has changed for {website_name}. Calculating differences.")
        change_percentage, change_description = self.calculate_content_change(last_content, current_content)

        # Heuristic: if percentage is very low and diff shows no actual additions/deletions,
        # it might be minor whitespace or formatting changes not worth reporting.
        if change_percentage < 0.01 and not any(line.startswith(('+', '-')) for line in change_description.splitlines()):
            logger.info(f"Negligible or no textual changes detected for {website_name} after diff. Hashes differed but diff is minimal.")
            return

        logger.info(f"Change detected for {website_name}: {change_percentage:.2f}%")

        # Translate the change description if configured and if there are changes.
        translated_description = ""
        if website_config.get("translate_changes_to_en", True) and change_description.strip():
            logger.info(f"Translating changes for {website_name}...")
            translated_description = self.translate_text(change_description)
        
        # Log the original and translated changes to the consolidated daily file.
        self._log_change_to_todays_file(website_name, change_description, translated_description)
        
        # Perform sentiment analysis and categorization on the *new* content.
        sentiment_result = self.analyze_sentiment(current_content)
        categories = self.categorize_content(current_content) # Placeholder
        
        # Check if the changes warrant an alert.
        self.check_alert_conditions(website_config, change_percentage, sentiment_result, categories, change_description)

    def run_checks(self):
        """
        Run the checking process for all websites listed in the configuration once.
        """
        logger.info("Starting a single run of all website checks...")
        if not self.config.get("websites"):
            logger.warning("No websites configured in config file.")
            return
        
        for website_config in self.config["websites"]:
            try:
                self.check_website(website_config)
            except Exception as e:
                logger.error(f"Unhandled error during check for website {website_config.get('name', 'Unknown')}: {e}", exc_info=True)
            logger.info(f"Finished check for website: {website_config.get('name', 'Unknown')}")
        logger.info("All website checks completed for this run.")

    def start_service(self, default_interval_minutes=60):
        """
        Start the web scraper as a continuous service, checking websites periodically.
        """
        logger.info("Web scraper service starting...")
        
        # Determine the check interval.
        # This simple version uses a single interval for all checks.
        # A more advanced version could respect individual site intervals.
        try:
            # Attempt to get a global interval from config, e.g. config["global_check_interval_minutes"]
            # For now, we'll use a passed default or a hardcoded one.
            interval = int(self.config.get("global_check_interval_minutes", default_interval_minutes))
        except ValueError:
            interval = default_interval_minutes
        
        logger.info(f"Scheduling checks to run every {interval} minutes.")
        schedule.every(interval).minutes.do(self.run_checks)
        
        logger.info(f"Scheduler started. Will run checks every {interval} minutes. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user (Ctrl+C).")
            print("\nWeb scraper service stopped.")

    def add_website(self, name, url, selector, interval, importance, translate=True):
        """Add a new website to the configuration."""
        if not self.config.get("websites"):
            self.config["websites"] = []
        
        # Check if website with the same name already exists
        if any(site['name'] == name for site in self.config["websites"]):
            logger.warning(f"Website with name '{name}' already exists. Skipping add.")
            print(f"Error: Website with name '{name}' already exists.")
            return

        new_site = {
            "name": name,
            "url": url,
            "selector": selector if selector else "", # Ensure selector is a string
            "check_interval_minutes": int(interval),
            "importance": importance,
            "translate_changes_to_en": translate
        }
        self.config["websites"].append(new_site)
        self.save_config()
        logger.info(f"Added website '{name}' to configuration.")
        print(f"Website '{name}' added successfully.")

    def remove_website(self, name):
        """Remove a website from the configuration."""
        initial_len = len(self.config.get("websites", []))
        self.config["websites"] = [site for site in self.config.get("websites", []) if site["name"] != name]
        if len(self.config.get("websites", [])) < initial_len:
            self.save_config()
            logger.info(f"Removed website '{name}' from configuration.")
            print(f"Website '{name}' removed successfully.")
        else:
            logger.warning(f"Website with name '{name}' not found for removal.")
            print(f"Error: Website '{name}' not found.")

    def update_alert_settings(self, speech_enabled=None, min_change_percent=None, 
                              negative_threshold=None, positive_threshold=None):
        """Update alert settings in the configuration."""
        if "alert_settings" not in self.config:
            self.config["alert_settings"] = {}
        if "alert_thresholds" not in self.config:
            self.config["alert_thresholds"] = {}

        if speech_enabled is not None:
            self.config["alert_settings"]["speech_enabled"] = speech_enabled
            logger.info(f"Speech alerts set to: {speech_enabled}")
        if min_change_percent is not None:
            self.config["alert_settings"]["min_change_percent"] = float(min_change_percent)
            logger.info(f"Min change percent for alerts set to: {min_change_percent}")
        if negative_threshold is not None:
            self.config["alert_thresholds"]["negative"] = float(negative_threshold)
            logger.info(f"Negative sentiment threshold set to: {negative_threshold}")
        if positive_threshold is not None:
            self.config["alert_thresholds"]["positive"] = float(positive_threshold)
            logger.info(f"Positive sentiment threshold set to: {positive_threshold}")
            
        self.save_config()
        print("Alert settings updated.")

# --- Main Execution Block ---
if __name__ == "__main__":
    # Create an instance of the WebScraper.
    scraper = WebScraper()
    
    # Perform a single run of checks for all configured websites.
    scraper.run_checks()
    
    # --- Optional: Periodic Scheduling (currently commented out) ---
    # To run checks periodically (e.g., every hour), you can use a library like `schedule`
    # or an OS-level scheduler like cron (Linux/macOS) or Task Scheduler (Windows).
    
    # Example using the `schedule` library:
    # import schedule # Make sure to `pip install schedule`
    # check_interval_all_sites_minutes = 60 # Define how often to run all checks
    # schedule.every(check_interval_all_sites_minutes).minutes.do(scraper.run_checks)
    # logger.info(f"Scheduler started. Will run checks every {check_interval_all_sites_minutes} minutes. Press Ctrl+C to exit.")
    # try:
    #     while True: # Keep the script running to allow the scheduler to work.
    #         schedule.run_pending() # Check if any scheduled tasks are due.
    #         time.sleep(1) # Wait a second before checking again.
    # except KeyboardInterrupt:
    #     logger.info("Scheduler stopped by user (Ctrl+C).")