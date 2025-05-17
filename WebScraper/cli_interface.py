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
    scraper = WebScraper()
    
    if args.command == "start":
        print("Starting web scraper service. Press Ctrl+C to stop.")
        scraper.start()
        
    elif args.command == "check":
        if args.all:
            print("Checking all websites...")
            scraper.run_scheduled_checks()
        elif args.name:
            website = next((w for w in scraper.config["websites"] if w["name"] == args.name), None)
            if website:
                print(f"Checking website: {args.name}")
                scraper.check_website(website)
            else:
                print(f"Website not found: {args.name}")
        else:
            print("Please specify --all or --name")
            
    elif args.command == "add":
        print(f"Adding website: {args.name} ({args.url})")
        scraper.add_website(
            args.name, args.url, args.selector, 
            args.interval, args.importance
        )
        
    elif args.command == "remove":
        print(f"Removing website: {args.name}")
        scraper.remove_website(args.name)
        
    elif args.command == "settings":
        speech_enabled = None
        if args.speech == "on":
            speech_enabled = True
        elif args.speech == "off":
            speech_enabled = False
            
        scraper.update_alert_settings(
            speech_enabled=speech_enabled,
            min_change_percent=args.min_change,
            negative_threshold=args.negative_threshold,
            positive_threshold=args.positive_threshold
        )
        print("Settings updated")
        
    elif args.command == "list":
        websites = scraper.config["websites"]
        if not websites:
            print("No websites configured for monitoring")
        else:
            print(f"{'Name':<20} {'URL':<40} {'Interval':<10} {'Importance':<10}")
            print("-" * 80)
            for site in websites:
                print(f"{site['name']:<20} {site['url']:<40} {site['check_interval_minutes']:<10} {site['importance']:<10}")
                
    elif args.command == "recent":
        changes = scraper.get_recent_changes(args.limit)
        if not changes:
            print("No changes recorded yet")
        else:
            print(f"{'Website':<20} {'Time':<20} {'Change %':<10} {'Sentiment':<20} {'Categories':<20}")
            print("-" * 90)
            for change in changes:
                categories = json.loads(change["categorization"])
                categories_str = ", ".join(categories)
                if len(categories_str) > 20:
                    categories_str = categories_str[:17] + "..."
                    
                sentiment = f"{change['sentiment_label']} ({change['sentiment_score']:.2f})"
                time_short = change["detection_time"].split("T")[0]
                
                print(f"{change['website_name']:<20} {time_short:<20} {change['change_percentage']:<10.1f} {sentiment:<20} {categories_str:<20}")
                
    elif args.command == "stats":
        stats = scraper.get_sentiment_stats(args.days)
        if not stats:
            print(f"No statistics available for the last {args.days} days")
        else:
            print(f"Sentiment statistics for the past {args.days} days:")
            print(f"{'Website':<20} {'Avg Score':<10} {'Changes':<10} {'Positive':<10} {'Negative':<10} {'Neutral':<10}")
            print("-" * 80)
            for stat in stats:
                print(f"{stat['website_name']:<20} {stat['avg_score']:<10.2f} {stat['change_count']:<10} "
                      f"{stat['positive_count']:<10} {stat['negative_count']:<10} {stat['neutral_count']:<10}")
    else:
        print("Please specify a command. Use --help for options.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting web scraper CLI")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"An error occurred: {str(e)}")
