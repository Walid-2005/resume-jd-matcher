from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, AnalysisFeedback, EmergingSkill


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username', 'user__email']


@admin.register(AnalysisFeedback)
class AnalysisFeedbackAdmin(admin.ModelAdmin):
    list_display  = ['id', 'score_rating', 'usefulness', 'match_score',
                     'user', 'analysis_id', 'created_at']
    list_filter   = ['score_rating', 'usefulness', 'created_at']
    search_fields = ['comment', 'user__username']
    readonly_fields = ['created_at', 'user_agent', 'ip_hash', 'snapshot',
                       'jd_excerpt']
    date_hierarchy = 'created_at'


@admin.register(EmergingSkill)
class EmergingSkillAdmin(admin.ModelAdmin):
    list_display  = ['token', 'mentions', 'is_promoted', 'first_seen', 'last_seen']
    list_filter   = ['is_promoted', 'first_seen', 'last_seen']
    search_fields = ['token']
    readonly_fields = ['first_seen', 'last_seen']
    date_hierarchy = 'last_seen'
    actions = ['mark_promoted', 'mark_unpromoted']

    @admin.action(description='Mark selected as promoted (already in dictionary)')
    def mark_promoted(self, request, queryset):
        queryset.update(is_promoted=True)

    @admin.action(description='Mark selected as unpromoted')
    def mark_unpromoted(self, request, queryset):
        queryset.update(is_promoted=False)

