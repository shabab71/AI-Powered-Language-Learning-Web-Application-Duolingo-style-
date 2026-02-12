from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from .models import LessonBasicWord, LessonBasicCompletion, LessonQuizCompletion, LessonQuizQuestion

from .models import (
    AppUser, EmailVerification, LessonBasicWord, UserProgress,
    VocabularyWord, UserWordProgress, DailyXP,
)
import uuid

# ---------------- Auth ----------------

def auth_page(request):
    return render(request, "auth2.html")

def register_user(request):
    if request.method == "POST":
        first = request.POST.get("firstName")
        last = request.POST.get("lastName")
        email = request.POST.get("email", "").lower().strip()
        phone = request.POST.get("phone")
        password = request.POST.get("password")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists. Please log in.")
            return redirect("lessons:auth_page")

        user = User.objects.create_user(
            username=email, email=email, password=password,
            first_name=first, last_name=last
        )
        app_user = AppUser.objects.create(user=user, phone=phone)

        verification, _ = EmailVerification.objects.get_or_create(user=app_user)
        verification.token = uuid.uuid4()
        verification.is_verified = False
        verification.save()

        try:
            verification.send_verification_email()
            messages.success(request, "✅ Account created! Check console for verification link.")
        except Exception as e:
            print("Email send failed:", e)
            messages.warning(request, "Account created but email not sent (check console).")

        return redirect("lessons:auth_page")

    return render(request, "auth2.html")

def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or 'User'}!")
            return redirect("lessons:dashboard")
        messages.error(request, "Invalid email or password.")
        return redirect("lessons:auth_page")
    return render(request, "auth2.html")

def logout_user(request):
    logout(request)
    messages.info(request, "You’ve been logged out.")
    return redirect("lessons:auth_page")


@login_required
def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        if not verification.is_verified:
            verification.is_verified = True
            verification.save()
            message = "✅ Email verified successfully!"
        else:
            message = "ℹ️ Email already verified."
    except EmailVerification.DoesNotExist:
        message = "❌ Invalid or expired verification link."
    return render(request, "verify_result.html", {"message": message})

# ---------------- Dashboard ----------------

@login_required
def dashboard(request):
    app_user = get_object_or_404(AppUser, user=request.user)
    progress, _ = UserProgress.objects.get_or_create(app_user=app_user)
    return render(request, "dashboard.html", {"progress": progress})

@login_required
def user_stats_view(request):
    app_user = get_object_or_404(AppUser, user=request.user)
    progress = get_object_or_404(UserProgress, app_user=app_user)

    # 🧮 Compute total XP
    total_xp = (
        DailyXP.objects.filter(app_user=app_user)
        .aggregate(Sum("xp_gained"))
        .get("xp_gained__sum") or 0
    )

    data = {
        "lessons_completed": progress.lessons_completed,
        "quizzes_completed": progress.quizzes_completed,
        "words_learned": progress.words_learned,
        "streak_days": progress.streak_days,
        "today_progress": progress.today_progress,
        "xp": total_xp,      # 👈 added key
    }
    return JsonResponse(data)

@login_required
def difficulty_stats_view(request):
    app_user = get_object_or_404(AppUser, user=request.user)
    up = get_object_or_404(UserProgress, app_user=app_user)

    # Difficulty counts
    easy = up.easy_words_learned
    med = up.medium_words_learned
    hard = up.hard_words_learned

    # XP for last 7 days
    today = timezone.now().date()
    xp_chart = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        xp = DailyXP.objects.filter(app_user=app_user, date=d).aggregate(Sum("xp_gained"))["xp_gained__sum"] or 0
        xp_chart.append({"day": d.strftime("%a"), "xp": xp})

    data = {
        "easy": easy,
        "medium": med,
        "hard": hard,
        "total_words": up.words_learned,
        "xp_total": sum(x["xp"] for x in xp_chart),
        "xp_chart": xp_chart,
        "streak": up.streak_days,
    }
    return JsonResponse(data)

# ---------------- Vocabulary ----------------

@login_required
def vocabulary_view(request):
    words = VocabularyWord.objects.all().order_by("english")
    learned_ids = set(
        UserWordProgress.objects.filter(user=request.user, learned=True).values_list("word_id", flat=True)
    )
    return render(request, "vocabulary.html", {"words": words, "learned_ids": learned_ids})

