"""
Copyright (C) Microsoft Corporation. All rights reserved.​
 ​
Microsoft Corporation (“Microsoft”) grants you a nonexclusive, perpetual,
royalty-free right to use, copy, and modify the software code provided by us
("Software Code"). You may not sublicense the Software Code or any use of it
(except to your affiliates and to vendors to perform work on your behalf)
through distribution, network access, service agreement, lease, rental, or
otherwise. This license does not purport to express any claim of ownership over
data you may have shared with Microsoft in the creation of the Software Code.
Unless applicable law gives you more rights, Microsoft reserves all other
rights not expressly granted herein, whether by implication, estoppel or
otherwise. ​
 ​
THE SOFTWARE CODE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
MICROSOFT OR ITS LICENSORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THE SOFTWARE CODE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
import pickle
from azureml.core import Workspace
from azureml.core.run import Run
import os
from sklearn.datasets import load_diabetes
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib
import numpy as np
import json
import subprocess
from typing import Tuple, List
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor

# run_history_name = 'devops-ai'
# os.makedirs('./outputs', exist_ok=True)
# #ws.get_details()
# Start recording results to AML
# run = Run.start_logging(workspace = ws, history_name = run_history_name)
run = Run.get_submitted_run()


X, y = load_diabetes(return_X_y=True)
columns = ["age", "gender", "bmi", "bp", "s1", "s2", "s3", "s4", "s5", "s6"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
data = {"train": {"X": X_train, "y": y_train}, "test": {"X": X_test, "y": y_test}}

print("Running train.py")


def GridSearch(reg,parameters,train_X,train_y,test_X,test_y):
    model = GridSearchCV(reg, parameters)
    model.fit(train_X,train_y)
    mse = mean_squared_error(model.predict(test_X),test_y)
    return model, mse

#Ridge Regression 
reg_ridge = Ridge()
parameters_ridge = {'alpha':np.arange(0.01, 1.0, 0.05)}
model_ridge,mse_ridge = GridSearch(reg_ridge, parameters_ridge, data["train"]["X"], data["train"]["y"],data["test"]["X"], data["test"]["y"])

#Support Vector Regression
reg_svr = SVR()
parameters_svr = {'kernel':['linear','poly','rbf']}
model_SVR,mse_SVR = GridSearch(reg_svr, parameters_svr,data["train"]["X"], data["train"]["y"],data["test"]["X"], data["test"]["y"])

 
#Random Forest Regression
reg_rfr = RandomForestRegressor()
parameters_rfr = {'max_depth': [10, 20, 30, 50],
 'min_samples_leaf': [1, 2, 4],
 'min_samples_split': [2, 5, 10]}
model_rfr,mse_rfr = GridSearch(reg_rfr, parameters_rfr,data["train"]["X"], data["train"]["y"],data["test"]["X"], data["test"]["y"])

#Check which model is better and save the best model
models = [model_ridge,model_SVR,model_rfr]
mse = [mse_ridge,mse_SVR,mse_rfr]
best_mse = min(mse)
best_model = models[np.argmin(mse)]

run.log("mse", best_mse)

# Save model as part of the run history
model_name = "sklearn_regression_model.pkl"
# model_name = "."

with open(model_name, "wb") as file:
    joblib.dump(value=best_model, filename=model_name)

# upload the model file explicitly into artifacts
run.upload_file(name="./outputs/" + model_name, path_or_stream=model_name)
print("Uploaded the model {} to experiment {}".format(model_name, run.experiment.name))
dirpath = os.getcwd()
print(dirpath)


# register the model
# run.log_model(file_name = model_name)
# print('Registered the model {} to run history {}'.format(model_name, run.history.name))


print("Following files are uploaded ")
print(run.get_file_names())
run.complete()
