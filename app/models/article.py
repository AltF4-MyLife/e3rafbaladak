from datetime import datetime
from app import db
from app.utils import generate_unique_slug

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(300), nullable=True)
    featured_image = db.Column(db.String(100), nullable=True)  # Path to image
    category = db.Column(db.String(50), nullable=False)  # constitution, geography, economy, history, diplomacy
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    view_count = db.Column(db.Integer, default=0)
    
    # Relationships
    author = db.relationship('User', backref='articles')
    comments = db.relationship('ArticleComment', backref='article', lazy='dynamic', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='related_article', lazy='dynamic')
    
    def __init__(self, title, content, category, author_id, summary=None, 
                 featured_image=None, is_published=False):
        self.title = title
        self.content = content
        self.category = category
        self.author_id = author_id
        self.summary = summary
        self.featured_image = featured_image
        self.is_published = is_published
        if is_published:
            self.published_at = datetime.utcnow()
        # Generate slug from title
        self.slug = generate_unique_slug(title, Article)
    
    def publish(self):
        self.is_published = True
        self.published_at = datetime.utcnow()
        db.session.commit()
    
    def unpublish(self):
        self.is_published = False
        db.session.commit()
    
    def increment_view_count(self):
        self.view_count += 1
        db.session.commit()
    
    def get_comment_count(self):
        return self.comments.count()
    
    def get_related_articles(self, limit=3):
        """Get related articles in the same category"""
        return Article.query.filter(
            Article.category == self.category,
            Article.id != self.id,
            Article.is_published == True
        ).order_by(Article.published_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Article {self.title}({self.category})>'

class ArticleComment(db.Model):
    __tablename__ = 'article_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    
    def __init__(self, article_id, user_id, content, is_approved=False):
        self.article_id = article_id
        self.user_id = user_id
        self.content = content
        self.is_approved = is_approved
    
    def approve(self):
        self.is_approved = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Comment {self.id} on Article {self.article_id}'

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # constitution, geography, economy, history, diplomacy
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=True)  # Optional related article
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)
    time_limit = db.Column(db.Integer, nullable=True)  # Time limit in minutes, if any
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    author = db.relationship('User', backref='quizzes')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic')
    
    def __init__(self, title, category, author_id, description=None, article_id=None, 
                 is_published=False, time_limit=None):
        self.title = title
        self.category = category
        self.author_id = author_id
        self.description = description
        self.article_id = article_id
        self.is_published = is_published
        self.time_limit = time_limit
    
    def publish(self):
        self.is_published = True
        db.session.commit()
    
    def unpublish(self):
        self.is_published = False
        db.session.commit()
    
    def get_question_count(self):
        return self.questions.count()
    
    def get_attempt_count(self):
        return self.attempts.count()
    
    def __repr__(self):
        return f'<Quiz {self.title}({self.category})>'

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false, short_answer
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer, default=0)  # Order in the quiz
    
    # Relationships
    choices = db.relationship('QuizChoice', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, quiz_id, question_text, question_type='multiple_choice', points=1, order=0):
        self.quiz_id = quiz_id
        self.question_text = question_text
        self.question_type = question_type
        self.points = points
        self.order = order
    
    def get_correct_choice(self):
        if self.question_type == 'multiple_choice':
            return self.choices.filter_by(is_correct=True).first()
        return None
    
    def __repr__(self):
        return f'<Question {self.id} for Quiz {self.quiz_id}>'

class QuizChoice(db.Model):
    __tablename__ = 'quiz_choices'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    choice_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)  # Order of choices
    
    def __init__(self, question_id, choice_text, is_correct=False, order=0):
        self.question_id = question_id
        self.choice_text = choice_text
        self.is_correct = is_correct
        self.order = order
    
    def __repr__(self):
        return f'<Choice {self.id} for Question {self.question_id}>'

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='quiz_attempts')
    answers = db.relationship('QuizAnswer', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, quiz_id, user_id):
        self.quiz_id = quiz_id
        self.user_id = user_id
        # Calculate max possible score
        from app.models.article import QuizQuestion
        questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
        self.max_score = sum(q.points for q in questions)
    
    def complete(self, score):
        self.score = score
        self.completed_at = datetime.utcnow()
        self.is_completed = True
        db.session.commit()
    
    def get_percentage_score(self):
        if self.max_score > 0:
            return (self.score / self.max_score) * 100
        return 0
    
    def __repr__(self):
        return f'<Attempt {self.id} by User {self.user_id} on Quiz {self.quiz_id}>'

class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    selected_choice_id = db.Column(db.Integer, db.ForeignKey('quiz_choices.id'), nullable=True)  # For multiple choice
    text_answer = db.Column(db.Text, nullable=True)  # For short answer
    is_correct = db.Column(db.Boolean, default=False)
    
    # Relationships
    question = db.relationship('QuizQuestion')
    selected_choice = db.relationship('QuizChoice', backref='answers')
    
    def __init__(self, attempt_id, question_id, selected_choice_id=None, text_answer=None):
        self.attempt_id = attempt_id
        self.question_id = question_id
        self.selected_choice_id = selected_choice_id
        self.text_answer = text_answer
        
        # Determine if the answer is correct
        if selected_choice_id:
            from app.models.article import QuizChoice
            choice = QuizChoice.query.get(selected_choice_id)
            if choice:
                self.is_correct = choice.is_correct
    
    def __repr__(self):
        return f'<Answer {self.id} for Question {self.question_id} in Attempt {self.attempt_id}>'