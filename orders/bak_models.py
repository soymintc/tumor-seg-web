import os
import nibabel
import numpy as np
import keras
import imageio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from keras.models import model_from_json
from scipy.ndimage import zoom
from keras import backend as K
from .utils import custom_objects


class Order(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    flair = models.FileField(upload_to='data/%Y%m%d%H%M/', blank=True) # nonexistable
    t1 = models.FileField(upload_to='data/%Y%m%d%H%M/', blank=True) # nonexistable
    t1ce = models.FileField(upload_to='data/%Y%m%d%H%M/', blank=True) # nonexistable
    t2 = models.FileField(upload_to='data/%Y%m%d%H%M/', blank=True) # nonexistable
    if settings.DEBUG:
        print('[DEBUG:Order]\n {}\n {}\n {}\n {}'.format(
            dir(flair), t1.upload_to, t1ce, t2))

    @property
    def flag_show_only(self):
        return (os.path.exists(self.get_pred_path())
            and os.path.exists(self.get_gif_path())) 

    def get_pred_path(self):
        flair_fname = os.path.split(self.flair.path)[-1] # MEDIA_ROOT/data/2019..../filename
        upload_dir = os.path.dirname(self.flair.path) # MEDIA_ROOT/data/2019..../
        assert os.path.isdir(upload_dir), "[ERROR] {} is not a directory".format(upload_dir)
        assert '_flair.nii.gz' in flair_fname, "[ERROR] _flair.nii.gz not in {}".format(flair_fname)
        sid = flair_fname.split('_flair.nii.gz')[0]
        fname = '{}_pred.nii.gz'.format(sid)
        pred_path = os.path.join(upload_dir, fname)
        return pred_path

    def get_gif_path(self):
        pred_path = self.get_pred_path()
        return pred_path + '.gif'

    def get_gif_url(self):
        pred_path = self.get_pred_path()
        pred_dir = os.path.dirname(pred_path)
        assert pred_path.startswith(settings.MEDIA_ROOT), '[ERROR] {} does not start with {}'.format(pred_path, settings.MEDIA_ROOT)
        pred_url = pred_dir.replace(settings.MEDIA_ROOT, settings.MEDIA_URL) 
        pred_fname = os.path.split(pred_path)[-1]
        gif_url = pred_url + '/' + pred_fname+'.gif'
        return gif_url

    def save_gif_from_pred(self, t1, pred, pred_cutoffs=(0.95, 0.5, 0.2)):
        pred_sum = np.zeros_like(pred[0])
        for c in range(3): # c <- channel
            ixs = (pred[c] >= pred_cutoffs[c])
            pred_sum[ixs] = c+1
        pred_sum = np.ma.masked_where(pred_sum == 0, pred_sum)
        X, Y, Z = pred_sum.shape
        zixs = range(0, Z)
        gif_path = self.get_pred_path() + '.gif'
        png_path = self.get_pred_path() + '.png'
        t1_vmax = np.max(t1)
        
        with imageio.get_writer(gif_path, mode='I', duration=0.05) as writer:
            for zix in zixs:
                fig, plot = plt.subplots(nrows=1, ncols=1)
                fig.set_size_inches((4, 4))
                result = plot.imshow(t1[:,:,zix], cmap='gray', vmin=0, vmax=t1_vmax)
                result = plot.imshow(pred_sum[:,:,zix], cmap='gnuplot', vmin=0, vmax=3, alpha=1)
                fig.savefig(png_path) # tmp
                image = imageio.imread(png_path)
                writer.append_data(image)
        if os.path.exists(png_path):
            os.system('rm {}'.format(png_path))

    def __str__(self):
        return self.title

    def get_model(self):
        if hasattr(settings, 'NN_MODEL'):
            return settings.NN_MODEL
        else:
            with settings.TF_SESSION.as_default():
                with settings.TF_SESSION.graph.as_default():
                    K.set_image_data_format('channels_first')
                    if settings.DEBUG:
                        print('[LOG:modelfn]', K.image_data_format())
                    with open(settings.MODEL_ARCHITECTURE_PATH, 'r') as f:
                        settings.NN_MODEL = model_from_json(f.read(), custom_objects=custom_objects)
                        if settings.DEBUG:
                            print('[LOG:modelfn]', 'Before weights loading')
                    settings.NN_MODEL.load_weights(settings.MODEL_WEIGHTS_PATH)
                    if settings.DEBUG:
                        print('[LOG:modelfn]', 'Weights loaded')
            return settings.NN_MODEL

    def predict(self):
        keras.backend.set_session(settings.TF_SESSION)
        image_shape = (128,128,128)

        with settings.TF_SESSION.as_default():
            with settings.TF_SESSION.graph.as_default():
                if settings.DEBUG:
                    print('[LOG:orders/models.py 1]', K.image_data_format())
                    print('[LOG:orders/models.py paths=\n{}\n{}\n{}\n{}\n{}'.format(
                        self.flair.path, self.t1.path, self.t1ce.path, self.t2.path, dir(self.flair) ))
                flair = nibabel.load(self.flair.path).get_data()
                t1 = nibabel.load(self.t1.path).get_data()
                t1ce = nibabel.load(self.t1ce.path).get_data()
                t2 = nibabel.load(self.t2.path).get_data()

                flair = zoom(flair, np.divide(image_shape, flair.shape), order=0) # re-size
                t1 = zoom(t1, np.divide(image_shape, t1.shape), order=0) # re-size
                t1ce = zoom(t1ce, np.divide(image_shape, t1ce.shape), order=0) # re-size
                t2 = zoom(t2, np.divide(image_shape, t2.shape), order=0) # re-size

                model = self.get_model() #settings.NN_MODEL
                K.set_image_data_format('channels_first')
                if settings.DEBUG:
                    print('[LOG:orders/models.py 2]', K.image_data_format())

                img = np.array([flair, t1, t1ce, t2]) # into (4, is,is,is)
                img = np.expand_dims(img, axis=0) # into (1, 4, is,is,is)

                pred_batch = model.predict(img)

                pred = pred_batch[0]
                self.save_gif_from_pred(t1, pred)

                pred = nibabel.Nifti1Image(pred, np.eye(4))
                pred_path = self.get_pred_path()
                nibabel.save(pred, pred_path)
                if settings.DEBUG:
                    print('[DEBUG] pred saved in {}'.format(pred_path))

                result = ''
                return result

    def save(self, *args, **kwargs):
        if settings.DEBUG:
            print('args and kwargs', args,'\n',kwargs)
        super(Order, self).save(*args, **kwargs)
        self.prediction = self.predict()

    def get_absolute_url(self): # page to return after save
        return reverse('order_detail', args=[str(self.id)])
