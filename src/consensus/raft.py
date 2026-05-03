class Raft:
    def __init__(self, node):
        self.node = node

    def elect_leader(self):
        # simplified election
        if self.node.node_id == "node1":
            self.node.state = "leader"
            self.node.leader_id = self.node.node_id
        else:
            self.node.state = "follower"
            self.node.leader_id = "node1"