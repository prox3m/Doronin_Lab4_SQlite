from django.db import models

class Album(models.Model):
    name = models.CharField(max_length=120)
    authors = models.CharField(max_length=200, blank=True, default='')
    length = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    country = models.CharField(max_length=50, blank=True, default='')
    image = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'authors')

    def __str__(self):
        return self.name


class Track(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='tracks')
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name