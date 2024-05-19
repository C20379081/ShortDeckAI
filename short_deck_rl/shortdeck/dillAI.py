# 'from .CFR import train' has to be commneted out when running the program due to an import conflict but is required for offline trianing
import dill
import os
import time
from . import node_manager
#from .CFR import train
from. import shared

# Custom unpickler to handle loading of specific classes
class Dill(dill.Unpickler):
    # Override to specify how to find and load the NodeManager and Node classes during unpickling.
    def find_class(self, module, name):
        if name == 'NodeManager':
            return NodeManager
        if name == "Node":
            return Node
        return super().find_class(module, name)

# Function used to save the objects to the file
def save_sets(obj, filename):
    try:
        with open(filename, "wb") as file:
            dill.dump(obj, file)
    except IOError as e:
        print(f"Failed to save object")

# function to set the training details (how long)
def train_time(sets, mins, startItr, limit=4, saveDir="Saves", saveInterval=100):
    # Initialise the training information and start timer.
    info = sets
    start = time.time()
    iterations = startItr
    
    # Train for a specified number of minutes.
    while (time.time() - start)/60 <= mins:
        iterations += 1
        # calls the train function and does a single iteration of CFR training.
        train(info, 1, limit)

        # save the current state
        if iterations % saveInterval == 0:
            save_sets(info, os.path.join(saveDir, "sets" + str(iterations) + ".p"))
    end = time.time()
    
    # print what the training achieved and save the chnages
    save_sets(info, os.path.join(saveDir, "sets" + str(iterations) + ".p"))
    print("total iterations completed:", iterations)
    print((end - start) / (iterations - startItr), "seconds per iteration on AVG")
   
# Used wehn training the AI further, run this file and specify the amounto ftime to training to continue the training
"""
# Path to the previously saved training data file
pickle_file_path = 'training4'
# Load the previously trained NodeManager object
node_manager, start_itr = shared.retrieve_save(pickle_file_path)
# Specify how many additional minutes you want to train
additional_training_minutes = 90 # for example, 60 minutes
# Specify the save directory and interval
save_directory = "training4"
save_interval = 100  # Save after every 100 iterations
# Continue training the loaded NodeManager object
train_time(node_manager, additional_training_minutes, start_itr, limit=4, saveDir=save_directory, saveInterval=save_interval)
print("Training continued successfully.")
"""