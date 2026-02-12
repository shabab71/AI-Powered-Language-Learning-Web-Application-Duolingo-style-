from django.contrib import admin
from .models import (
    AppUser, EmailVerification, LessonQuizCompletion, LessonQuizQuestion, UserProgress, DailyXP,
    VocabularyWord, UserWordProgress, LessonBasicWord, LessonBasicCompletion,
)

# Inline blocks
class EmailVerificationInline(admin.StackedInline):
    model = EmailVerification
    extra = 0
    can_delete = False
    readonly_fields = ("token", "created_at")


class UserProgressInline(admin.StackedInline):
    model = UserProgress
    extra = 0
    readonly_fields = ("today_progress",)


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "created_at", "is_verified")
    search_fields = ("user__username", "user__email", "phone")
    list_filter = ("created_at",)
    inlines = [EmailVerificationInline, UserProgressInline]

    def is_verified(self, obj):
        return getattr(obj.email_verification, "is_verified", False)
    is_verified.boolean = True
    is_verified.short_description = "Verified"


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "is_verified", "token", "created_at")
    search_fields = ("user__user__email", "token")
    list_filter = ("is_verified", "created_at")
    readonly_fields = ("token", "created_at")
    ordering = ("-created_at",)


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = (
        "app_user",
        "lessons_completed", "quizzes_completed",
        "words_learned", "easy_words_learned", "medium_words_learned", "hard_words_learned",
        "streak_days", "today_progress",
    )
    list_filter = ("streak_days",)
    search_fields = ("app_user__user__email", "app_user__user__username")
    ordering = ("-today_progress",)


@admin.register(DailyXP)
class DailyXPAdmin(admin.ModelAdmin):
    list_display = ("app_user", "date", "xp_gained", "reason")
    list_filter = ("date",)
    search_fields = ("app_user__user__username", "reason")


@admin.register(VocabularyWord)
class VocabularyWordAdmin(admin.ModelAdmin):
    list_display = ("english", "hindi", "difficulty")
    search_fields = ("english", "hindi")
    list_filter = ("difficulty",)
    fieldsets = (
        (None, {"fields": ("english", "hindi", "difficulty", "banner", "video",
                           "english_audio", "hindi_audio", "description")}),
    )


@admin.register(UserWordProgress)
class UserWordProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "learned", "last_practiced")
    list_filter = ("learned", "last_practiced")
    search_fields = ("user__username", "word__english")



# ---------- Lesson: Unit 1 Basic ----------
@admin.register(LessonBasicWord)
class LessonBasicWordAdmin(admin.ModelAdmin):
    list_display = ("lesson_name", "english_word", "hindi_word", "order")
    search_fields = ("english_word", "hindi_word", "lesson_name")
    list_filter = ("lesson_name",)
    ordering = ("lesson_name", "order")
    fieldsets = (
        (None, {
            "fields": (
                "lesson_name",
                "english_word",
                "hindi_word",
                "english_audio",
                "hindi_audio",
                "image",
                "order",
            )
        }),
    )

@admin.register(LessonBasicCompletion)
class LessonBasicCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson_name", "is_completed", "completed_at")
    list_filter = ("is_completed", "lesson_name")
    search_fields = ("user__username", "lesson_name")
    ordering = ("-completed_at",)


# ---------- Lesson: Unit 1 Quiz ----------
@admin.register(LessonQuizQuestion)
class LessonQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("lesson_name", "order", "question_text", "correct_option")
    search_fields = ("lesson_name", "question_text")
    list_filter = ("lesson_name",)
    ordering = ("lesson_name", "order")
    fieldsets = (
        (None, {
            "fields": (
                "lesson_name",
                "order",
                "question_text",
                "image",
                "video",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_option",
            )
        }),
    )


@admin.register(LessonQuizCompletion)
class LessonQuizCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson_name", "score", "is_completed", "completed_at")
    list_filter = ("is_completed", "lesson_name")
    search_fields = ("user__username", "lesson_name")
    ordering = ("-completed_at",)