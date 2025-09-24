from rest_framework import serializers
import json
from academics.models import GradeClass, Subject
from reportcard.models import Period
from users.serializers import UserSerializer
from teacherdata.models import TeacherDataProcess
from django.utils.dateparse import parse_datetime
from datetime import datetime
from users.models import User
from .models import Assignment, AssignmentComment, OnlineTest, PeriodicTest, Question, StudentAnswer, TestQuestion, TestSection



class AssignmentReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AssignmentComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at', 'is_edited', 'parent']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited', 'parent']

    def to_representation(self, instance):
        context = self.context
        serializer = UserSerializer(instance.user, context=context)
        ret = super().to_representation(instance)
        ret['user'] = serializer.data
        return ret


class AssignmentCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = AssignmentReplySerializer(many=True, read_only=True)

    class Meta:
        model = AssignmentComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at', 'is_edited', 'replies', 'parent']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_edited', 'replies', 'parent']

    def to_representation(self, instance):
        context = self.context
        serializer = UserSerializer(instance.user, context=context)
        ret = super().to_representation(instance)
        ret['user'] = serializer.data
        # For replies, override similarly
        ret['replies'] = [
            AssignmentReplySerializer(reply, context=context).data
            for reply in instance.replies.all()
        ]
        return ret





class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000)


class ReplyCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000)




class AssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    total_comment_items = serializers.IntegerField(read_only=True)

    user_has_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = '__all__'  # includes above fields + can_edit
        read_only_fields = ['teacher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        # Scope selectable grade_class & subject for teachers
        if user and user.is_authenticated and getattr(user, 'role', None) == 'teacher':
            ta_qs = TeacherDataProcess.objects.filter(teacher=user, is_active=True)
            gc_ids = ta_qs.values_list('grade_class_id', flat=True).distinct()
            subj_ids = ta_qs.values_list('subject_id', flat=True).distinct()
            self.fields['grade_class'].queryset = GradeClass.objects.filter(id__in=gc_ids)
            self.fields['subject'].queryset = Subject.objects.filter(id__in=subj_ids)
        else:
            self.fields['grade_class'].queryset = GradeClass.objects.all()
            self.fields['subject'].queryset = Subject.objects.all()

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        grade_class = attrs.get('grade_class') or getattr(self.instance, 'grade_class', None)
        subject = attrs.get('subject') or getattr(self.instance, 'subject', None)

        if user and user.is_authenticated and getattr(user, 'role', None) == 'teacher':
            ok = TeacherDataProcess.objects.filter(
                teacher=user,
                grade_class=grade_class,
                subject=subject,
                is_active=True,
            ).exists()
            if not ok:
                raise serializers.ValidationError("You are not assigned to this grade class / subject.")
        return attrs

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_can_edit(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or user.is_anonymous:
            return False

        # Only the teacher who created the assignment can edit
        if getattr(user, 'user_type', None) == 'teacher':
            return obj.teacher_id == user.id

        return False



class AssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    teacher_id = serializers.IntegerField(source='teacher.id', read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    total_comment_items = serializers.IntegerField(read_only=True)

    user_has_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = '__all__'  # includes all fields + can_edit + can_delete
        read_only_fields = ['teacher']

    # ... your __init__ and validate methods remain unchanged ...

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_can_edit(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or user.is_anonymous:
            return False
        # Only teacher who created the assignment can edit
        if getattr(user, 'user_type', None) == 'teacher':
            return obj.teacher_id == user.id
        # Staff or admins can edit all (optional)
        if user.is_staff or user.is_superuser:
            return True
        return False

    def get_can_delete(self, obj):
        # Usually delete permission same as edit, but separated if needed
        return self.get_can_edit(obj)



# ---------------------------
# Question
# ---------------------------
class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    question_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'question_image', 'question_image_url', 'attachment', 'structured_payload',
            'marks', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer'
        ]
        extra_kwargs = {
            'question_text': {'required': True},
            'marks': {'required': False},
        }

    def get_question_image_url(self, obj):
        request = self.context.get('request')
        if obj.question_image:
            if request is not None:
                return request.build_absolute_uri(obj.question_image.url)
            else:
                # fallback if no request in context
                return obj.question_image.url
        return None

    def validate(self, attrs):
        return attrs



# ---------------------------
# TestSection
# ---------------------------
class TestSectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = TestSection
        fields = ['id', 'question_type', 'allocated_marks', 'number_of_questions', 'questions']
        extra_kwargs = {
            'allocated_marks': {'required': True},
            'number_of_questions': {'required': False},
        }

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        section = TestSection.objects.create(**validated_data)
        self._create_or_update_questions(section, questions_data)
        return section

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_data is not None:
            self._create_or_update_questions(instance, questions_data, is_update=True)

        return instance

    def _create_or_update_questions(self, section, questions_data, is_update=False):
        existing = {q.id: q for q in section.questions.all()} if is_update else {}
        seen = set()

        for qdata in questions_data:
            q_id = qdata.get('id')
            # Build per-question serializer context w/ this section's qtype
            ctx = {**self.context, 'question_type': section.question_type}
            if is_update and q_id and q_id in existing:
                q_inst = existing[q_id]
                q_ser = QuestionSerializer(q_inst, data=qdata, context=ctx, partial=True)
                q_ser.is_valid(raise_exception=True)
                q_ser.save()
                seen.add(q_id)
            else:
                q_ser = QuestionSerializer(data=qdata, context=ctx)
                q_ser.is_valid(raise_exception=True)
                q_ser.save(section=section)

        if is_update:
            for q_id, q_inst in existing.items():
                if q_id not in seen:
                    q_inst.delete()

        # sync number_of_questions
        section.number_of_questions = section.questions.count()
        section.save(update_fields=['number_of_questions'])


# ---------------------------
# PeriodicTest
# ---------------------------
class PeriodicTestSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)
    grade_class = serializers.PrimaryKeyRelatedField(queryset=GradeClass.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    period = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all())
    sections = TestSectionSerializer(many=True)

    # read-only display fields
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    period_name = serializers.CharField(source='period.name', read_only=True)

    class Meta:
        model = PeriodicTest
        fields = [
            'id', 'direction', 'grade_class', 'grade_class_name',
            'subject', 'subject_name', 'period', 'period_name',
            'teacher', 'total_marks', 'start_time', 'end_time',
            'duration', 'sections'
        ]

    # -----------------------
    # Input normalization
    # -----------------------
    def to_internal_value(self, data):
        """
        Normalize incoming payload:
        - Accept `sections` as JSON string (from multipart) or list.
        - Normalize start_time/end_time (accept HTML datetime-local).
        """
        mutable = dict(data)  # shallow copy

        # sections: if string, parse
        sections_val = mutable.get('sections')
        if isinstance(sections_val, str):
            try:
                mutable['sections'] = json.loads(sections_val)
            except Exception:
                raise serializers.ValidationError({'sections': 'Invalid JSON.'})

        # normalize datetimes
        for field in ('start_time', 'end_time'):
            val = mutable.get(field)
            if val in (None, ''):
                continue
            if isinstance(val, datetime):
                continue  # DRF will keep it
            if isinstance(val, str):
                # Accept "YYYY-MM-DDTHH:MM" (no seconds / tz) from datetime-local inputs
                if len(val) == 16 and 'T' in val:
                    val = val + ':00'  # add seconds
                # Let DRF parse after we reassign; OR parse ourselves:
                parsed = parse_datetime(val)
                if parsed is None:
                    # try timezone make aware naive
                    try:
                        parsed = datetime.fromisoformat(val)
                    except Exception:
                        raise serializers.ValidationError({field: 'Invalid datetime format.'})
                mutable[field] = parsed.isoformat()

        return super().to_internal_value(mutable)

    # -----------------------
    # Global validation
    # -----------------------
    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be after start time."})

        duration = attrs.get('duration')
        if duration is not None and start_time and end_time and duration > (end_time - start_time):
            raise serializers.ValidationError({
                "duration": "Duration cannot be longer than the time window between start and end."
            })

        return attrs

    # -----------------------
    # Create
    # -----------------------
    def create(self, validated_data):
        sections_data = validated_data.pop('sections', [])
        validated_data.pop('teacher', None)

        request = self.context.get('request')
        teacher = getattr(request, 'user', None)
        if not teacher or teacher.is_anonymous:
            raise serializers.ValidationError({"teacher": "Authenticated user required."})

        test = PeriodicTest.objects.create(teacher=teacher, **validated_data)

        # create sections & questions
        for sec_data in sections_data:
            questions_data = sec_data.pop('questions', [])
            section = TestSection.objects.create(test=test, **sec_data)
            for q_data in questions_data:
                Question.objects.create(section=section, **q_data)

        test.update_total_marks()
        return test

    # -----------------------
    # Update
    # -----------------------
    def update(self, instance, validated_data):
        sections_data = validated_data.pop('sections', None)
        partial = self.partial  # respect PATCH vs PUT

        # update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if sections_data is not None:
            self._update_sections(instance, sections_data, partial=partial)

        instance.update_total_marks()
        return instance

    # -----------------------
    # Helpers
    # -----------------------
    def _update_sections(self, instance, sections_data, partial=False):
        existing_sections = {s.id: s for s in instance.sections.all()}
        seen_section_ids = set()

        for sec in sections_data:
            sec_id = sec.get('id')
            questions_data = sec.pop('questions', [])

            if sec_id and sec_id in existing_sections:
                section_obj = existing_sections[sec_id]
                # update section
                for attr, value in sec.items():
                    if attr != 'id':
                        setattr(section_obj, attr, value)
                section_obj.save()
                seen_section_ids.add(sec_id)
            else:
                # create new
                section_obj = TestSection.objects.create(test=instance, **{k: v for k, v in sec.items() if k != 'id'})
                seen_section_ids.add(section_obj.id)

            self._update_questions(section_obj, questions_data, partial=partial)

            # sync number_of_questions
            section_obj.number_of_questions = section_obj.questions.count()
            section_obj.save(update_fields=['number_of_questions'])

        # delete sections missing from payload (for full PUT only)
        if not partial:
            for sec_id, sec_obj in existing_sections.items():
                if sec_id not in seen_section_ids:
                    sec_obj.delete()

    def _update_questions(self, section_obj, questions_data, partial=False):
        existing_qs = {q.id: q for q in section_obj.questions.all()}
        seen_q_ids = set()

        for q in questions_data:
            q_id = q.get('id')
            if q_id and q_id in existing_qs:
                q_obj = existing_qs[q_id]
                for attr, value in q.items():
                    if attr != 'id':
                        setattr(q_obj, attr, value)
                q_obj.save()
                seen_q_ids.add(q_id)
            else:
                q_obj = Question.objects.create(section=section_obj, **{k: v for k, v in q.items() if k != 'id'})
                seen_q_ids.add(q_obj.id)

        # delete missing questions (PUT only)
        if not partial:
          for q_id, q_obj in existing_qs.items():
              if q_id not in seen_q_ids:
                  q_obj.delete()







class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = ['id', 'student', 'question', 'text_answer', 'answer_image', 'structured_response', 'marks_obtained', 'submitted_at']







# //Not used but reserved
class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = '__all__'


class OnlineTestSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)
    questions = TestQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = OnlineTest
        fields = '__all__'
