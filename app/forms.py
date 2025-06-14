from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, DateField, MultipleFileField, HiddenField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError, Regexp
from app.models.user import User
from app.models.volunteer import Volunteer
from app.models.school import School
from flask_login import current_user

# Authentication Forms
class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='يرجى إدخال كلمة المرور')
    ])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegistrationForm(FlaskForm):
    name = StringField('الاسم', validators=[
        DataRequired(message='يرجى إدخال الاسم'),
        Length(min=2, max=100, message='يجب أن يكون الاسم بين 2 و 100 حرف')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    password = PasswordField('كلمة المرور', validators=[
        DataRequired(message='يرجى إدخال كلمة المرور'),
        Length(min=8, message='يجب أن تكون كلمة المرور 8 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='يرجى تأكيد كلمة المرور'),
        EqualTo('password', message='كلمات المرور غير متطابقة')
    ])
    submit = SubmitField('تسجيل')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('هذا البريد الإلكتروني مسجل بالفعل')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    submit = SubmitField('إرسال')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('كلمة المرور الجديدة', validators=[
        DataRequired(message='يرجى إدخال كلمة المرور'),
        Length(min=8, message='يجب أن تكون كلمة المرور 8 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        DataRequired(message='يرجى تأكيد كلمة المرور'),
        EqualTo('password', message='كلمات المرور غير متطابقة')
    ])
    submit = SubmitField('إعادة تعيين كلمة المرور')

# School Forms
class SchoolForm(FlaskForm):
    name = StringField('اسم المدرسة', validators=[
        DataRequired(message='يرجى إدخال اسم المدرسة'),
        Length(min=3, max=100, message='يجب أن يكون اسم المدرسة بين 3 و 100 حرف')
    ])
    address = StringField('العنوان', validators=[
        DataRequired(message='يرجى إدخال عنوان المدرسة'),
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    city = StringField('المدينة', validators=[
        DataRequired(message='يرجى إدخال المدينة'),
        Length(min=2, max=50, message='يجب أن تكون المدينة بين 2 و 50 حرف')
    ])
    phone = StringField('رقم الهاتف', validators=[
        DataRequired(message='يرجى إدخال رقم الهاتف'),
        Regexp(r'^[0-9+\-\s()]+$', message='يرجى إدخال رقم هاتف صحيح')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    website = StringField('الموقع الإلكتروني', validators=[
        Optional(),
        Length(max=100, message='يجب أن لا يتجاوز الموقع الإلكتروني 100 حرف')
    ])
    description = TextAreaField('وصف المدرسة', validators=[
        Optional(),
        Length(max=500, message='يجب أن لا يتجاوز الوصف 500 حرف')
    ])
    submit = SubmitField('حفظ')

# Volunteer Forms
class VolunteerForm(FlaskForm):
    name = StringField('الاسم', validators=[
        DataRequired(message='يرجى إدخال الاسم'),
        Length(min=2, max=100, message='يجب أن يكون الاسم بين 2 و 100 حرف')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    phone = StringField('رقم الهاتف', validators=[
        DataRequired(message='يرجى إدخال رقم الهاتف'),
        Regexp(r'^[0-9+\-\s()]+$', message='يرجى إدخال رقم هاتف صحيح')
    ])
    school_id = SelectField('المدرسة', coerce=int, validators=[
        DataRequired(message='يرجى اختيار المدرسة')
    ])
    grade = SelectField('الصف الدراسي', choices=[
        ('', 'اختر الصف الدراسي'),
        ('primary_1', 'الصف الأول الابتدائي'),
        ('primary_2', 'الصف الثاني الابتدائي'),
        ('primary_3', 'الصف الثالث الابتدائي'),
        ('primary_4', 'الصف الرابع الابتدائي'),
        ('primary_5', 'الصف الخامس الابتدائي'),
        ('primary_6', 'الصف السادس الابتدائي'),
        ('prep_1', 'الصف الأول الإعدادي'),
        ('prep_2', 'الصف الثاني الإعدادي'),
        ('prep_3', 'الصف الثالث الإعدادي'),
        ('secondary_1', 'الصف الأول الثانوي'),
        ('secondary_2', 'الصف الثاني الثانوي'),
        ('secondary_3', 'الصف الثالث الثانوي'),
        ('graduate', 'خريج'),
        ('teacher', 'معلم'),
        ('other', 'أخرى')
    ], validators=[DataRequired(message='يرجى اختيار الصف الدراسي')])
    skills = SelectMultipleField('المهارات', choices=[
        ('teaching', 'التدريس'),
        ('art', 'الفنون'),
        ('music', 'الموسيقى'),
        ('sports', 'الرياضة'),
        ('technology', 'التكنولوجيا'),
        ('writing', 'الكتابة'),
        ('organization', 'التنظيم'),
        ('leadership', 'القيادة'),
        ('other', 'أخرى')
    ], validators=[DataRequired(message='يرجى اختيار مهارة واحدة على الأقل')])
    experience = TextAreaField('الخبرات السابقة', validators=[
        Optional(),
        Length(max=500, message='يجب أن لا تتجاوز الخبرات 500 حرف')
    ])
    availability = SelectField('التوفر', choices=[
        ('weekdays', 'أيام الأسبوع'),
        ('weekends', 'عطلة نهاية الأسبوع'),
        ('evenings', 'المساء'),
        ('flexible', 'مرن')
    ], validators=[DataRequired(message='يرجى اختيار التوفر')])
    submit = SubmitField('تسجيل')

# Article Forms
class ArticleForm(FlaskForm):
    title = StringField('العنوان', validators=[
        DataRequired(message='يرجى إدخال عنوان المقال'),
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    content = TextAreaField('المحتوى', validators=[
        DataRequired(message='يرجى إدخال محتوى المقال'),
        Length(min=100, message='يجب أن يكون المحتوى 100 حرف على الأقل')
    ])
    category = SelectField('التصنيف', choices=[
        ('education', 'تعليم'),
        ('culture', 'ثقافة'),
        ('history', 'تاريخ'),
        ('tourism', 'سياحة'),
        ('other', 'أخرى')
    ], validators=[DataRequired(message='يرجى اختيار تصنيف')])
    image = FileField('الصورة', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], message='يرجى اختيار صورة بصيغة jpg أو png أو jpeg')
    ])
    submit = SubmitField('نشر')

# Quiz Forms
class QuizForm(FlaskForm):
    title = StringField('عنوان الاختبار', validators=[
        DataRequired(message='يرجى إدخال عنوان الاختبار'),
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    description = TextAreaField('وصف الاختبار', validators=[
        Optional(),
        Length(max=500, message='يجب أن لا يتجاوز الوصف 500 حرف')
    ])
    category = SelectField('التصنيف', choices=[
        ('general', 'معلومات عامة'),
        ('history', 'تاريخ'),
        ('geography', 'جغرافيا'),
        ('culture', 'ثقافة'),
        ('other', 'أخرى')
    ], validators=[DataRequired(message='يرجى اختيار تصنيف')])
    submit = SubmitField('إنشاء')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('السؤال', validators=[
        DataRequired(message='يرجى إدخال السؤال'),
        Length(min=5, max=500, message='يجب أن يكون السؤال بين 5 و 500 حرف')
    ])
    choice1 = StringField('الخيار الأول', validators=[
        DataRequired(message='يرجى إدخال الخيار الأول'),
        Length(max=200, message='يجب أن لا يتجاوز الخيار 200 حرف')
    ])
    choice2 = StringField('الخيار الثاني', validators=[
        DataRequired(message='يرجى إدخال الخيار الثاني'),
        Length(max=200, message='يجب أن لا يتجاوز الخيار 200 حرف')
    ])
    choice3 = StringField('الخيار الثالث', validators=[
        DataRequired(message='يرجى إدخال الخيار الثالث'),
        Length(max=200, message='يجب أن لا يتجاوز الخيار 200 حرف')
    ])
    choice4 = StringField('الخيار الرابع', validators=[
        DataRequired(message='يرجى إدخال الخيار الرابع'),
        Length(max=200, message='يجب أن لا يتجاوز الخيار 200 حرف')
    ])
    correct_choice = SelectField('الإجابة الصحيحة', choices=[
        ('1', 'الخيار الأول'),
        ('2', 'الخيار الثاني'),
        ('3', 'الخيار الثالث'),
        ('4', 'الخيار الرابع')
    ], validators=[DataRequired(message='يرجى اختيار الإجابة الصحيحة')])
    explanation = TextAreaField('شرح الإجابة', validators=[
        Length(max=500, message='يجب أن لا يتجاوز الشرح 500 حرف')
    ])
    submit = SubmitField('حفظ')

class MediaUploadForm(FlaskForm):
    title = StringField('العنوان', validators=[
        DataRequired(message='يرجى إدخال عنوان الوسائط'),
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    description = TextAreaField('الوصف', validators=[
        DataRequired(message='يرجى إدخال وصف الوسائط'),
        Length(max=500, message='يجب أن لا يتجاوز الوصف 500 حرف')
    ])
    media_type = SelectField('نوع الوسائط', choices=[
        ('image', 'صورة'),
        ('video', 'فيديو'),
        ('document', 'مستند'),
        ('audio', 'صوت')
    ], validators=[DataRequired(message='يرجى اختيار نوع الوسائط')])
    file = FileField('الملف', validators=[
        FileRequired(message='يرجى اختيار ملف'),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'mp4', 'pdf', 'doc', 'docx', 'mp3', 'wav'], 
                    message='صيغة الملف غير مدعومة')
    ])
    category = SelectField('التصنيف', choices=[
        ('project', 'مشروع طلابي'),
        ('activity', 'نشاط مدرسي'),
        ('artwork', 'عمل فني'),
        ('presentation', 'عرض تقديمي'),
        ('other', 'أخرى')
    ], validators=[DataRequired(message='يرجى اختيار تصنيف')])
    submit = SubmitField('رفع')

# Report Forms
class ReportForm(FlaskForm):
    title = StringField('عنوان التقرير', validators=[
        DataRequired(message='يرجى إدخال عنوان التقرير'),
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    activity_date = DateField('تاريخ النشاط', format='%Y-%m-%d', validators=[
        DataRequired(message='يرجى إدخال تاريخ النشاط')
    ])
    description = TextAreaField('وصف النشاط', validators=[
        DataRequired(message='يرجى إدخال وصف النشاط'),
        Length(min=50, max=2000, message='يجب أن يكون الوصف بين 50 و 2000 حرف')
    ])
    participants_count = IntegerField('عدد المشاركين', validators=[
        DataRequired(message='يرجى إدخال عدد المشاركين'),
        NumberRange(min=1, message='يجب أن يكون عدد المشاركين أكبر من صفر')
    ])
    attachments = MultipleFileField('المرفقات', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'pdf', 'doc', 'docx'], 
                    message='صيغة الملف غير مدعومة (jpg, png, jpeg, pdf, doc, docx)')
    ])
    submit = SubmitField('إرسال التقرير')

# Support Form
class ContactForm(FlaskForm):
    name = StringField('الاسم', validators=[
        DataRequired(message='يرجى إدخال الاسم'),
        Length(min=2, max=100, message='يجب أن يكون الاسم بين 2 و 100 حرف')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    subject = StringField('الموضوع', validators=[
        DataRequired(message='يرجى إدخال الموضوع'),
        Length(min=5, max=200, message='يجب أن يكون الموضوع بين 5 و 200 حرف')
    ])
    category = SelectField('نوع الاستفسار', choices=[
        ('technical', 'مشكلة تقنية'),
        ('content', 'استفسار عن المحتوى'),
        ('volunteer', 'استفسار عن التطوع'),
        ('school', 'استفسار عن المدارس'),
        ('other', 'أخرى')
    ], validators=[DataRequired(message='يرجى اختيار نوع الاستفسار')])
    message = TextAreaField('الرسالة', validators=[
        DataRequired(message='يرجى إدخال الرسالة'),
        Length(min=20, max=2000, message='يجب أن تكون الرسالة بين 20 و 2000 حرف')
    ])
    submit = SubmitField('إرسال')

# Search Form
class SearchForm(FlaskForm):
    query = StringField('بحث', validators=[
        DataRequired(message='يرجى إدخال كلمات البحث'),
        Length(min=2, message='يجب أن تكون كلمات البحث حرفين على الأقل')
    ])
    category = SelectField('التصنيف', choices=[
        ('all', 'الكل'),
        ('articles', 'المقالات'),
        ('schools', 'المدارس'),
        ('volunteers', 'المتطوعين'),
        ('media', 'الوسائط')
    ], default='all')
    submit = SubmitField('بحث')

# Comment Form
class CommentForm(FlaskForm):
    content = TextAreaField('التعليق', validators=[
        DataRequired(message='يرجى إدخال التعليق'),
        Length(min=2, max=500, message='يجب أن يكون التعليق بين 2 و 500 حرف')
    ])
    submit = SubmitField('إرسال')

# Activity Form
class ActivityForm(FlaskForm):
    title = StringField('عنوان النشاط', validators=[
        DataRequired(message='يرجى إدخال عنوان النشاط'),
        Length(min=5, max=200, message='يجب أن يكون العنوان بين 5 و 200 حرف')
    ])
    description = TextAreaField('وصف النشاط', validators=[
        DataRequired(message='يرجى إدخال وصف النشاط'),
        Length(min=20, max=2000, message='يجب أن يكون الوصف بين 20 و 2000 حرف')
    ])
    date = DateField('تاريخ النشاط', format='%Y-%m-%d', validators=[
        DataRequired(message='يرجى إدخال تاريخ النشاط')
    ])
    location = StringField('مكان النشاط', validators=[
        DataRequired(message='يرجى إدخال مكان النشاط'),
        Length(max=200, message='يجب أن لا يتجاوز المكان 200 حرف')
    ])
    status = SelectField('حالة النشاط', choices=[
        ('planned', 'مخطط'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ], validators=[DataRequired(message='يرجى اختيار حالة النشاط')])
    submit = SubmitField('حفظ')

# User Profile Form
class ProfileForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[
        DataRequired(message='يرجى إدخال اسم المستخدم'),
        Length(min=2, max=50, message='يجب أن يكون اسم المستخدم بين 2 و 50 حرف')
    ])
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يرجى إدخال البريد الإلكتروني'),
        Email(message='يرجى إدخال بريد إلكتروني صحيح')
    ])
    first_name = StringField('الاسم الأول', validators=[
        Optional(),
        Length(max=50, message='يجب أن لا يتجاوز الاسم الأول 50 حرف')
    ])
    last_name = StringField('الاسم الأخير', validators=[
        Optional(),
        Length(max=50, message='يجب أن لا يتجاوز الاسم الأخير 50 حرف')
    ])
    bio = TextAreaField('نبذة شخصية', validators=[
        Optional(),
        Length(max=500, message='يجب أن لا تتجاوز النبذة الشخصية 500 حرف')
    ])
    current_password = PasswordField('كلمة المرور الحالية', validators=[
        Optional()
    ])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[
        Optional(),
        Length(min=8, message='يجب أن تكون كلمة المرور 8 أحرف على الأقل')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[
        EqualTo('new_password', message='كلمات المرور غير متطابقة')
    ])
    submit = SubmitField('تحديث')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('هذا البريد الإلكتروني مسجل بالفعل')