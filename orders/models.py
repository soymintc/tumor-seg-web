import os
import time
import nibabel
import numpy as np
import keras
import imageio
import multiprocessing
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

    def plotter(self, args): # plotter worker module for multiprocessing
        zix, t1_segment, pred_sum_segment, png_path = args
        fig, plot = plt.subplots(nrows=1, ncols=1)
        fig.set_size_inches((4, 4))
        result = plot.imshow(t1_segment, cmap='gray', vmin=0, vmax=1)
        result = plot.imshow(pred_sum_segment, cmap='gnuplot', vmin=0, vmax=3, alpha=1)
        fig.savefig(png_path) # tmp

    def save_gif_from_pred(self, t1, pred_sum):
        X, Y, Z = pred_sum.shape

        if settings.DEBUG:
            print('[LOG:{} init savegif] t1 ({}) uniques:'.format(time.ctime(), t1.shape), np.unique(t1)[:10])
        
        # init pool, make args, map pool <- args
        pool = multiprocessing.Pool() # init pool
        zixs = range(0, Z) # z-indices
        t1 = t1 / max(1, np.max(t1))
        t1_segments = [t1[:,:,zix] for zix in zixs] # t1 segments
        pred_sum_segments = [pred_sum[:,:,zix] for zix in zixs] # pred segments
        png_paths = [self.get_pred_path() + '.{}.png'.format(zix) for zix in zixs]

        args_input = zip(zixs, t1_segments, pred_sum_segments, png_paths) # zip args
        pool.map(self.plotter, args_input)
        print('[LOG:{}] pool mapped'.format(time.ctime()))

        gif_path = self.get_pred_path() + '.gif'
        with imageio.get_writer(gif_path, mode='I', duration=0.05) as writer:
            for png_path in png_paths:
                image = imageio.imread(png_path)
                writer.append_data(image)
                if os.path.exists(png_path):
                    os.system('rm {}'.format(png_path))
        print('[LOG:{}] gif made'.format(time.ctime()))

    def get_model(self):
        if hasattr(settings, 'NN_MODEL'):
            print('[LOG:get_model] NN_MODEL already LOADED!')
            return settings.NN_MODEL
        else:
            with settings.TF_SESSION.as_default():
                with settings.TF_SESSION.graph.as_default():
                    K.set_image_data_format('channels_first')
                    with open(settings.MODEL_ARCHITECTURE_PATH, 'r') as f:
                        settings.NN_MODEL = model_from_json(f.read(), custom_objects=custom_objects)
                        if settings.DEBUG:
                            print('[LOG:get_model]', 'Before weights loading')
                    settings.NN_MODEL.load_weights(settings.MODEL_WEIGHTS_PATH)
                    if settings.DEBUG:
                        print('[LOG:get_model]', 'Weights loaded')
            return settings.NN_MODEL

    def predict(self):
        keras.backend.set_session(settings.TF_SESSION)
        dst_shape = (128,128,128)

        with settings.TF_SESSION.as_default():
            with settings.TF_SESSION.graph.as_default():
                flair_src = nibabel.load(self.flair.path).get_data()
                t1_src = nibabel.load(self.t1.path).get_data()
                t1ce_src = nibabel.load(self.t1ce.path).get_data()
                t2_src = nibabel.load(self.t2.path).get_data()
                src_shape = flair_src.shape

                flair = zoom(flair_src, np.divide(dst_shape, src_shape), order=0) # re-size
                t1 = zoom(t1_src, np.divide(dst_shape, src_shape), order=0) # re-size
                t1ce = zoom(t1ce_src, np.divide(dst_shape, src_shape), order=0) # re-size
                t2 = zoom(t2_src, np.divide(dst_shape, src_shape), order=0) # re-size

                model = self.get_model() #settings.NN_MODEL
                K.set_image_data_format('channels_first')
                if settings.DEBUG:
                    print('[LOG:orders/models.py - models LOADED]', K.image_data_format())

                img = np.array([flair, t1, t1ce, t2]) # into (4, is,is,is)
                img = np.expand_dims(img, axis=0) # into (1, 4, is,is,is) - batch size 1

                if settings.DEBUG:
                    print('[LOG:orders/models.py - just before predict]', K.image_data_format())
                pred_batch = model.predict(img)
                if settings.DEBUG:
                    print('[LOG:orders/models.py - right after predict]', K.image_data_format())
        
                # Make summed up segmentation as pred_sum
                pred = pred_batch[0] # only 1 sample per batch
                pred_sum = np.zeros_like(pred[0])
                pred_cutoffs = (0.95, 0.5, 0.2)
                for c in range(3): # c <- channel
                    ixs = (pred[c] >= pred_cutoffs[c])
                    pred_sum[ixs] = c+1 + (c==2) # seg values: 1 2 4
                pred_sum = zoom(pred_sum, np.divide(src_shape, dst_shape), order=0) # re-resize
                pred_sum = np.ma.masked_where(pred_sum == 0, pred_sum) # mask only after resize
                self.save_gif_from_pred(t1_src, pred_sum)

                pred_nii = nibabel.Nifti1Image(pred_sum, np.eye(4))
                pred_path = self.get_pred_path()
                nibabel.save(pred_nii, pred_path)
                if settings.DEBUG:
                    print('[DEBUG] pred_sum saved in {}'.format(pred_path))

                result = ''
                return result

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        self.prediction = self.predict()

    def get_absolute_url(self): # page to return after save
        return reverse('order_detail', args=[str(self.id)])
    
    def __str__(self):
        return self.title

