import argparse
import json
import logging
from web_scraper import WebScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Web Scraper with Change Detection & Sentiment Analysis")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the scraper service")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Perform a check now")
    check_parser.add_argument("--all", action="store_true", help="Check all websites")
    check_parser.add_argument("--name", type=str, help="Name of the website to check")
    
    # Add website command
    add_parser = subparsers.add_parser("add", help="Add a new website to monitor")
    add_parser.add_argument("--name", type=str, required=True, help="Name of the website")
    add_parser.add_argument("--url", type=str, required=True, help="URL of the website")
    add_parser.add_argument("--selector", type=str, help="CSS selector for content")
    add_parser.add_argument("--interval", type=int, default=60, help="Check interval in minutes")
    add_parser.add_argument("--importance", type=str, default="medium", 
                           choices=["low", "medium", "high"], help="Importance level")
    
    # Remove website command
    remove_parser = subparsers.add_parser("remove", help="Remove a website from monitoring")
    remove_parser.add_argument("--name", type=str, required=True, help="Name of the website to remove")
    
    # Update settings command
    settings_parser = subparsers.add_parser("settings", help="Update alert settings")
    settings_parser.add_argument("--speech", type=str, choices=["on", "off"], 
                               help="Enable/disable speech alerts")
    settings_parser.add_argument("--min-change", type=float, 
                               help="Minimum percentage change to trigger alert")
    settings_parser.add_argument("--negative-threshold", type=float, 
                               help="Threshold for negative sentiment alerts (0-1)")
    settings_parser.add_argument("--positive-threshold", type=float, 
                               help="Threshold for positive sentiment alerts (0-1)")
    
    # List websites command
    list_parser = subparsers.add_parser("list", help="List monitored websites")
    
    # View recent changes command
    recent_parser = subparsers.add_parser("recent", help="View recent changes")
    recent_parser.add_argument("--limit", type=int, default=10, help="Number of changes to show")
    
    # View stats command
    stats_parser = subparsers.add_parser("stats", help="View sentiment statistics")
    stats_parser.add_argument("--days", type=int, default=7, help="Number of days to include in stats")
    
    return parser.parse_args()

def main():
    """Main function for CLI."""
    args = parse_args()
    scraper = WebScraper() # Initializes WebScraper, loads config
    
    if args.command == "start":
        print("Starting web scraper service. Press Ctrl+C to stop.")
        # Call the new service method
        scraper.start_service() 
        
    elif args.command == "check":
        if args.all:
            print("Checking all websites now (single run)...")
            # Call run_checks for a one-time check of all sites
            scraper.run_checks() 
        elif args.name:
            # Find the specific website config
            website_to_check = None
            for site_config in scraper.config.get("websites", []):
                if site_config["name"] == args.name:
                    website_to_check = site_config
                    break
            
            if website_to_check:
                print(f"Checking website: {args.name} (single run)...")
                scraper.check_website(website_to_check) # check_website expects a config dict
            else:
                print(f"Website not found: {args.name}")
                logger.warning(f"CLI: Website '{args.name}' not found in configuration for 'check' command.")
        else:
            # This case should ideally be handled by argparse if --all or --name is mandatory for check
            print("For 'check' command, please specify --all or --name <website_name>.")
            
    elif args.command == "add":
        print(f"Adding website: {args.name} ({args.url})")
        scraper.add_website(
            name=args.name, 
            url=args.url, 
            selector=args.selector, 
            interval=args.interval, 
            importance=args.importance
            # translate_changes_to_en is not an arg here, will use default or you can add it
        )
        
    elif args.command == "remove":
        print(f"Removing website: {args.name}")
        scraper.remove_website(name=args.name)
        
    elif args.command == "settings":
        speech_enabled = None
        if args.speech is not None: # Check if the argument was provided
            speech_enabled = args.speech.lower() == "on"
            
        scraper.update_alert_settings(
            speech_enabled=speech_enabled,
            min_change_percent=args.min_change if args.min_change is not None else None,
            negative_threshold=args.negative_threshold if args.negative_threshold is not None else None,
            positive_threshold=args.positive_threshold if args.positive_threshold is not None else None
        )
        # Message is printed by update_alert_settings
        
    elif args.command == "list":
        websites = scraper.config.get("websites", []) # Ensure 'websites' key exists
        if not websites:
            print("No websites configured for monitoring.")
        else:
            print(f"{'Name':<20} {'URL':<40} {'Interval (min)':<15} {'Importance':<10} {'Translate':<10}")
            print("-" * 105)
            for site in websites:
                print(f"{site.get('name', 'N/A'):<20} {site.get('url', 'N/A'):<40} {site.get('check_interval_minutes', 'N/A'):<15} {site.get('importance', 'N/A'):<10} {str(site.get('translate_changes_to_en', 'N/A')):<10}")
                
    elif args.command == "recent":
        # This command will likely fail or do nothing useful as get_recent_changes
        # was database-dependent and is not implemented for file-based storage.
        print("Command 'recent' is not fully functional with the current file-based storage.")
        logger.warning("CLI: 'recent' command called, but get_recent_changes is not implemented for file-based system.")
        # changes = scraper.get_recent_changes(args.limit) # This line would error
        # ... (rest of the original 'recent' block would need rework) ...
                
    elif args.command == "stats":
        # Similar to 'recent', this was database-dependent.
        print("Command 'stats' is not fully functional with the current file-based storage.")
        logger.warning("CLI: 'stats' command called, but get_sentiment_stats is not implemented for file-based system.")
        # stats = scraper.get_sentiment_stats(args.days) # This line would error
        # ... (rest of the original 'stats' block would need rework) ...
    else:
        # This should be caught by argparse if 'command' is required.
        # If subparsers are optional, then this message is fine.
        print("Please specify a command. Use --help for options.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting web scraper CLI.")
    except Exception as e:
        logger.error(f"CLI Error: {str(e)}", exc_info=True) # Log with traceback
        print(f"An unexpected error occurred in CLI: {str(e)}")
