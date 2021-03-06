from django.conf.urls import patterns, include, url

from webgui.views import list_posts, get_post

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    ('^$', list_posts),
    ('^post$', get_post),
    # Examples:
    # url(r'^$', 'webgui.views.home', name='home'),
    # url(r'^web/', include('webgui.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
