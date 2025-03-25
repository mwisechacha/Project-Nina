#### NINA: BREAST CANCER DETECTION SYSTEM


##### Under the Hood
This system leverages CNNs and Machine Learning algorithms for binary classification of the tumor and decision making
The RESNET18 model is trained on the CBIS-DDSM dataset and the Random Forest Classifier trained in the features of the tumor

##### How it works
A uer/radiologist uploads a mammogram, enters the features of the tumor and breast: the breast density, the mass margin, and the mass shape. They receive the prediction results(Pathology) for the ResNet18 model and the BI-RADS classification results from the Random Forest Classifier. This helps the radiologist in decision making. The can either approve the model results of disapprove.

##### Preview
