import os
import time
import psutil
import signal
from subprocess import Popen, PIPE
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import CreateView
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

from .models import Train

from django.http import HttpResponse, Http404



@method_decorator(staff_member_required, name='dispatch')
class TrainCreateView(LoginRequiredMixin, CreateView):
    model = Train
    template_name = 'train_new.html'
    fields = ('title', 'batch_size', 'image_size', 'n_validation', 'n_test',
        'learning_rate', 'optimizer', 'group_size', 'filters_root', 'augment',)

    def form_valid(self, form):
        form.instance.author = self.request.user # requires user field
        return super().form_valid(form) # now anonymous --> error


@staff_member_required
def train_kill_view(request, pk):
    train = get_object_or_404(Train, pk=pk)
    if train.pid_exists():
        os.kill(train.pid, signal.SIGTERM)
        context = {'submitted_kill': True}
        print('[LOG]', train.pid_exists(), context)
    else:
        context = {'submitted_kill': Fale}
        print('[LOG]', train.pid_exists(), context)
    context['train'] = train
    return render(request, 'train_kill.html', context)


@staff_member_required
def train_log_view(request, pk):
    train = get_object_or_404(Train, pk=pk)
    log_path = train.get_log_path()
    log = open(log_path, 'r').read()
    context = {'train':train, 'log':log}
    return render(request, 'train_log.html', context)


@staff_member_required
def train_detail_view(request, pk):
    train = get_object_or_404(Train, pk=pk)
    #train = Train.objects.get(pk=pk)
    script = os.path.join(settings.BASE_DIR, 'train', 'scripts', 'run_vnet3d_with_ag.py')
    assert os.path.exists(script), "[ERROR] {} does not exist".format(script)

    # Set log path
    log_dir = os.path.join(settings.BASE_DIR, 'train', 'train_logs')
    if not os.path.exists(log_dir):
        os.system('mkdir -p {}'.format(log_dir))
    log_path = train.get_log_path()

    # Set command
    cmd_args = ['python3', script,
        '--core_tag', train.title, # log, models made by title
        '--nii_dir', settings.NII_DIR, 

        '--batch_size', train.batch_size,
        '--image_size', train.image_size,
        '--n_validation', train.n_validation,
        '--n_test', train.n_test,

        '--learning_rate', train.learning_rate,

        '--optimizer', train.optimizer,
        '--group_size', train.group_size,
        '--f_root', train.filters_root,]
        
        #'> {} 2>&1'.format(log_path),]
    if train.augment:
        #cmd_args += ['--augment'] ##@##
        pass
    cmd_args = [str(_) for _ in cmd_args]

    if train.run_phase():
        with open(log_path,"wb") as out, open(log_path,"wb") as err:
            child = Popen(cmd_args, stdout=out, stderr=err) # open and run child process

        train.pid = child.pid
        train.cmd_str = '\n'.join([cmd_args[i] + ' ' + cmd_args[i+1]
            for i in range(0, len(cmd_args), 2)])
        train.save()
    else:
        pass

    context = {'train':train}
    return render(request, 'train_detail.html', context)



