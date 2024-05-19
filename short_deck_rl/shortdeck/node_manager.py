import dill
import pickle
class Node():
    def __init__(self, actions):
        if actions is None:
            actions = []  # Default to an empty list if actions is None
        # Tracks the cumulative regret for not having chosen each available action in the info set.
        self.regret_sum = [0.0 for _ in range(len(actions))]
        # used to calcualte the avergae strategy, it's the sum of strategies at each info set
        self.strategy_sum = [0.0 for _ in range(len(actions))]
        
    # Ensures all strategy values are positive and normalise them so their sum is 1.   
    # If the total is 0, assign equal probability to all actions.
    def normalise_strategy(self, strategy):
        positive_strats = [max(s, 0) for s in strategy]
        normalising_sum = sum(positive_strats)
        return [s / normalising_sum if normalising_sum > 0 else 1.0/len(strategy) for s in positive_strats]

    # Uses regret matching to get the current strategy for an info set
    # RealisationWeight represents the probability of reaching this information set based on the current strategy
    def get_strategy(self, realisationWeight):
        # Calculate the strategy based on regret matching
        strategy = [max(r, 0) for r in self.regret_sum]
        # normalise the strategy
        normalise_strategy = self.normalise_strategy(strategy)
        
        # Update strategy sum
        for i in range(len(self.strategy_sum)):
            #Update the strategy sum with the weighted strategy
            self.strategy_sum[i] += realisationWeight * normalise_strategy[i]
        
        return normalise_strategy

    # Returns the normalised avg. strategy over all iters.
    def get_average_strategy(self):
        return self.normalise_strategy(self.strategy_sum)
    
    # update cumlative regret for each action
    def update_regret(self, actionIndex, regret):
        self.regret_sum[actionIndex] += regret

    def __str__(self):
        return f"Node({self.get_average_strategy()})" 
    
class NodeManager():
    # Initialises the manager with an empty dictionary for storing nodes 
    def __init__(self):
        self.nodes = {}
    
    # Retrieve the node using its key
    # Ensures that each info set is represented by only one node.
    def getNode(self, key, actions):
        if actions is None:
            actions = []  
        if key not in self.nodes:
            self.nodes[key] = Node(actions)
        return self.nodes[key]
    

