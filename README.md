# brain_tumor_segmentation_web_service
Brain tumor segmentation web service to predict the segmentation of 3D brain MRI images.
Assumes that you run the scripts using python3 and that your tensorflow is supported by GPUs. 

Install the necessary packages as follows:
`pip3 install -r requirements.txt`

Then create a seg_model directory, to store your segmentation model files.
`mkdir segmodel`

Put your model architecture saved as a json file into `segmodel/segmodel_architecture.json` and its weights saved as a hd5 file into `segmodel/segmodel_weights.h5`.

Then start django webserver (in port 8000 as of now) as follows:
`python manage.py runserver 0.0.0.0:8000
