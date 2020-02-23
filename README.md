A web service to predict the brain tumor segmentations of 3D brain MRI images.<br>
Below is a web page example of the prediction result.<br>
<img src="https://s5.gifyu.com/images/brain_seg_webd38a9413a306fdc9.gif" width="466" height="380" /><br>
Assumes that you run the scripts using python3 and that your tensorflow (v1.15) is supported by GPUs. 

Install the necessary packages as follows:<br>
```pip3 install -r requirements.txt```

Then create a seg_model directory, to store your segmentation model files.<br>
```mkdir segmodel```

Put your model architecture saved as a json file into `segmodel/segmodel_architecture.json` and its weights saved as a hd5 file into `segmodel/segmodel_weights.h5`

Then start django webserver (in port 8000 as of now) as follows:<br>
```python manage.py runserver 0:8000```
