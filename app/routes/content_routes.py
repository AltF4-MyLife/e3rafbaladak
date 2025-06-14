from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.models.article import Article, ArticleComment, Quiz, QuizQuestion, QuizChoice, QuizAttempt, QuizAnswer
from app.models.media import Media, MediaComment, MediaRating, MediaCollection
from app.forms import ArticleForm, QuizForm, QuestionForm, MediaUploadForm, CommentForm
from app import db
from app.utils import save_file, allowed_file, save_image_with_thumbnail
from werkzeug.utils import secure_filename
import os
from datetime import datetime

content = Blueprint('content', __name__)

# Article routes
@content.route('/articles')
def article_list():
    """List all published articles"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    category = request.args.get('category')
    
    # Build query
    query = Article.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    articles = query.order_by(Article.published_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('content/article_list.html', 
                           articles=articles, 
                           current_category=category)

@content.route('/articles/<slug>')
def article_view(slug):
    """View a specific article"""
    article = Article.query.filter_by(slug=slug).first_or_404()
    
    # If article is not published, only allow author or admin to view
    if not article.is_published and (not current_user.is_authenticated or 
                                    (current_user.id != article.author_id and not current_user.is_admin())):
        abort(404)
    
    # Increment view count
    article.increment_view_count()
    
    # Get related articles
    related_articles = article.get_related_articles()
    
    # Get comments
    comments = ArticleComment.query.filter_by(
        article_id=article.id, 
        is_approved=True
    ).order_by(ArticleComment.created_at.desc()).all()
    
    # Comment form
    comment_form = CommentForm()
    
    return render_template('content/article_view.html', 
                           article=article, 
                           related_articles=related_articles,
                           comments=comments,
                           comment_form=comment_form)

@content.route('/articles/<slug>/comment', methods=['POST'])
@login_required
def article_comment(slug):
    """Add a comment to an article"""
    article = Article.query.filter_by(slug=slug).first_or_404()
    form = CommentForm()
    
    if form.validate_on_submit():
        # Create comment
        comment = ArticleComment(
            article_id=article.id,
            user_id=current_user.id,
            content=form.content.data,
            is_approved=current_user.is_admin()  # Auto-approve admin comments
        )
        
        db.session.add(comment)
        db.session.commit()
        
        if comment.is_approved:
            flash('Your comment has been added.', 'success')
        else:
            flash('Your comment has been submitted and is awaiting approval.', 'info')
        
        return redirect(url_for('content.article_view', slug=article.slug))
    
    flash('Error submitting comment.', 'danger')
    return redirect(url_for('content.article_view', slug=article.slug))

@content.route('/articles/new', methods=['GET', 'POST'])
@login_required
def article_create():
    """Create a new article"""
    # Only admins can create articles
    if not current_user.is_admin():
        flash('You do not have permission to create articles.', 'danger')
        return redirect(url_for('content.article_list'))
    
    form = ArticleForm()
    if form.validate_on_submit():
        # Create article
        article = Article(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            author_id=current_user.id,
            summary=form.summary.data,
            is_published=form.is_published.data
        )
        
        # Handle featured image upload
        if form.featured_image.data:
            image_filename = save_file(form.featured_image.data, 'articles')
            if image_filename:
                article.featured_image = image_filename
        
        db.session.add(article)
        db.session.commit()
        
        flash('Article created successfully!', 'success')
        return redirect(url_for('content.article_view', slug=article.slug))
    
    return render_template('content/article_form.html', form=form, title='Create Article')

@content.route('/articles/<slug>/edit', methods=['GET', 'POST'])
@login_required
def article_edit(slug):
    """Edit an article"""
    article = Article.query.filter_by(slug=slug).first_or_404()
    
    # Only author or admin can edit
    if current_user.id != article.author_id and not current_user.is_admin():
        flash('You do not have permission to edit this article.', 'danger')
        return redirect(url_for('content.article_view', slug=article.slug))
    
    form = ArticleForm(obj=article)
    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        article.category = form.category.data
        article.summary = form.summary.data
        
        # Handle published status change
        if form.is_published.data != article.is_published:
            if form.is_published.data:
                article.publish()
            else:
                article.unpublish()
        else:
            article.is_published = form.is_published.data
        
        # Handle featured image upload
        if form.featured_image.data:
            image_filename = save_file(form.featured_image.data, 'articles')
            if image_filename:
                # Delete old image if exists
                if article.featured_image:
                    old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'articles', article.featured_image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                article.featured_image = image_filename
        
        db.session.commit()
        
        flash('Article updated successfully!', 'success')
        return redirect(url_for('content.article_view', slug=article.slug))
    
    return render_template('content/article_form.html', form=form, article=article, title='Edit Article')

# Quiz routes
@content.route('/quizzes')
def quiz_list():
    """List all published quizzes"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    category = request.args.get('category')
    
    # Build query
    query = Quiz.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    quizzes = query.order_by(Quiz.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('content/quiz_list.html', 
                           quizzes=quizzes, 
                           current_category=category)

@content.route('/quizzes/<int:id>')
def quiz_view(id):
    """View a specific quiz"""
    quiz = Quiz.query.get_or_404(id)
    
    # If quiz is not published, only allow author or admin to view
    if not quiz.is_published and (not current_user.is_authenticated or 
                                 (current_user.id != quiz.author_id and not current_user.is_admin())):
        abort(404)
    
    # Check if user has already taken this quiz
    user_attempt = None
    if current_user.is_authenticated:
        user_attempt = QuizAttempt.query.filter_by(
            quiz_id=quiz.id,
            user_id=current_user.id,
            is_completed=True
        ).order_by(QuizAttempt.completed_at.desc()).first()
    
    return render_template('content/quiz_view.html', 
                           quiz=quiz,
                           user_attempt=user_attempt)

@content.route('/quizzes/<int:id>/take', methods=['GET', 'POST'])
@login_required
def quiz_take(id):
    """Take a quiz"""
    quiz = Quiz.query.get_or_404(id)
    
    # If quiz is not published, only allow author or admin to take
    if not quiz.is_published and current_user.id != quiz.author_id and not current_user.is_admin():
        abort(404)
    
    if request.method == 'POST':
        # Process quiz submission
        attempt = QuizAttempt(quiz_id=quiz.id, user_id=current_user.id)
        db.session.add(attempt)
        db.session.commit()
        
        score = 0
        
        # Process each question
        for key, value in request.form.items():
            if key.startswith('question_'):
                question_id = int(key.split('_')[1])
                question = QuizQuestion.query.get(question_id)
                
                if question.question_type == 'multiple_choice':
                    selected_choice_id = int(value)
                    answer = QuizAnswer(
                        attempt_id=attempt.id,
                        question_id=question_id,
                        selected_choice_id=selected_choice_id
                    )
                    db.session.add(answer)
                    
                    # Check if correct
                    if answer.is_correct:
                        score += question.points
                
                elif question.question_type == 'true_false':
                    # For true/false, value will be 'true' or 'false'
                    text_answer = value
                    answer = QuizAnswer(
                        attempt_id=attempt.id,
                        question_id=question_id,
                        text_answer=text_answer
                    )
                    db.session.add(answer)
                    
                    # Check if correct (simplified for example)
                    correct_choice = question.get_correct_choice()
                    if correct_choice and correct_choice.choice_text.lower() == text_answer.lower():
                        answer.is_correct = True
                        score += question.points
                
                elif question.question_type == 'short_answer':
                    text_answer = value
                    answer = QuizAnswer(
                        attempt_id=attempt.id,
                        question_id=question_id,
                        text_answer=text_answer
                    )
                    db.session.add(answer)
                    
                    # Short answers need manual grading, so leave is_correct as False for now
        
        # Complete the attempt
        attempt.complete(score)
        
        flash('Quiz completed! Your score: {:.1f}%'.format(attempt.get_percentage_score()), 'success')
        return redirect(url_for('content.quiz_results', attempt_id=attempt.id))
    
    # Get questions for the quiz
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()
    
    return render_template('content/quiz_take.html', 
                           quiz=quiz,
                           questions=questions)

@content.route('/quiz-results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    """View quiz results"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Only allow the user who took the quiz or an admin to view results
    if attempt.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    
    # Get quiz and questions
    quiz = Quiz.query.get(attempt.quiz_id)
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()
    
    # Get answers for this attempt
    answers = {}
    for answer in attempt.answers:
        answers[answer.question_id] = answer
    
    return render_template('content/quiz_results.html',
                           attempt=attempt,
                           quiz=quiz,
                           questions=questions,
                           answers=answers)

@content.route('/quizzes/new', methods=['GET', 'POST'])
@login_required
def quiz_create():
    """Create a new quiz"""
    # Only admins can create quizzes
    if not current_user.is_admin():
        flash('You do not have permission to create quizzes.', 'danger')
        return redirect(url_for('content.quiz_list'))
    
    form = QuizForm()
    
    # Get articles for dropdown
    articles = Article.query.filter_by(is_published=True).all()
    form.article_id.choices = [(0, 'None')] + [(a.id, a.title) for a in articles]
    
    if form.validate_on_submit():
        # Create quiz
        quiz = Quiz(
            title=form.title.data,
            category=form.category.data,
            author_id=current_user.id,
            description=form.description.data,
            article_id=form.article_id.data if form.article_id.data != 0 else None,
            is_published=form.is_published.data,
            time_limit=form.time_limit.data
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully! Now add some questions.', 'success')
        return redirect(url_for('content.quiz_add_questions', id=quiz.id))
    
    return render_template('content/quiz_form.html', form=form, title='Create Quiz')

@content.route('/quizzes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def quiz_edit(id):
    """Edit a quiz"""
    quiz = Quiz.query.get_or_404(id)
    
    # Only author or admin can edit
    if current_user.id != quiz.author_id and not current_user.is_admin():
        flash('You do not have permission to edit this quiz.', 'danger')
        return redirect(url_for('content.quiz_view', id=quiz.id))
    
    form = QuizForm(obj=quiz)
    
    # Get articles for dropdown
    articles = Article.query.filter_by(is_published=True).all()
    form.article_id.choices = [(0, 'None')] + [(a.id, a.title) for a in articles]
    
    if form.validate_on_submit():
        quiz.title = form.title.data
        quiz.category = form.category.data
        quiz.description = form.description.data
        quiz.article_id = form.article_id.data if form.article_id.data != 0 else None
        quiz.time_limit = form.time_limit.data
        
        # Handle published status change
        if form.is_published.data != quiz.is_published:
            if form.is_published.data:
                quiz.publish()
            else:
                quiz.unpublish()
        else:
            quiz.is_published = form.is_published.data
        
        db.session.commit()
        
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('content.quiz_view', id=quiz.id))
    
    return render_template('content/quiz_form.html', form=form, quiz=quiz, title='Edit Quiz')

@content.route('/quizzes/<int:id>/questions', methods=['GET', 'POST'])
@login_required
def quiz_add_questions(id):
    """Add questions to a quiz"""
    quiz = Quiz.query.get_or_404(id)
    
    # Only author or admin can add questions
    if current_user.id != quiz.author_id and not current_user.is_admin():
        flash('You do not have permission to edit this quiz.', 'danger')
        return redirect(url_for('content.quiz_view', id=quiz.id))
    
    form = QuestionForm()
    
    if form.validate_on_submit():
        # Get the next order number
        next_order = db.session.query(db.func.max(QuizQuestion.order)).\
            filter(QuizQuestion.quiz_id == quiz.id).scalar() or 0
        next_order += 1
        
        # Create question
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=form.question_text.data,
            question_type=form.question_type.data,
            points=form.points.data,
            order=next_order
        )
        
        db.session.add(question)
        db.session.commit()
        
        # Add choices for multiple choice questions
        if question.question_type == 'multiple_choice':
            choices = form.choices.data.split('\n')
            correct_choice = int(form.correct_choice.data)
            
            for i, choice_text in enumerate(choices):
                if choice_text.strip():
                    choice = QuizChoice(
                        question_id=question.id,
                        choice_text=choice_text.strip(),
                        is_correct=(i == correct_choice),
                        order=i
                    )
                    db.session.add(choice)
        
        # Add true/false choices
        elif question.question_type == 'true_false':
            # Add True choice
            true_choice = QuizChoice(
                question_id=question.id,
                choice_text='True',
                is_correct=(form.correct_choice.data == '0'),
                order=0
            )
            db.session.add(true_choice)
            
            # Add False choice
            false_choice = QuizChoice(
                question_id=question.id,
                choice_text='False',
                is_correct=(form.correct_choice.data == '1'),
                order=1
            )
            db.session.add(false_choice)
        
        db.session.commit()
        
        flash('Question added successfully!', 'success')
        return redirect(url_for('content.quiz_add_questions', id=quiz.id))
    
    # Get existing questions
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()
    
    return render_template('content/quiz_questions.html', 
                           form=form, 
                           quiz=quiz, 
                           questions=questions)

# Media routes
@content.route('/media')
def media_list():
    """List all approved media"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    media_type = request.args.get('type')
    
    # Build query
    query = Media.query.filter_by(is_approved=True)
    
    if media_type:
        query = query.filter_by(media_type=media_type)
    
    media = query.order_by(Media.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('content/media_list.html', 
                           media=media, 
                           current_type=media_type)

@content.route('/media/<int:id>')
def media_detail(id):
    """View a specific media item"""
    media = Media.query.get_or_404(id)
    
    # If media is not approved, only allow creator or admin to view
    if not media.is_approved and (not current_user.is_authenticated or 
                                 (current_user.id != media.user_id and not current_user.is_admin())):
        abort(404)
    
    # Increment view count
    media.increment_view_count()
    
    # Get comments
    comments = MediaComment.query.filter_by(
        media_id=media.id, 
        is_approved=True
    ).order_by(MediaComment.created_at.desc()).all()
    
    # Comment form
    comment_form = CommentForm()
    
    # User rating
    user_rating = None
    if current_user.is_authenticated:
        user_rating = MediaRating.query.filter_by(
            media_id=media.id,
            user_id=current_user.id
        ).first()
    
    return render_template('content/media_detail.html', 
                           media=media, 
                           comments=comments,
                           comment_form=comment_form,
                           user_rating=user_rating)

@content.route('/media/<int:id>/comment', methods=['POST'])
@login_required
def media_comment(id):
    """Add a comment to a media item"""
    media = Media.query.get_or_404(id)
    form = CommentForm()
    
    if form.validate_on_submit():
        # Create comment
        comment = MediaComment(
            media_id=media.id,
            user_id=current_user.id,
            content=form.content.data,
            is_approved=current_user.is_admin()  # Auto-approve admin comments
        )
        
        db.session.add(comment)
        db.session.commit()
        
        if comment.is_approved:
            flash('Your comment has been added.', 'success')
        else:
            flash('Your comment has been submitted and is awaiting approval.', 'info')
        
        return redirect(url_for('content.media_detail', id=media.id))
    
    flash('Error submitting comment.', 'danger')
    return redirect(url_for('content.media_detail', id=media.id))

@content.route('/media/<int:id>/rate', methods=['POST'])
@login_required
def media_rate(id):
    """Rate a media item"""
    media = Media.query.get_or_404(id)
    rating_value = request.form.get('rating', type=int)
    
    if not rating_value or rating_value < 1 or rating_value > 5:
        flash('Invalid rating value.', 'danger')
        return redirect(url_for('content.media_detail', id=media.id))
    
    # Check if user already rated this media
    existing_rating = MediaRating.query.filter_by(
        media_id=media.id,
        user_id=current_user.id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_value
        flash('Your rating has been updated.', 'success')
    else:
        # Create new rating
        rating = MediaRating(
            media_id=media.id,
            user_id=current_user.id,
            rating=rating_value
        )
        db.session.add(rating)
        flash('Thank you for rating!', 'success')
    
    db.session.commit()
    return redirect(url_for('content.media_detail', id=media.id))

@content.route('/media/upload', methods=['GET', 'POST'])
@login_required
def media_upload():
    """Upload a new media item"""
    form = MediaUploadForm()
    
    # Get schools for dropdown
    if current_user.is_admin():
        form.school_id.choices = [(0, 'None')] + [(s.id, s.name) for s in School.query.order_by(School.name).all()]
    else:
        # Non-admins can only associate with their school
        if current_user.school_id:
            school = School.query.get(current_user.school_id)
            if school:
                form.school_id.choices = [(school.id, school.name)]
            else:
                form.school_id.choices = [(0, 'None')]
        else:
            form.school_id.choices = [(0, 'None')]
    
    if form.validate_on_submit():
        # Create media item
        media = Media(
            title=form.title.data,
            media_type=form.media_type.data,
            user_id=current_user.id,
            description=form.description.data,
            school_id=form.school_id.data if form.school_id.data != 0 else None,
            tags=form.tags.data
        )
        
        # Handle file upload for video, image, document
        if form.media_type.data in ['video', 'image', 'document']:
            if form.file.data:
                if form.media_type.data == 'image':
                    # For images, create thumbnail
                    filename, thumbnail = save_image_with_thumbnail(form.file.data, 'media')
                    if filename:
                        media.file_path = filename
                        media.thumbnail_path = thumbnail
                else:
                    # For other files, just save the file
                    filename = save_file(form.file.data, 'media')
                    if filename:
                        media.file_path = filename
        
        # Handle external URL for embedded content
        elif form.media_type.data == 'external':
            media.external_url = form.external_url.data
        
        # Auto-approve for admins
        if current_user.is_admin():
            media.is_approved = True
            media.approved_by = current_user.id
            media.approved_at = datetime.utcnow()
        
        db.session.add(media)
        db.session.commit()
        
        if media.is_approved:
            flash('Media uploaded successfully!', 'success')
        else:
            flash('Media uploaded and awaiting approval.', 'info')
        
        return redirect(url_for('content.media_detail', id=media.id))
    
    return render_template('content/media_upload.html', form=form)

@content.route('/media/collections')
def media_collections():
    """List public media collections"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['PAGINATION_PER_PAGE']
    
    collections = MediaCollection.query.filter_by(is_public=True)\
        .order_by(MediaCollection.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('content/collections_list.html', collections=collections)

@content.route('/media/collections/<int:id>')
def media_collection_detail(id):
    """View a specific media collection"""
    collection = MediaCollection.query.get_or_404(id)
    
    # If collection is not public, only allow creator or admin to view
    if not collection.is_public and (not current_user.is_authenticated or 
                                    (current_user.id != collection.created_by and not current_user.is_admin())):
        abort(404)
    
    # Get collection items
    items = collection.items.order_by(MediaCollectionItem.order).all()
    
    return render_template('content/collection_detail.html', 
                           collection=collection, 
                           items=items)