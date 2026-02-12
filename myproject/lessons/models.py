from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.mail import send_mail
import uuid

# ---------- Core Profile / Auth ----------

class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="app_profile")
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.email or self.user.username


class EmailVerification(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE, related_name="email_verification")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.user.email} - {'Verified' if self.is_verified else 'Pending'}"

    def send_verification_email(self):
        verify_url = f"http://127.0.0.1:8000/verify/{self.token}/"
        subject = "Verify your email address"
        message = (
            "Welcome to LinguaLearn!\nPlease verify your email by clicking this link:\n"
            f"{verify_url}\n\nIf you didn't register, ignore this message."
        )
        print("📧 Email verification link:", verify_url)
        try:
            send_mail(subject, message, "noreply@lingualearn.com", [self.user.user.email])
        except Exception as e:
            print("Email send failed:", e)


# ---------- Progress / XP ----------

class UserProgress(models.Model):
    app_user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    lessons_completed = models.PositiveIntegerField(default=0)
    quizzes_completed = models.PositiveIntegerField(default=0)
    words_learned = models.PositiveIntegerField(default=0)

    # Optional difficulty breakdown (kept because you asked not to discard)
    easy_words_learned = models.PositiveIntegerField(default=0)
    medium_words_learned = models.PositiveIntegerField(default=0)
    hard_words_learned = models.PositiveIntegerField(default=0)

    streak_days = models.PositiveIntegerField(default=0)
    today_progress = models.FloatField(default=0.0)  # a % if you want

    def __str__(self):
        return f"{self.app_user.user.username}'s Progress"


class DailyXP(models.Model):
    app_user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    xp_gained = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        unique_together = ("app_user", "date", "reason")

    def __str__(self):
        return f"{self.app_user.user.username} • {self.date} • {self.xp_gained} XP"


# ---------- Vocabulary ----------

class VocabularyWord(models.Model):
    DIFFICULTY_CHOICES = [("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")]
    english = models.CharField(max_length=100)
    hindi = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    banner = models.ImageField(upload_to="vocab_banners/", blank=True, null=True)
    video = models.FileField(upload_to="vocab_videos/", blank=True, null=True)
    english_audio = models.FileField(upload_to="vocab_audio/", blank=True, null=True)
    hindi_audio = models.FileField(upload_to="vocab_audio/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.english} — {self.hindi}"


class UserWordProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(VocabularyWord, on_delete=models.CASCADE)
    learned = models.BooleanField(default=False)
    last_practiced = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")

    def __str__(self):
        return f"{self.user.username} • {self.word.english} • {'✓' if self.learned else '…'}"
    

# ---------- Basic Lesson Words (for Unit Lessons) ----------
class LessonBasicWord(models.Model):
    lesson_name = models.CharField(max_length=100, default="Unit 1 - Basic")
    english_word = models.CharField(max_length=100)
    hindi_word = models.CharField(max_length=100)
    english_audio = models.FileField(upload_to="lesson_basic/audio/en/", blank=True, null=True)
    hindi_audio = models.FileField(upload_to="lesson_basic/audio/hi/", blank=True, null=True)
    image = models.ImageField(upload_to="lesson_basic/images/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.english_word} — {self.hindi_word}"

    class Meta:
        ordering = ["order"]


class LessonBasicCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_basic_completions")
    lesson_name = models.CharField(max_length=100)  # e.g. "Unit 1 - Basic"
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.lesson_name} ({'Done' if self.is_completed else 'Pending'})"

    class Meta:
        verbose_name = "Lesson Basic Completion"
        verbose_name_plural = "Lesson Basic Completions"

# ---------- Quiz Questions for Lessons ----------
class LessonQuizQuestion(models.Model):
    lesson_name = models.CharField(max_length=100, default="Unit 1 - Quiz")
    question_text = models.TextField()
    image = models.ImageField(upload_to="lesson_quiz/images/", blank=True, null=True)
    video = models.FileField(upload_to="lesson_quiz/videos/", blank=True, null=True)
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
        default="A"
    )
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.lesson_name}: Q{self.order} - {self.question_text[:40]}"

    class Meta:
        ordering = ["order"]

class LessonQuizCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_quiz_completions")
    lesson_name = models.CharField(max_length=100)
    score = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.lesson_name} ({'Done' if self.is_completed else 'Pending'})"

    class Meta:
        verbose_name = "Lesson Quiz Completion"
        verbose_name_plural = "Lesson Quiz Completions"