@login_required
def mark_word_learned(request, word_id):
    word = get_object_or_404(VocabularyWord, id=word_id)
    wp, _ = UserWordProgress.objects.get_or_create(user=request.user, word=word)
    if not wp.learned:
        wp.learned = True
        wp.save()

        app_user = get_object_or_404(AppUser, user=request.user)
        up, _ = UserProgress.objects.get_or_create(app_user=app_user)
        up.words_learned = UserWordProgress.objects.filter(user=request.user, learned=True).count()

        # also bump difficulty counters
        if word.difficulty == "easy":
            up.easy_words_learned += 1
        elif word.difficulty == "medium":
            up.medium_words_learned += 1
        else:
            up.hard_words_learned += 1

        up.save()

        # award XP (e.g., 5 XP/word)
        DailyXP.objects.update_or_create(
            app_user=app_user,
            date=timezone.now().date(),
            reason="vocab",
            defaults={"xp_gained": (DailyXP.objects.filter(app_user=app_user, date=timezone.now().date(), reason="vocab")
                                    .aggregate(Sum("xp_gained"))["xp_gained__sum"] or 0) + 5}
        )

    return JsonResponse({"success": True})

@login_required
def lessons_view(request):
    return render(request, "lessons.html")


@login_required
def lesson_unit1_basic(request):
    """Render Unit 1 Basic with the 10 words slideshow."""
    #words = LessonBasicWord.objects.filter(unit=1).order_by("order")
    words = LessonBasicWord.objects.filter(lesson_name="Unit 1 - Basic").order_by("order")
    return render(request, "lessons/lesson-unit1-basic.html", {"words": words})


@csrf_exempt
@login_required
def mark_lesson_basic_completed(request):
    """AJAX endpoint triggered when the user finishes Unit 1 Basic."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

    user = request.user
    lesson_name = request.POST.get("lesson_name", "Unit 1 - Basic")
    xp_award = 20

    # ✅ Create or update completion record
    completion, created = LessonBasicCompletion.objects.get_or_create(
        user=user,
        lesson_name=lesson_name
    )

    if created or not completion.is_completed:
        completion.is_completed = True
        completion.completed_at = timezone.now()
        completion.save()

        # ✅ Link AppUser
        app_user = get_object_or_404(AppUser, user=user)

        # ✅ Update UserProgress
        progress, _ = UserProgress.objects.get_or_create(app_user=app_user)
        progress.lessons_completed += 1
        progress.today_progress = min(progress.today_progress + 10, 100)  # optional %
        progress.save()

        # ✅ Award XP to DailyXP
        DailyXP.objects.update_or_create(
            app_user=app_user,
            date=timezone.now().date(),
            reason="lesson_basic",
            defaults={
                "xp_gained": (DailyXP.objects.filter(
                    app_user=app_user, date=timezone.now().date(), reason="lesson_basic"
                ).aggregate(Sum("xp_gained"))["xp_gained__sum"] or 0) + xp_award
            },
        )

        message = f"✅ Lesson completed! +{xp_award} XP earned."
    else:
        message = "ℹ️ Lesson already marked complete."

    return JsonResponse({"success": True, "message": message})

@login_required
def lesson_unit1_quiz(request):
    questions = LessonQuizQuestion.objects.filter(lesson_name="Unit 1 - Quiz").order_by("order")
    return render(request, "lessons/lesson-unit1-quiz.html", {"questions": questions})

@csrf_exempt
@login_required
def mark_lesson_quiz_completed(request):
    """Called when a quiz is finished — award XP and mark quiz as completed."""
    user = request.user
    lesson_name = request.POST.get("lesson_name", "Unit 1 Quiz")
    score = int(request.POST.get("score", 0))

    # mark completion
    completion, created = LessonBasicCompletion.objects.get_or_create(
        user=user, lesson_name=lesson_name
    )
    completion.is_completed = True
    completion.completed_at = timezone.now()
    completion.save()

    # update user progress and XP
    app_user = AppUser.objects.get(user=user)
    progress, _ = UserProgress.objects.get_or_create(app_user=app_user)

    # increment quiz completion count
    progress.quizzes_completed += 1

    # award XP (e.g., 30 XP for completing quiz)
    DailyXP.objects.update_or_create(
        app_user=app_user,
        date=timezone.now().date(),
        reason="quiz",
        defaults={
            "xp_gained": (
                DailyXP.objects.filter(
                    app_user=app_user, date=timezone.now().date(), reason="quiz"
                ).aggregate(Sum("xp_gained"))["xp_gained__sum"]
                or 0
            )
            + 30
        },
    )

    progress.save()

    return JsonResponse({"success": True, "message": "✅ Quiz completed +30 XP!"})