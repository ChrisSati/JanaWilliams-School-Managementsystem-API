from django.contrib import admin
from .models import Assignment, OnlineTest, PeriodicTest, Question, StudentAnswer, TestQuestion, TestSection


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'subject', 'grade_class', 'due_date', 'created_at')
    search_fields = ('title', 'teacher__full_name')
    list_filter = ('subject', 'grade_class', 'due_date')


@admin.register(OnlineTest)
class OnlineTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'subject', 'grade_class', 'start_time', 'end_time')
    search_fields = ('title', 'teacher__full_name')
    list_filter = ('subject', 'grade_class')


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('online_test', 'question_text', 'correct_option')
    search_fields = ('question_text',)



# New

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = (
        'question_text', 'question_image', 'attachment', 'marks',
        'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer'
    )

class TestSectionInline(admin.StackedInline):
    model = TestSection
    extra = 1
    fields = ('question_type', 'allocated_marks', 'number_of_questions')
    show_change_link = True


@admin.register(PeriodicTest)
class PeriodicTestAdmin(admin.ModelAdmin):
    list_display = ('direction', 'grade_class', 'subject', 'period', 'teacher', 'total_marks', 'start_time', 'end_time', 'duration', 'created_at')
    search_fields = ('direction', 'grade_class__name', 'subject__name')
    list_filter = ('grade_class', 'subject', 'period')
    inlines = [TestSectionInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.update_total_marks()


@admin.register(TestSection)
class TestSectionAdmin(admin.ModelAdmin):
    list_display = ('test', 'question_type', 'allocated_marks', 'number_of_questions')
    list_filter = ('question_type',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('section', 'short_question_text', 'marks', 'has_image', 'has_attachment')
    list_filter = ('section__test__grade_class', 'section__question_type')
    search_fields = ('question_text',)

    def short_question_text(self, obj):
        return (obj.question_text[:50] + '...') if len(obj.question_text) > 50 else obj.question_text
    short_question_text.short_description = 'Question'

    def has_image(self, obj):
        return bool(obj.question_image)
    has_image.boolean = True

    def has_attachment(self, obj):
        return bool(obj.attachment)
    has_attachment.boolean = True


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'marks_obtained', 'submitted_at')
    list_filter = ('submitted_at', 'question__section__test__subject')
    search_fields = ('student__username', 'question__question_text')
