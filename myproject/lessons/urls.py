from django.urls import path
from . import views

app_name = "lessons"

urlpatterns = [
    # auth
    path("", views.auth_page, name="auth_page"),
    path("register/", views.register_user, name="register_user"),
    path("login/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout_user"),
    path("verify/<uuid:token>/", views.verify_email, name="verify_email"),

    # app pages
    path("dashboard/", views.dashboard, name="dashboard"),
    path("vocabulary/", views.vocabulary_view, name="vocabulary"),
    path("lessons/", views.lessons_view, name="lessons"),
    path("lesson/unit1/basic/", views.lesson_unit1_basic, name="lesson_unit1_basic"),
    path("lesson/unit1/quiz/", views.lesson_unit1_quiz, name="lesson_unit1_quiz"),
    
    # ajax/data
    path("user-stats/", views.user_stats_view, name="user_stats"),
    path("difficulty-stats/", views.difficulty_stats_view, name="difficulty_stats"),
    path("vocabulary/learn/<int:word_id>/", views.mark_word_learned, name="mark_word_learned"),
    path("api/lesson/basic/complete/", views.mark_lesson_basic_completed, name="mark_lesson_basic_completed"),
    path("api/lesson/quiz/complete/", views.mark_lesson_quiz_completed, name="mark_lesson_quiz_completed"),
]
