import requests
from bs4 import BeautifulSoup
import hashlib
import json
import time
import os
import re
import glob
from datetime import datetime
import sqlite3
import schedule
from transformers import pipeline
import pyttsx3
import logging
import difflib

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
        """Fetch content from a website based on configuration.
        Downloads the entire website content as text if no selector is specified."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(website_config["url"], headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements as they don't contain visible text
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
                
            # Store the entire website as text if no selector is provided
            if "selector" in website_config and website_config["selector"]:
                content = soup.select(website_config["selector"])
                if not content:
                    logger.warning(f"Selector '{website_config['selector']}' did not match any content on {website_config['url']}. Using full page content instead.")
                    content_text = soup.get_text(separator="\n", strip=True)
                else:
                    content_text = "\n".join([elem.get_text(separator="\n", strip=True) for elem in content])
            else:
                # Get the full page content as text
                content_text = soup.get_text(separator="\n", strip=True)
                
            # Save to a text file for archival purposes
            site_filename = self._get_site_filename(website_config["name"])
            with open(site_filename, "w", encoding="utf-8") as f:
                f.write(content_text)
            
            logger.info(f"Saved website content to {site_filename} ({len(content_text)} characters)")
                
            return content_text
        except Exception as e:
            logger.error(f"Error fetching {website_config['url']}: {str(e)}")
            return None
            
    def _get_site_filename(self, website_name):
        """Generate a filename for storing website content."""
        # Create archives directory if it doesn't exist
        os.makedirs("website_archives", exist_ok=True)
        
        # Create a safe filename from the website name
        safe_name = re.sub(r'[^\w\-_]', '_', website_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"website_archives/{safe_name}_{timestamp}.txt"
            
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
        """Calculate the percentage of content change and describe changes between old and new content."""
        if not old_content or not old_content.strip():
            return 100.0, "New content added"
        
        # Use difflib for sophisticated diff calculation
        import difflib
        
        # Split content into lines
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Create a unified diff
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        # Extract changes (lines starting with + or -)
        changes = [line for line in diff if line.startswith('+') or line.startswith('-')]
        added = [line for line in changes if line.startswith('+')]
        removed = [line for line in changes if line.startswith('-')]
        
        # Calculate change percentage based on number of modified lines
        total_lines = len(old_lines)
        if total_lines == 0:
            return 100.0, "New content added"
            
        change_percentage = (len(changes) / (total_lines * 2)) * 100  # Multiply by 2 to normalize percentage
        change_percentage = min(change_percentage, 100.0)  # Cap at 100%
        
        # Generate a detailed change description
        description = []
        
        # Show number of changes
        description.append(f"{len(added)} lines added, {len(removed)} lines removed")
        
        # Sample of added content (up to 3 examples)
        if added:
            description.append("Added content samples:")
            for i, line in enumerate(added[:3]):  # Limit to 3 examples
                if len(line) > 2:  # Skip the '+' prefix
                    sample = line[2:].strip()
                    if len(sample) > 50:
                        sample = sample[:47] + "..."
                    description.append(f"+ {sample}")
                if i >= 2 and len(added) > 3:  # Show indication of more changes
                    description.append(f"+ ...and {len(added) - 3} more additions")
                    break
                    
        # Sample of removed content (up to 3 examples)
        if removed:
            description.append("Removed content samples:")
            for i, line in enumerate(removed[:3]):  # Limit to 3 examples
                if len(line) > 2:  # Skip the '-' prefix
                    sample = line[2:].strip()
                    if len(sample) > 50:
                        sample = sample[:47] + "..."
                    description.append(f"- {sample}")
                if i >= 2 and len(removed) > 3:  # Show indication of more changes
                    description.append(f"- ...and {len(removed) - 3} more removals")
                    break
                    
        # Save the detailed diff to a file
        self._save_diff_file(old_content, new_content, diff)
            
        return change_percentage, "\n".join(description)
        
    def _save_diff_file(self, old_content, new_content, diff):
        """Save detailed diff information to a file for later reference."""
        os.makedirs("diffs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        diff_filename = f"diffs/diff_{timestamp}.txt"
        
        with open(diff_filename, "w", encoding="utf-8") as f:
            f.write("==== DETAILED CONTENT CHANGES ====\n\n")
            f.write("---- DIFF OUTPUT ----\n")
            for line in diff:
                f.write(line + "\n")
                
        logger.info(f"Saved detailed diff to {diff_filename}")
        return diff_filename
        
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
        
        # Get the path to the latest saved text file
        latest_file = self._get_latest_saved_file(website_name)
        
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
            """INSERT INTO content_changes 
               (website_name, url, previous_hash, new_hash, change_description, 
                change_percentage, sentiment_score, sentiment_label, categorization, detection_time) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (website_name, url, last_record[0], content_hash, change_description, 
             change_percentage, sentiment_result["score"], sentiment_result["label"], 
             categories_json, current_time)
        )
        
        change_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Change detected for {website_name}: {change_percentage:.2f}% changed")
        
        # Check if alert should be triggered
        self.check_alert_conditions(website_config, change_id, change_percentage, sentiment_result, categories, change_description)
        
    def _get_latest_saved_file(self, website_name):
        """Get the path to the latest saved text file for a website."""
        safe_name = re.sub(r'[^\w\-_]', '_', website_name)
        pattern = f"website_archives/{safe_name}_*.txt"
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files[0]
        
    def check_alert_conditions(self, website_config, change_id, change_percentage, sentiment_result, categories, change_description):
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
            self.trigger_alert(website_config, change_id, change_percentage, sentiment_result, categories, change_description, ", ".join(alert_reason))
            
    def trigger_alert(self, website_config, change_id, change_percentage, sentiment_result, categories, change_description, reason):
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
        
        # Add a summary of changes
        change_summary = self._get_change_summary(change_description)
        if change_summary:
            alert_message += f"\n\nChange summary: {change_summary}"
        
        logger.info(f"ALERT: {alert_message}")
        
        # Text-to-speech alert if enabled
        if self.config["alert_settings"].get("speech_enabled", False):
            try:
                # Create a shorter version for speech
                speech_message = f"Alert for {website_name}. {change_percentage:.1f} percent content changed. "
                speech_message += f"Sentiment is {sentiment_result['label']}. "
                
                self.tts_engine.say(speech_message)
                self.tts_engine.runAndWait()
            except Exception as e:
                logger.error(f"Text-to-speech error: {str(e)}")
                
    def _get_change_summary(self, change_description):
        """Extract a concise summary from the change description."""
        # If change description is already short, return it directly
        if len(change_description) < 100:
            return change_description
            
        # Otherwise extract just the first few lines
        lines = change_description.split('\n')
        summary_lines = []
        
        # Get the first line, which has the count of additions/removals
        if lines:
            summary_lines.append(lines[0])
            
        # Get the first sample of added content
        added_index = -1
        for i, line in enumerate(lines):
            if line == "Added content samples:":
                added_index = i
                break
                
        if added_index >= 0 and added_index + 1 < len(lines):
            summary_lines.append("Sample addition: " + lines[added_index + 1][2:])
            
        # Get the first sample of removed content
        removed_index = -1
        for i, line in enumerate(lines):
            if line == "Removed content samples:":
                removed_index = i
                break
                
        if removed_index >= 0 and removed_index + 1 < len(lines):
            summary_lines.append("Sample removal: " + lines[removed_index + 1][2:])
            
        return " | ".join(summary_lines)
                
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