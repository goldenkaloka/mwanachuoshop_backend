from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import NewUser, Profile

@admin.register(NewUser)
class NewUserAdmin(ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'phonenumber', 'is_active', 'is_staff', 'is_superuser'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phonenumber')
    ordering = ('-id',)
    readonly_fields = ('last_login', 'start_date')
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'phonenumber', 'password')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'start_date')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phonenumber', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_campuses', 'image', 'instagram', 'tiktok', 'facebook')
    search_fields = ('user__username', 'instagram', 'tiktok', 'facebook')
    # Removed list_filter for campus, as campuses is ManyToMany

    def get_campuses(self, obj):
        return ", ".join([c.name for c in obj.campuses.all()])
    get_campuses.short_description = 'Campuses'