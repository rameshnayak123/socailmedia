
import random
import json
from datetime import datetime, timedelta
from ml_models import *
import string

class TestDataGenerator:
    """Generate realistic test data for the social media platform"""

    def __init__(self):
        self.categories = ['music', 'comedy', 'dance', 'education', 'sports', 'food', 'lifestyle', 'tech', 'art', 'travel']
        self.sample_usernames = [
            'musiclover', 'comedyfan', 'dancer123', 'techguru', 'foodie_life', 
            'sports_fanatic', 'art_creator', 'travel_addict', 'lifestyle_blogger', 'educator'
        ]
        self.sample_content = {
            'music': [
                'Just dropped my new track! What do you think? 🎵',
                'Jamming to this amazing song right now! 🎧',
                'Working on some new beats in the studio 🎹',
                'This melody has been stuck in my head all day! 🎼'
            ],
            'comedy': [
                'When you realize it\'s Monday tomorrow 😭',
                'Me trying to adult like... 🤦‍♂️',
                'That awkward moment when... 😅',
                'Why is adulting so hard? Someone explain! 🤔'
            ],
            'dance': [
                'Nailed this choreography! Check it out! 💃',
                'Dancing my heart out to this amazing song! 🕺',
                'New dance challenge accepted! Who\'s joining? 🔥',
                'Practice makes perfect! Still working on this routine ✨'
            ],
            'education': [
                'Today I learned something incredible about quantum physics! 🤯',
                'Study tip: Use the Pomodoro technique for better focus! 📚',
                'Breaking down complex concepts into simple explanations 🧠',
                'Learning something new every day keeps the mind sharp! 💡'
            ],
            'food': [
                'Homemade pasta from scratch! Recipe in the comments 🍝',
                'This pizza looks too good to eat... almost! 🍕',
                'Trying out a new dessert recipe today! 🍰',
                'Fresh ingredients make all the difference! 🥗'
            ]
        }

        self.hashtag_pools = {
            'music': ['#music', '#song', '#newtrack', '#studio', '#musician', '#beats', '#melody'],
            'comedy': ['#funny', '#comedy', '#humor', '#meme', '#lol', '#hilarious', '#joke'],
            'dance': ['#dance', '#choreography', '#dancing', '#moves', '#dancer', '#performance'],
            'education': ['#learning', '#education', '#knowledge', '#study', '#tips', '#science'],
            'food': ['#food', '#cooking', '#recipe', '#delicious', '#homemade', '#chef']
        }

    def generate_users(self, count=20):
        """Generate sample users"""
        users = []

        for i in range(count):
            user_id = f"user_{i+1:03d}"
            username = f"{random.choice(self.sample_usernames)}_{random.randint(1, 999)}"

            user = {
                'user_id': user_id,
                'username': username,
                'email': f"{username}@example.com",
                'bio': f"Content creator passionate about {random.choice(self.categories)}! 🌟",
                'followers': random.randint(10, 10000),
                'following': random.randint(50, 1000),
                'posts_count': random.randint(5, 100),
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                'preferences': {
                    'content_types': random.choices(self.categories, k=random.randint(2, 4)),
                    'privacy_level': random.choice(['public', 'private'])
                }
            }
            users.append(user)

        return users

    def generate_posts(self, users, count=100):
        """Generate sample posts"""
        posts = []

        for i in range(count):
            user = random.choice(users)
            category = random.choice(user['preferences']['content_types'])

            # Get sample content for the category
            content_options = self.sample_content.get(category, ['Great content! Check this out!'])
            content = random.choice(content_options)

            # Add random elements to make content more varied
            if random.random() > 0.7:  # 30% chance
                content += f" #{category} #{random.choice(['trending', 'viral', 'awesome', 'amazing'])}"

            # Generate hashtags
            available_hashtags = self.hashtag_pools.get(category, [f'#{category}'])
            hashtags = random.choices(available_hashtags, k=random.randint(1, 5))

            post = {
                'post_id': f"post_{i+1:04d}",
                'user_id': user['user_id'],
                'username': user['username'],
                'content': content,
                'category': category,
                'hashtags': hashtags,
                'media_urls': [f"https://example.com/media/post_{i+1}.jpg"] if random.random() > 0.3 else [],
                'likes': random.randint(0, 1000),
                'comments': random.randint(0, 100),
                'shares': random.randint(0, 50),
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                'sentiment_analysis': {
                    'sentiment': random.choice(['positive', 'neutral', 'negative']),
                    'score': random.uniform(0.1, 0.9)
                }
            }
            posts.append(post)

        return posts

    def generate_reels(self, users, count=50):
        """Generate sample reels"""
        reels = []

        for i in range(count):
            user = random.choice(users)
            category = random.choice(user['preferences']['content_types'])

            # Reels typically have shorter, punchier titles
            titles = {
                'music': ['New beat drop! 🎵', 'Vibing to this! 🎧', 'Music magic ✨'],
                'dance': ['Watch this move! 💃', 'Dance battle! 🕺', 'Smooth moves ⚡'],
                'comedy': ['You\'ll laugh! 😂', 'Comedy gold! 🤣', 'So funny! 😆'],
                'food': ['Satisfying! 😋', 'Delicious! 🤤', 'Food art! 🎨']
            }

            title_options = titles.get(category, ['Check this out!'])
            title = random.choice(title_options)

            hashtags = random.choices(
                self.hashtag_pools.get(category, [f'#{category}']), 
                k=random.randint(2, 6)
            )
            hashtags.extend(['#reels', '#viral', '#fyp'])  # Common reel hashtags

            reel = {
                'reel_id': f"reel_{i+1:04d}",
                'user_id': user['user_id'],
                'username': user['username'],
                'title': title,
                'description': f"Amazing {category} content! Don't miss this! 🔥",
                'category': category,
                'video_url': f"https://example.com/videos/reel_{i+1}.mp4",
                'thumbnail_url': f"https://example.com/thumbnails/reel_{i+1}.jpg",
                'duration': random.randint(15, 60),
                'hashtags': hashtags,
                'music_id': f"music_{random.randint(1, 100)}",
                'effects': random.choices(['slow_motion', 'fast_forward', 'reverse', 'filter'], k=random.randint(0, 2)),
                'views': random.randint(100, 50000),
                'likes': random.randint(10, 5000),
                'comments': random.randint(5, 500),
                'shares': random.randint(0, 200),
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'sentiment_analysis': {
                    'sentiment': random.choice(['positive', 'neutral', 'negative']),
                    'score': random.uniform(0.2, 0.9)
                },
                'engagement_rate': random.uniform(0.02, 0.15)
            }
            reels.append(reel)

        return reels

    def generate_interactions(self, users, posts, reels, count=500):
        """Generate sample user interactions"""
        interactions = []
        all_content = [(p, 'post') for p in posts] + [(r, 'reel') for r in reels]

        for i in range(count):
            user = random.choice(users)
            content, content_type = random.choice(all_content)

            interaction = {
                'interaction_id': f"interaction_{i+1:05d}",
                'user_id': user['user_id'],
                'content_id': content[f'{content_type}_id'],
                'content_type': content_type,
                'action_type': random.choice(['view', 'like', 'share', 'comment', 'save']),
                'timestamp': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
                'engagement_score': random.uniform(0.1, 1.0)
            }
            interactions.append(interaction)

        return interactions

    def generate_complete_dataset(self):
        """Generate a complete dataset for testing"""
        print("Generating test data...")

        users = self.generate_users(30)
        print(f"✅ Generated {len(users)} users")

        posts = self.generate_posts(users, 150)
        print(f"✅ Generated {len(posts)} posts")

        reels = self.generate_reels(users, 75)
        print(f"✅ Generated {len(reels)} reels")

        interactions = self.generate_interactions(users, posts, reels, 1000)
        print(f"✅ Generated {len(interactions)} interactions")

        return {
            'users': users,
            'posts': posts,
            'reels': reels,
            'interactions': interactions,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_users': len(users),
                'total_posts': len(posts),
                'total_reels': len(reels),
                'total_interactions': len(interactions),
                'categories': self.categories
            }
        }

    def save_test_data(self, filename='test_data.json'):
        """Save generated test data to file"""
        data = self.generate_complete_dataset()

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Test data saved to {filename}")
        return data

# Example usage and testing
if __name__ == "__main__":
    generator = TestDataGenerator()
    test_data = generator.save_test_data()

    # Print some sample data
    print("\n=== Sample Data ===")
    print(f"Sample User: {json.dumps(test_data['users'][0], indent=2)}")
    print(f"\nSample Post: {json.dumps(test_data['posts'][0], indent=2)}")
    print(f"\nSample Reel: {json.dumps(test_data['reels'][0], indent=2)}")
