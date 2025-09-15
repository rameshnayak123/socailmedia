# Instagram Clone - Flask Backend

A complete Instagram clone backend built with Flask, featuring all the essential social media functionalities including user authentication, posts, stories, direct messaging, real-time features, and advanced machine learning algorithms for content recommendations.

## 🚀 Features

### Core Features
- **User Authentication** - Registration, login, JWT tokens
- **User Profiles** - Customizable profiles with bio, profile pictures, follower counts
- **Posts** - Photo/video sharing with captions, locations, and hashtags
- **Stories** - 24-hour temporary content sharing
- **Social Interactions** - Like, comment, share, follow/unfollow
- **Direct Messaging** - Real-time private messaging between users
- **Explore** - Discover new content and users
- **Search** - Find users and content
- **Notifications** - Real-time notifications for interactions

### Advanced Features
- **Machine Learning Recommendations** - AI-powered content and user suggestions
- **Content Moderation** - Automatic content filtering and spam detection
- **Image Analysis** - Hashtag suggestions and image quality analysis
- **Engagement Prediction** - ML-based post performance prediction
- **Real-time Features** - WebSocket support for live messaging and notifications
- **User Clustering** - Group users with similar interests for better recommendations

## 🛠 Tech Stack

- **Framework**: Flask 2.3.3
- **Database**: PostgreSQL (SQLite for development)
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Real-time**: Socket.IO
- **Caching**: Redis
- **Machine Learning**: scikit-learn, pandas, numpy
- **Image Processing**: OpenCV, Pillow
- **Email**: Flask-Mail
- **Deployment**: Gunicorn, Docker-ready

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for development)
- Redis (optional, for caching)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd instagram-clone-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Database Setup
```bash
# For PostgreSQL
createdb instagram_clone

# Initialize database
python run.py
```

### 6. Run the Application
```bash
python run.py
```

The server will start at `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key
DEBUG=True
HOST=0.0.0.0
PORT=5000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/instagram_clone

# JWT
JWT_SECRET_KEY=your-jwt-secret-key

# Email (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# AWS S3 (optional, for file storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-bucket-name

# Machine Learning
ML_MODEL_PATH=ml_models
ENABLE_ML_RECOMMENDATIONS=True
```

### Database Configuration

The application supports multiple database configurations:

- **Development**: SQLite (default)
- **Production**: PostgreSQL
- **Testing**: In-memory SQLite

## 📊 API Documentation

### Authentication Endpoints

```
POST /api/auth/register    - Register new user
POST /api/auth/login       - User login
GET  /api/auth/verify-token - Verify JWT token
POST /api/auth/logout      - User logout
```

### User Endpoints

```
GET  /api/users/profile           - Get current user profile
PUT  /api/users/profile           - Update profile
GET  /api/users/<username>        - Get user profile by username
POST /api/users/<id>/follow       - Follow user
POST /api/users/<id>/unfollow     - Unfollow user
GET  /api/users/search            - Search users
GET  /api/users/suggestions       - Get user suggestions
```

### Post Endpoints

```
GET  /api/posts/              - Get feed posts
POST /api/posts/              - Create new post
GET  /api/posts/<id>          - Get specific post
POST /api/posts/<id>/like     - Like/unlike post
POST /api/posts/<id>/comments - Add comment
GET  /api/posts/<id>/comments - Get post comments
DELETE /api/posts/<id>        - Delete post
GET  /api/posts/explore       - Explore posts
```

### Messaging Endpoints

```
GET  /api/messages/conversations     - Get all conversations
GET  /api/messages/conversation/<id> - Get conversation with user
POST /api/messages/send              - Send message
PUT  /api/messages/<id>/read         - Mark message as read
GET  /api/messages/unread-count      - Get unread message count
```

### Recommendation Endpoints

```
GET  /api/recommendations/posts        - Get recommended posts
GET  /api/recommendations/users        - Get recommended users
GET  /api/recommendations/trending     - Get trending posts
POST /api/recommendations/hashtags     - Get hashtag suggestions
POST /api/recommendations/engagement-prediction - Predict post engagement
```

## 🤖 Machine Learning Features

### Recommendation System
- **Collaborative Filtering**: Recommendations based on similar users
- **Content-Based Filtering**: Recommendations based on content similarity
- **Hybrid Approach**: Combines both methods for better accuracy

### Content Moderation
- **Text Analysis**: Detects inappropriate language and spam
- **Sentiment Analysis**: Analyzes post sentiment
- **Image Moderation**: Basic image content filtering

### Engagement Prediction
- **Post Performance**: Predicts likes, comments, and shares
- **Optimal Timing**: Suggests best times to post
- **Content Analysis**: Analyzes caption and hashtag effectiveness

## 🔄 Real-time Features

The application uses Socket.IO for real-time functionality:

### Events
- `connect/disconnect` - User connection status
- `join_room/leave_room` - Chat room management
- `send_message` - Real-time messaging
- `new_notification` - Live notifications

### Usage Example
```javascript
// Connect to Socket.IO
const socket = io('http://localhost:5000');

// Join a chat room
socket.emit('join_room', { room: 'user_123_456' });

// Send a message
socket.emit('send_message', {
    room: 'user_123_456',
    message: 'Hello!',
    username: 'johndoe'
});

// Listen for new messages
socket.on('new_message', (data) => {
    console.log('New message:', data);
});
```

## 📈 Performance & Scalability

### Caching
- Redis for session storage and frequent queries
- Database query optimization with proper indexing
- Pagination for large datasets

### Database Optimization
- Indexed columns for fast lookups
- Relationship optimization
- Query optimization for complex joins

### Rate Limiting
- API rate limiting to prevent abuse
- User-specific limits for posts and messages

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 🚢 Deployment

### Using Docker

```bash
# Build image
docker build -t instagram-clone-backend .

# Run container
docker run -p 5000:5000 instagram-clone-backend
```

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL database
- [ ] Configure Redis for caching
- [ ] Set up SSL/HTTPS
- [ ] Configure file storage (AWS S3)
- [ ] Set up monitoring and logging
- [ ] Configure email service
- [ ] Set strong secret keys
- [ ] Set up database backups

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run tests and ensure they pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

## 🔮 Future Enhancements

- [ ] Video upload and streaming
- [ ] Advanced image filters
- [ ] Push notifications
- [ ] Admin dashboard
- [ ] Analytics and insights
- [ ] Multi-language support
- [ ] Advanced search with filters
- [ ] Story highlights
- [ ] Live streaming
- [ ] E-commerce integration

---

Built with ❤️ using Flask and modern web technologies.
