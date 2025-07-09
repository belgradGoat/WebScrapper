import json
import sys
import os
import requests
from datetime import datetime, timezone, timedelta
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class RedditScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def search_posts(self, query, limit=100):
        """Search for Reddit posts using multiple methods"""
        try:
            print(f"🔍 Searching Reddit for: '{query}' (limit: {limit})", file=sys.stderr)
            print(f"📅 Filtering posts from last 24 hours, sorted by popularity then recency", file=sys.stderr)
            
            # Try multiple Reddit endpoints for better coverage
            all_posts = []
            
            # Method 1: Reddit JSON API search (most reliable)
            posts_from_search = self.search_via_json_api(query, limit)
            if posts_from_search:
                all_posts.extend(posts_from_search)
                print(f"✅ Found {len(posts_from_search)} posts via JSON API search", file=sys.stderr)
            
            # Method 2: Popular subreddits for the topic
            if len(all_posts) < limit:
                posts_from_subreddits = self.search_relevant_subreddits(query, limit - len(all_posts))
                if posts_from_subreddits:
                    all_posts.extend(posts_from_subreddits)
                    print(f"✅ Found {len(posts_from_subreddits)} additional posts from relevant subreddits", file=sys.stderr)
            
            # Remove duplicates and limit results
            unique_posts = self.remove_duplicates(all_posts)
            
            # Final sort by popularity then recency
            unique_posts.sort(key=lambda x: (-x['engagement']['score'], -datetime.fromisoformat(x['createdAt'].replace('Z', '+00:00')).timestamp()))
            
            limited_posts = unique_posts[:limit]
            
            print(f"✅ Total unique posts found: {len(limited_posts)}", file=sys.stderr)
            if limited_posts:
                print(f"📊 Score range: {limited_posts[0]['engagement']['score']} (highest) to {limited_posts[-1]['engagement']['score']} (lowest)", file=sys.stderr)
            
            return limited_posts
            
        except Exception as e:
            print(f"❌ Error searching Reddit: {str(e)}", file=sys.stderr)
            return self.generate_sample_posts(query, limit)
    
    def search_via_json_api(self, query, limit):
        """Search Reddit using the JSON API"""
        try:
            # Reddit's search endpoint
            url = "https://www.reddit.com/search.json"
            params = {
                'q': query,
                'sort': 'hot',  # Changed from 'new' to 'hot' for popularity
                'limit': min(limit * 2, 100),  # Get more posts to filter by time
                't': 'day',  # Changed from 'week' to 'day' for 24-hour posts
                'type': 'link'
            }
            
            print(f"🔄 Fetching from Reddit JSON API: {url}", file=sys.stderr)
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                posts = []
                current_time = datetime.now(timezone.utc)
                
                if 'data' in data and 'children' in data['data']:
                    for item in data['data']['children']:
                        post_data = item.get('data', {})
                        
                        # Check if post is within 24 hours
                        created_utc = post_data.get('created_utc', 0)
                        post_time = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                        time_diff = current_time - post_time
                        
                        # Only include posts from last 24 hours
                        if time_diff.total_seconds() <= 24 * 60 * 60:  # 24 hours in seconds
                            formatted_post = self.format_reddit_post(post_data)
                            if formatted_post:
                                posts.append(formatted_post)
                
                # Sort by popularity (score) first, then by recency
                posts.sort(key=lambda x: (-x['engagement']['score'], -datetime.fromisoformat(x['createdAt'].replace('Z', '+00:00')).timestamp()))
                
                # Limit to requested amount
                return posts[:limit]
            else:
                print(f"⚠️  Reddit JSON API returned status {response.status_code}", file=sys.stderr)
                return []
                
        except Exception as e:
            print(f"❌ JSON API search failed: {str(e)}", file=sys.stderr)
            return []
    
    def search_relevant_subreddits(self, query, limit):
        """Search specific subreddits that are likely to have relevant content"""
        # Map keywords to relevant subreddits
        subreddit_mapping = {
            'news': ['news', 'worldnews', 'politics', 'NeutralNews'],
            'technology': ['technology', 'tech', 'programming', 'gadgets'],
            'politics': ['politics', 'PoliticalDiscussion', 'worldnews'],
            'science': ['science', 'EverythingScience', 'technology'],
            'business': ['business', 'Economics', 'investing', 'stocks'],
            'world': ['worldnews', 'geopolitics', 'news'],
            'crypto': ['CryptoCurrency', 'Bitcoin', 'ethereum'],
            'ai': ['artificial', 'MachineLearning', 'technology'],
            'climate': ['climate', 'environment', 'science'],
            'health': ['health', 'medicine', 'science']
        }
        
        # Determine relevant subreddits based on query
        query_lower = query.lower()
        relevant_subreddits = ['news', 'worldnews']  # Default subreddits
        
        for keyword, subreddits in subreddit_mapping.items():
            if keyword in query_lower:
                relevant_subreddits.extend(subreddits)
                break
        
        # Remove duplicates while preserving order
        relevant_subreddits = list(dict.fromkeys(relevant_subreddits))
        
        print(f"🎯 Searching relevant subreddits: {relevant_subreddits[:5]}", file=sys.stderr)
        
        all_posts = []
        posts_per_subreddit = max(1, limit // len(relevant_subreddits))
        
        for subreddit in relevant_subreddits:
            if len(all_posts) >= limit:
                break
                
            try:
                posts = self.get_subreddit_posts(subreddit, query, posts_per_subreddit)
                if posts:
                    all_posts.extend(posts)
                    print(f"  📥 r/{subreddit}: {len(posts)} posts", file=sys.stderr)
                    
            except Exception as e:
                print(f"  ❌ r/{subreddit}: {str(e)}", file=sys.stderr)
                continue
        
        return all_posts
    
    def get_subreddit_posts(self, subreddit, query, limit):
        """Get posts from a specific subreddit"""
        try:
            # Try 'hot' first for popular posts, then 'new' as fallback
            for sort_type in ['hot', 'new']:
                url = f"https://www.reddit.com/r/{subreddit}/{sort_type}.json"
                params = {
                    'limit': min(limit * 4, 50),  # Get more posts to filter
                    't': 'day'  # Posts from last day
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = []
                    current_time = datetime.now(timezone.utc)
                    
                    if 'data' in data and 'children' in data['data']:
                        for item in data['data']['children']:
                            post_data = item.get('data', {})
                            
                            # Check if post is within 24 hours
                            created_utc = post_data.get('created_utc', 0)
                            post_time = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                            time_diff = current_time - post_time
                            
                            # Only include posts from last 24 hours
                            if time_diff.total_seconds() > 24 * 60 * 60:
                                continue
                            
                            # Filter posts that contain the query term
                            title = post_data.get('title', '').lower()
                            selftext = post_data.get('selftext', '').lower()
                            
                            if (query.lower() in title or 
                                query.lower() in selftext or
                                any(word in title for word in query.lower().split())):
                                
                                formatted_post = self.format_reddit_post(post_data)
                                if formatted_post:
                                    posts.append(formatted_post)
                                    
                            if len(posts) >= limit:
                                break
                    
                    if posts:
                        # Sort by popularity (score) first, then by recency
                        posts.sort(key=lambda x: (-x['engagement']['score'], -datetime.fromisoformat(x['createdAt'].replace('Z', '+00:00')).timestamp()))
                        return posts[:limit]
                else:
                    print(f"    ⚠️  r/{subreddit} {sort_type} returned status {response.status_code}", file=sys.stderr)
            
            return []
            
        except Exception as e:
            print(f"    ❌ Error fetching r/{subreddit}: {str(e)}", file=sys.stderr)
            return []
    
    def format_reddit_post(self, post_data):
        """Format a Reddit post for consistent output"""
        try:
            # Extract basic info
            post_id = post_data.get('id', '')
            title = post_data.get('title', '')
            subreddit = post_data.get('subreddit', '')
            author = post_data.get('author', '[deleted]')
            
            # Skip deleted or removed posts
            if not title or title == '[deleted]' or title == '[removed]':
                return None
            
            # Extract text content
            selftext = post_data.get('selftext', '')
            if not selftext and post_data.get('is_self', False):
                selftext = 'Self post - click to view on Reddit'
            elif not selftext:
                selftext = 'Link post - click to view on Reddit'
            
            # Extract engagement metrics
            score = post_data.get('score', 0)
            num_comments = post_data.get('num_comments', 0)
            upvote_ratio = post_data.get('upvote_ratio', 0.5)
            
            # Calculate upvote percentage
            upvote_percentage = int(upvote_ratio * 100) if upvote_ratio else 50
            
            # Extract timestamp
            created_utc = post_data.get('created_utc', time.time())
            created_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            
            # Extract URL
            permalink = post_data.get('permalink', '')
            reddit_url = f"https://www.reddit.com{permalink}" if permalink else f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
            
            # Extract flair
            flair = post_data.get('link_flair_text', '')
            
            # Check if post is recent (within 2 hours)
            is_recent = (datetime.now(timezone.utc) - created_date) < timedelta(hours=2)
            
            formatted_post = {
                "id": post_id,
                "title": title,
                "text": selftext,
                "subreddit": subreddit,
                "author": {
                    "username": author,
                    "displayName": author
                },
                "createdAt": created_date.isoformat(),
                "formattedTime": created_date.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "url": reddit_url,
                "engagement": {
                    "score": score,
                    "comments": num_comments,
                    "upvotes": upvote_percentage
                },
                "flair": flair,
                "platform": "Reddit",
                "isRecent": is_recent
            }
            
            return formatted_post
            
        except Exception as e:
            print(f"❌ Error formatting Reddit post: {str(e)}", file=sys.stderr)
            return None
    
    def remove_duplicates(self, posts):
        """Remove duplicate posts based on ID and title"""
        seen_ids = set()
        seen_titles = set()
        unique_posts = []
        
        for post in posts:
            post_id = post.get('id', '')
            title = post.get('title', '').lower().strip()
            
            # Skip if we've seen this ID or very similar title
            if post_id in seen_ids or title in seen_titles:
                continue
            
            seen_ids.add(post_id)
            seen_titles.add(title)
            unique_posts.append(post)
        
        return unique_posts
    
    def generate_sample_posts(self, query, limit):
        """Generate sample Reddit posts when API fails"""
        print(f"🎭 Generating sample Reddit posts for query: '{query}'", file=sys.stderr)
        
        sample_posts = []
        current_time = datetime.now(timezone.utc)
        
        # Sample subreddits
        subreddits = [
            'news', 'worldnews', 'technology', 'politics', 'science',
            'todayilearned', 'AskReddit', 'explainlikeimfive', 'business'
        ]
        
        # Sample post templates
        post_templates = [
            f"Breaking: Latest developments in {query} situation",
            f"Discussion: What are your thoughts on {query}?",
            f"Analysis: How {query} is affecting the current landscape",
            f"Update: New information about {query} emerges",
            f"Question: Can someone explain the {query} situation?",
            f"News: Major {query} announcement today",
            f"Opinion: Why {query} matters more than you think",
            f"Research: Recent study on {query} reveals interesting findings",
            f"Alert: Important {query} update everyone should know",
            f"Deep dive: Understanding the {query} phenomenon"
        ]
        
        usernames = [
            'NewsWatcher', 'InfoSeeker', 'AnalystUser', 'UpdateBot',
            'DiscussionLover', 'FactChecker', 'TrendSpotter', 'NewsHound',
            'RedditUser2024', 'CurrentEvents'
        ]
        
        for i in range(min(limit, len(post_templates))):
            # Generate posts within last 24 hours, with varying popularity
            hours_ago = (i * 2) % 24  # Distribute across 24 hours
            post_time = current_time - timedelta(hours=hours_ago)
            
            # Create realistic popularity distribution (higher scores for more recent posts)
            base_score = 500 - (i * 30)  # Start high and decrease
            variance = (i * 25) % 200  # Add some randomness
            score = max(10, base_score + variance)  # Ensure minimum score
            
            comments = max(5, (score // 10) + (i * 3) % 50)  # Comments roughly correlate with score
            upvote_ratio = max(0.6, 0.95 - (i * 0.02))  # Higher ratio for popular posts
            
            sample_posts.append({
                "id": f"reddit_sample_{i}",
                "title": post_templates[i],
                "text": f"This is a sample Reddit post about {query}. In a real implementation, this would contain actual post content from Reddit's API. This post simulates popular content from the last 24 hours.",
                "subreddit": subreddits[i % len(subreddits)],
                "author": {
                    "username": usernames[i % len(usernames)],
                    "displayName": usernames[i % len(usernames)]
                },
                "createdAt": post_time.isoformat(),
                "formattedTime": post_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "url": f"https://www.reddit.com/r/{subreddits[i % len(subreddits)]}/comments/sample_{i}/",
                "engagement": {
                    "score": score,
                    "comments": comments,
                    "upvotes": int(upvote_ratio * 100)
                },
                "flair": "Popular" if score > 400 else ("Trending" if score > 200 else ""),
                "platform": "Reddit",
                "isRecent": hours_ago < 2  # Mark as recent if less than 2 hours old
            })
        
        # Sort sample posts by score (popularity) then by recency
        sample_posts.sort(key=lambda x: (-x['engagement']['score'], -datetime.fromisoformat(x['createdAt']).timestamp()))
        
        return sample_posts

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No search query provided"}))
        return
    
    try:
        query = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        
        print(f"🔍 Searching Reddit for: '{query}' (limit: {limit})", file=sys.stderr)
        
        scraper = RedditScraper()
        posts = scraper.search_posts(query, limit)
        
        # Determine if we're using real or sample data
        is_sample_data = any(post.get('id', '').startswith('reddit_sample_') for post in posts[:3])
        
        result = {
            "success": True,
            "query": query,
            "totalPosts": len(posts),
            "posts": posts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Sample data - Reddit API access limited" if is_sample_data else "Real Reddit data via JSON API"
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}", file=sys.stderr)
        
        # Fallback to sample data
        try:
            query = sys.argv[1] if len(sys.argv) > 1 else "news"
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            
            scraper = RedditScraper()
            posts = scraper.generate_sample_posts(query, limit)
            
            result = {
                "success": True,
                "query": query,
                "totalPosts": len(posts),
                "posts": posts,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": f"Sample data - Error occurred: {str(e)}"
            }
            
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        except Exception as fallback_error:
            error_result = {
                "success": False,
                "error": f"Both main process and fallback failed: {str(e)}, {str(fallback_error)}",
                "query": sys.argv[1] if len(sys.argv) > 1 else "unknown",
                "posts": []
            }
            print(json.dumps(error_result))

if __name__ == "__main__":
    main()