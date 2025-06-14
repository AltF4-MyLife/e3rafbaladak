from datetime import datetime
from app import db

class Media(db.Model):
    __tablename__ = 'media'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    media_type = db.Column(db.String(20), nullable=False)  # video, image, document, article
    file_path = db.Column(db.String(255), nullable=True)  # Path to the file if uploaded
    external_url = db.Column(db.String(255), nullable=True)  # URL if embedded from external source
    thumbnail_path = db.Column(db.String(255), nullable=True)  # Path to thumbnail image
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Creator
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)  # Associated school if any
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=True)  # Associated activity if any
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)  # Requires admin approval
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who approved
    approved_at = db.Column(db.DateTime, nullable=True)
    view_count = db.Column(db.Integer, default=0)
    featured = db.Column(db.Boolean, default=False)  # Featured on homepage
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[user_id], backref='uploaded_media')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_media')
    school = db.relationship('School', backref='media')
    ratings = db.relationship('MediaRating', backref='media', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('MediaComment', backref='media', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, media_type, user_id, description=None, file_path=None, 
                 external_url=None, thumbnail_path=None, school_id=None, tags=None):
        self.title = title
        self.media_type = media_type
        self.user_id = user_id
        self.description = description
        self.file_path = file_path
        self.external_url = external_url
        self.thumbnail_path = thumbnail_path
        self.school_id = school_id
        self.tags = tags
    
    def approve(self, admin_id):
        self.is_approved = True
        self.approved_by = admin_id
        self.approved_at = datetime.utcnow()
        db.session.commit()
    
    def reject(self):
        self.is_approved = False
        self.approved_by = None
        self.approved_at = None
        db.session.commit()
    
    def toggle_featured(self):
        self.featured = not self.featured
        db.session.commit()
    
    def increment_view_count(self):
        self.view_count += 1
        db.session.commit()
    
    def get_average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)
    
    def get_comment_count(self):
        return self.comments.count()
    
    def get_tag_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]
    
    def __repr__(self):
        return f'<Media {self.id}: {self.title} ({self.media_type})>'

class MediaRating(db.Model):
    __tablename__ = 'media_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='media_ratings')
    
    # Ensure one rating per user per media item
    __table_args__ = (db.UniqueConstraint('media_id', 'user_id', name='_media_user_rating_uc'),)
    
    def __init__(self, media_id, user_id, rating):
        self.media_id = media_id
        self.user_id = user_id
        self.rating = min(max(rating, 1), 5)  # Ensure rating is between 1-5
    
    def __repr__(self):
        return f'<Rating {self.id}: {self.rating} stars for Media {self.media_id} by User {self.user_id}>'

class MediaComment(db.Model):
    __tablename__ = 'media_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)  # Requires moderation
    
    # Relationships
    user = db.relationship('User', backref='media_comments')
    
    def __init__(self, media_id, user_id, content, is_approved=False):
        self.media_id = media_id
        self.user_id = user_id
        self.content = content
        self.is_approved = is_approved
    
    def approve(self):
        self.is_approved = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Comment {self.id} on Media {self.media_id} by User {self.user_id}>'

class MediaCollection(db.Model):
    __tablename__ = 'media_collections'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)  # Optional school association
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)  # Whether visible to all users
    
    # Relationships
    creator = db.relationship('User', backref='created_collections')
    school = db.relationship('School', backref='media_collections')
    items = db.relationship('MediaCollectionItem', backref='collection', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, created_by, description=None, school_id=None, is_public=True):
        self.title = title
        self.created_by = created_by
        self.description = description
        self.school_id = school_id
        self.is_public = is_public
    
    def add_media(self, media_id, order=None):
        # If order not specified, add to end
        if order is None:
            max_order = db.session.query(db.func.max(MediaCollectionItem.order)).\
                filter(MediaCollectionItem.collection_id == self.id).scalar() or 0
            order = max_order + 1
        
        item = MediaCollectionItem(collection_id=self.id, media_id=media_id, order=order)
        db.session.add(item)
        db.session.commit()
        return item
    
    def remove_media(self, media_id):
        item = MediaCollectionItem.query.filter_by(
            collection_id=self.id, media_id=media_id).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        return False
    
    def get_media_count(self):
        return self.items.count()
    
    def __repr__(self):
        return f'<MediaCollection {self.id}: {self.title}'

class MediaCollectionItem(db.Model):
    __tablename__ = 'media_collection_items'
    
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('media_collections.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    order = db.Column(db.Integer, default=0)  # Order in the collection
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    media = db.relationship('Media')
    
    # Ensure media appears only once in a collection
    __table_args__ = (db.UniqueConstraint('collection_id', 'media_id', name='_collection_media_uc'),)
    
    def __init__(self, collection_id, media_id, order=0):
        self.collection_id = collection_id
        self.media_id = media_id
        self.order = order
    
    def __repr__(self):
        return f'<CollectionItem {self.id}: Media {self.media_id} in Collection {self.collection_id}>'