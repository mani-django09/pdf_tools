from django.contrib.sitemaps import Sitemap

# Define all the classes expected by your urls.py import statement
class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'
    
    def items(self):
        return [{'url': '/', 'priority': 1.0}]
    
    def location(self, item):
        return item['url']
    
    def priority(self, item):
        return item.get('priority', self.priority)


class ToolSitemap(Sitemap):
    priority = 0.9
    changefreq = 'monthly'
    
    def items(self):
        return [
            {'url': '/pdf-to-png/'},
            {'url': '/pdf-to-jpg/'},
            {'url': '/pdf-to-word/'},
            {'url': '/word-to-pdf/'},
        ]
    
    def location(self, item):
        return item['url']


class ImageToolSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'
    
    def items(self):
        return [
            {'url': '/jpg-to-pdf/'},
            {'url': '/jpg-to-png/'},
            {'url': '/png-to-jpg/'},
            {'url': '/png-to-pdf/'},
            {'url': '/png-to-webp/'},
            {'url': '/webp-to-png/'},
        ]
    
    def location(self, item):
        return item['url']


class InfoPageSitemap(Sitemap):
    priority = 0.4
    changefreq = 'yearly'
    
    def items(self):
        return [
            {'url': '/about-us/'},
            {'url': '/contact/'},
            {'url': '/privacy-policy/'},
            {'url': '/terms-of-service/'},
        ]
    
    def location(self, item):
        return item['url']