A web service to predict the brain tumor segmentations of 3D brain MRI images.<br>
Below is a web page example of the prediction result.<br><br>
![Example prediction gif](https://user-images.githubusercontent.com/9957757/75111418-eec45880-567c-11ea-8be8-c769c76aa6e0.gif)
<br>
Assumes that you run the scripts using python3 and that your tensorflow (v1.15) is supported by GPUs. 

Install the necessary packages as follows:<br>
```pip3 install -r requirements.txt```

Then create a seg_model directory, to store your segmentation model files.<br>
```mkdir segmodel```

Put your model architecture saved as a json file into `segmodel/segmodel_architecture.json` and its weights saved as a hd5 file into `segmodel/segmodel_weights.h5`

Then start django webserver (in port 8000 as of now) as follows:<br>
```python manage.py runserver 0:8000```
