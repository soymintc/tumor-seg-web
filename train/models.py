import os
import glob
import psutil
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError



def validate_optimizer(value):
    if value not in ['adam', 'sgd']:
        raise ValidationError("optimizer '{}' should be either adam or sgd".format(value))


class Train(models.Model):
    # Creation attrs
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)

    title = models.CharField(max_length=255)

    batch_size = models.PositiveIntegerField()
    image_size = models.PositiveIntegerField()
    n_validation = models.PositiveIntegerField()
    n_test = models.PositiveIntegerField()

    learning_rate = models.FloatField(
        validators=[MinValueValidator(1e-20), MaxValueValidator(1)],)

    optimizer = models.CharField(max_length=10, validators=[validate_optimizer])
    group_size = models.PositiveIntegerField()
    filters_root = models.PositiveIntegerField()
    augment = models.BooleanField()

    # Non-input attrs    
    pid = models.PositiveIntegerField(default=0)
    cmd_str = models.CharField(max_length=1000, default='.')


    def __str__(self):
        return self.title
    
    def pid_exists(self):
        return psutil.pid_exists(self.pid)

    def run_phase(self):
        return self.pid == 0

    def get_log_path(self):
        log_dir = os.path.join(settings.BASE_DIR, 'train', 'train_logs')
        return os.path.join(log_dir, self.title + '.log')

    def get_absolute_url(self): # page to return after save
        #return reverse('train_detail', args=[str(self.id)])
        #return reverse('train_log', args=[self.pk])
        return reverse('train_detail', args=[self.pk])

    

