import requests
from bs4 import BeautifulSoup
import hashlib
import json
import time
import os
import re
from datetime import datetime
import sqlite3
import schedule
from transformers import pipeline
import pyttsx3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webscraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class WebScraper:
    def __init__(self, config_file="config.json", database_file="website_data.db"):
        """Initialize the web scraper with configurations."""
        self.config_file = config_file
        self.database_file = database_file
        self.load_config()
        self.setup_database()
        
        # Initialize sentiment analysis pipeline
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        
    def load_config(self):
        """Load configuration from JSON file or create default if not exists."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
        else:
            # Default configuration
            self.config = {
                "websites": [
                    {
                        "name": "Example News",
                        "url": "https://example.com/news",
                        "selector": "div.content",
                        "check_interval_minutes": 60,
                        "importance": "high"
                    }
                ],
                "alert_thresholds": {
                    "negative": 0.7,  # Alert if sentiment is more negative than this
                    "positive": 0.8   # Alert if sentiment is more positive than this
                },
                "alert_settings": {
                    "speech_enabled": True,
                    "min_change_percent": 10  # Minimum percentage change to trigger alert
                }
            }
            self.save_config()
            logger.info(f"Default configuration created and saved to {self.config_file}")
            
    def save_config(self):
        """Save current configuration to JSON file."""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)
        logger.info(f"Configuration saved to {self.config_file}")
            
    def setup_database(self):
        """Set up SQLite database to store website content and changes."""
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Create table for website content history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS website_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_name TEXT,
            url TEXT,
            content_hash TEXT,
            content_text TEXT,
            capture_time TIMESTAMP,
            sentiment_score REAL,
            sentiment_label TEXT,
            categorization TEXT
        )
        ''')
        
        # Create table for detected changes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_name TEXT,
            url TEXT,
            previous_hash TEXT,
            new_hash TEXT,
            change_description TEXT,
            change_percentage REAL,
            sentiment_score REAL,
            sentiment_label TEXT,
            categorization TEXT,
            detection_time TIMESTAMP,
            alerted INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database setup complete")
        
    def fetch_website_content(self, website_config):
        """Fetch content from a website based on configuration."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(website_config["url"], headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            if "selector" in website_config and website_config["selector"]:
                content = soup.select(website_config["selector"])
                content_text = "\n".join([elem.get_text(strip=True) for elem in content])
            else:
                # If no selector is provided, get the body content
                content = soup.body
                content_text = content.get_text(strip=True) if content else ""
                
            return content_text
        except Exception as e:
            logger.error(f"Error fetching {website_config['url']}: {str(e)}")
            return None
            
    def calculate_hash(self, content):
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text and return score and label."""
        try:
            # Truncate text if too long (transformers typically has a token limit)
            if len(text) > 1000:
                text = text[:1000]
                
            result = self.sentiment_analyzer(text)[0]
            return {
                "score": result["score"],
                "label": result["label"]
            }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"score": 0.5, "label": "NEUTRAL"}
            
    def categorize_content(self, text):
        """Categorize content based on keywords and patterns."""
        categories = []
        
        # Simple keyword-based categorization
        keyword_categories = {
            "technology": ["software", "hardware", "tech", "ai", "artificial intelligence", "computer"],
            "business": ["stock", "market", "finance", "company", "investor", "profit"],
            "politics": ["government", "election", "president", "vote", "policy", "democratic", "republican"],
            "health": ["covid", "disease", "healthcare", "patient", "doctor", "medical", "vaccine"],
            "environment": ["climate", "weather", "pollution", "sustainable", "renewable", "green"]
        }
        
        text_lower = text.lower()
        for category, keywords in keyword_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    categories.append(category)
                    break
        
        return list(set(categories)) if categories else ["uncategorized"]
        
    def calculate_content_change(self, old_content, new_content):
        """Calculate the percentage of content change and describe changes."""
        if not old_content or not old_content.strip():
            return 100.0, "New content added"
        
        # Simple difference calculation based on character count
        total_chars = len(old_content)
        if total_chars == 0:
            return 100.0, "New content added"
            
        # Use difflib for more sophisticated diff calculation
        import difflib
        diff = difflib.ndiff(old_content.splitlines(), new_content.splitlines())
        changes = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]
        
        change_chars = sum(len(line) for line in changes)
        change_percentage = (change_chars / total_chars) * 100
        
        # Generate change description
        added_lines = [line[2:] for line in changes if line.startswith('+ ')]
        removed_lines = [line[2:] for line in changes if line.startswith('- ')]
        
        description = []
        if added_lines:
            added_sample = added_lines[0][:50] + "..." if len(added_lines[0]) > 50 else added_lines[0]
            description.append(f"Added: {added_sample}")
        if removed_lines:
            removed_sample = removed_lines[0][:50] + "..." if len(removed_lines[0]) > 50 else removed_lines[0]
            description.append(f"Removed: {removed_sample}")
            
        return change_percentage, " | ".join(description)
        
    def check_website(self, website_config):
        """Check a website for changes and process if found."""
        website_name = website_config["name"]
        url = website_config["url"]
        logger.info(f"Checking website: {website_name} ({url})")
        
        content = self.fetch_website_content(website_config)
        if not content:
            logger.warning(f"No content fetched from {website_name}")
            return
            
        content_hash = self.calculate_hash(content)
        
        # Get the last recorded content for this website
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content_hash, content_text FROM website_content WHERE website_name = ? ORDER BY capture_time DESC LIMIT 1", 
            (website_name,)
        )
        last_record = cursor.fetchone()
        
        # Check if content has changed
        if last_record and last_record[0] == content_hash:
            logger.info(f"No changes detected for {website_name}")
            conn.close()
            return
            
        # Analyze sentiment
        sentiment_result = self.analyze_sentiment(content)
        
        # Categorize content
        categories = self.categorize_content(content)
        categories_json = json.dumps(categories)
        
        # Save current content to database
        current_time = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO website_content (website_name, url, content_hash, content_text, capture_time, sentiment_score, sentiment_label, categorization) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (website_name, url, content_hash, content, current_time, sentiment_result["score"], sentiment_result["label"], categories_json)
        )
        
        # If this is the first scan, no need to record a change
        if not last_record:
            conn.commit()
            conn.close()
            logger.info(f"Initial content recorded for {website_name}")
            return
            
        # Calculate and record the change
        change_percentage, change_description = self.calculate_content_change(last_record[1], content)
        
        cursor.execute(
            "INSERT INTO content_changes (website_name, url, previous_hash, new_hash, change_description, change_percentage, sentiment_score, sentiment_label, categorization, detection_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (website_name, url, last_record[0], content_hash, change_description, change_percentage, sentiment_result["score"], sentiment_result["label"], categories_json, current_time)
        )
        
        change_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Change detected for {website_name}: {change_percentage:.2f}% changed")
        
        # Check if alert should be triggered
        self.check_alert_conditions(website_config, change_id, change_percentage, sentiment_result, categories)
        
    def check_alert_conditions(self, website_config, change_id, change_percentage, sentiment_result, categories):
        """Check if alert conditions are met for a detected change."""
        # Skip if change percentage is below threshold
        min_change_percent = self.config["alert_settings"].get("min_change_percent", 10)
        if change_percentage < min_change_percent:
            logger.info(f"Change below threshold ({change_percentage:.2f}% < {min_change_percent}%), no alert triggered")
            return
            
        # Check sentiment thresholds
        alert_thresholds = self.config["alert_thresholds"]
        sentiment_score = sentiment_result["score"]
        sentiment_label = sentiment_result["label"]
        
        should_alert = False
        alert_reason = []
        
        if sentiment_label == "NEGATIVE" and sentiment_score > alert_thresholds["negative"]:
            should_alert = True
            alert_reason.append(f"High negative sentiment ({sentiment_score:.2f})")
            
        if sentiment_label == "POSITIVE" and sentiment_score > alert_thresholds["positive"]:
            should_alert = True
            alert_reason.append(f"High positive sentiment ({sentiment_score:.2f})")
            
        # Check importance-based alerts
        importance = website_config.get("importance", "medium").lower()
        if importance == "high":
            should_alert = True
            alert_reason.append(f"High importance website")
            
        if should_alert:
            self.trigger_alert(website_config, change_id, change_percentage, sentiment_result, categories, ", ".join(alert_reason))
            
    def trigger_alert(self, website_config, change_id, change_percentage, sentiment_result, categories, reason):
        """Trigger an alert for a website change."""
        website_name = website_config["name"]
        
        # Mark as alerted in database
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE content_changes SET alerted = 1 WHERE id = ?", (change_id,))
        conn.commit()
        conn.close()
        
        # Format alert message
        alert_message = f"Alert for {website_name}: {change_percentage:.1f}% content changed. "
        alert_message += f"Sentiment: {sentiment_result['label']} ({sentiment_result['score']:.2f}). "
        alert_message += f"Categories: {', '.join(categories)}. "
        alert_message += f"Reason: {reason}"
        
        logger.info(f"ALERT: {alert_message}")
        
        # Text-to-speech alert if enabled
        if self.config["alert_settings"].get("speech_enabled", False):
            try:
                self.tts_engine.say(alert_message)
                self.tts_engine.runAndWait()
            except Exception as e:
                logger.error(f"Text-to-speech error: {str(e)}")
                
    def run_scheduled_checks(self):
        """Run all scheduled website checks."""
        for website_config in self.config["websites"]:
            try:
                self.check_website(website_config)
            except Exception as e:
                logger.error(f"Error checking {website_config['name']}: {str(e)}")
                
    def setup_schedules(self):
        """Set up scheduling for all websites."""
        for website_config in self.config["websites"]:
            interval_minutes = website_config.get("check_interval_minutes", 60)
            
            # Create a closure to capture website_config
            def create_job(site_config):
                return lambda: self.check_website(site_config)
                
            job = create_job(website_config)
            
            # Schedule the job to run at the specified interval
            schedule.every(interval_minutes).minutes.do(job)
            logger.info(f"Scheduled {website_config['name']} to check every {interval_minutes} minutes")
            
    def add_website(self, name, url, selector=None, check_interval_minutes=60, importance="medium"):
        """Add a new website to monitor."""
        new_website = {
            "name": name,
            "url": url,
            "selector": selector,
            "check_interval_minutes": check_interval_minutes,
            "importance": importance
        }
        
        self.config["websites"].append(new_website)
        self.save_config()
        
        # Perform initial check
        self.check_website(new_website)
        
        # Update schedules
        self.setup_schedules()
        
        logger.info(f"Added new website: {name} ({url})")
        
    def remove_website(self, name):
        """Remove a website from monitoring."""
        self.config["websites"] = [w for w in self.config["websites"] if w["name"] != name]
        self.save_config()
        
        # Reset schedules
        schedule.clear()
        self.setup_schedules()
        
        logger.info(f"Removed website: {name}")
        
    def update_alert_settings(self, speech_enabled=None, min_change_percent=None, 
                             negative_threshold=None, positive_threshold=None):
        """Update alert settings."""
        if speech_enabled is not None:
            self.config["alert_settings"]["speech_enabled"] = speech_enabled
            
        if min_change_percent is not None:
            self.config["alert_settings"]["min_change_percent"] = min_change_percent
            
        if negative_threshold is not None:
            self.config["alert_thresholds"]["negative"] = negative_threshold
            
        if positive_threshold is not None:
            self.config["alert_thresholds"]["positive"] = positive_threshold
            
        self.save_config()
        logger.info("Alert settings updated")
        
    def get_recent_changes(self, limit=10):
        """Get recent content changes."""
        conn = sqlite3.connect(self.database_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM content_changes 
            ORDER BY detection_time DESC 
            LIMIT ?
        """, (limit,))
        
        changes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return changes
        
    def get_sentiment_stats(self, days=7):
        """Get sentiment statistics for a time period."""
        conn = sqlite3.connect(self.database_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calculate date threshold
        from datetime import datetime, timedelta
        threshold_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT website_name, 
                   AVG(sentiment_score) as avg_score,
                   COUNT(*) as change_count,
                   SUM(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) as positive_count,
                   SUM(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_count,
                   SUM(CASE WHEN sentiment_label = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_count
            FROM content_changes
            WHERE detection_time > ?
            GROUP BY website_name
        """, (threshold_date,))
        
        stats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return stats
        
    def start(self):
        """Start the web scraper service."""
        logger.info("Starting web scraper service")
        
        # Setup schedules
        self.setup_schedules()
        
        # Run initial check for all websites
        self.run_scheduled_checks()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping web scraper service")


if __name__ == "__main__":
    scraper = WebScraper()
    scraper.start()
